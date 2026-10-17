#!/usr/bin/env bash
#
# build.sh - build the local OSRM routing data (Maryland extract, car profile, MLD algorithm).
#
#   infra/osrm/build.sh          # run from any directory
#
# Steps
#   1. Download the Geofabrik Maryland extract into data/osrm/, unless the local copy already
#      matches the md5 that Geofabrik publishes next to it (maryland-latest.osm.pbf.md5). The md5
#      is always verified; one mismatch triggers one re-download, a second mismatch stops the build.
#   2. osrm-extract, osrm-partition and osrm-customize, each in the pinned osrm-backend image
#      (native linux/arm64) -> data/osrm/maryland-latest.osrm.*
#   3. Write data/osrm/PROVENANCE.json (source, md5, size, image tag + digest, timestamps).
#      The file is removed before step 2 and rewritten only when the build finishes, so its
#      presence means "the .osrm files were built from exactly this extract".
#
# All output (script messages and docker output) is appended to data/osrm/build.log.
# This script does NOT start osrm-routed (the routing server is a separate step).
# Needs: bash (3.2 is fine), curl, a running Docker, md5 (macOS) or md5sum.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OSRM_DIR="$ROOT/data/osrm"
LOG="$OSRM_DIR/build.log"

PBF_NAME="maryland-latest.osm.pbf"
OSRM_NAME="maryland-latest.osrm"
PBF_URL="https://download.geofabrik.de/north-america/us/maryland-latest.osm.pbf"
MD5_URL="$PBF_URL.md5"
PBF="$OSRM_DIR/$PBF_NAME"
MD5_FILE="$PBF.md5"
PROV="$OSRM_DIR/PROVENANCE.json"

IMAGE="ghcr.io/project-osrm/osrm-backend:v6.0.0"
PLATFORM="linux/arm64"

# Filled in by main().
EXPECTED_MD5=""
PBF_MD5=""
PBF_SIZE=""
HTTP_LAST_MODIFIED=""
DOWNLOADED_UTC=""
BUILT_UTC=""
IMAGE_DIGEST=""
DURATIONS=""

# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
utc_now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log()     { printf '[%s] %s\n' "$(utc_now)" "$*"; }
die()     { log "ERROR: $*"; exit 1; }

trap 'log "ERROR: command failed (exit $?) at line $LINENO: $BASH_COMMAND"' ERR

md5_of() {
  if command -v md5 >/dev/null 2>&1; then md5 -q "$1"; else md5sum "$1" | awk '{print $1}'; fi
}

file_size() { wc -c < "$1" | tr -d '[:space:]'; }

# File modification time as UTC ISO-8601. The pbf is written once by fetch() and never touched
# again, so this is the moment the download finished (and stays the same on later runs).
mtime_utc() {
  if TZ=UTC /usr/bin/stat -f '%Sm' -t '%Y-%m-%dT%H:%M:%SZ' "$1" 2>/dev/null; then return 0; fi
  date -u -d "@$(stat -c %Y "$1")" '+%Y-%m-%dT%H:%M:%SZ'
}

json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

# fetch URL DEST: curl to DEST.part, rename on success; on failure log it and exit with curl's code.
fetch() {
  local url="$1" dest="$2" rc=0
  rm -f "$dest.part"
  curl -fL --retry 2 -sS -o "$dest.part" "$url" || rc=$?
  if [ "$rc" -ne 0 ]; then
    rm -f "$dest.part"
    log "ERROR: download failed after retries (curl exit $rc): $url"
    exit "$rc"
  fi
  mv -f "$dest.part" "$dest"
}

# Fetch the published md5 and put it (lower-case, 32 hex chars) into EXPECTED_MD5.
fetch_expected_md5() {
  fetch "$MD5_URL" "$MD5_FILE"
  EXPECTED_MD5="$(awk 'NR==1 {print tolower($1)}' "$MD5_FILE")"
  if ! printf '%s' "$EXPECTED_MD5" | grep -Eq '^[0-9a-f]{32}$'; then
    die "unexpected content in $MD5_FILE (from $MD5_URL): $(head -c 200 "$MD5_FILE")"
  fi
  log "published md5: $EXPECTED_MD5  ($MD5_URL)"
}

# Steps a + b: make sure $PBF exists and matches the published md5 (sets PBF_MD5).
ensure_pbf() {
  local attempt=1 t0

  fetch_expected_md5

  if [ -f "$PBF" ]; then
    PBF_MD5="$(md5_of "$PBF")"
    if [ "$PBF_MD5" = "$EXPECTED_MD5" ]; then
      log "SKIP download: $PBF_NAME is already present and its md5 matches the published md5"
      return 0
    fi
    log "local $PBF_NAME has md5 $PBF_MD5, published md5 is $EXPECTED_MD5 -> downloading again"
  else
    log "no local $PBF_NAME -> downloading"
  fi

  while :; do
    log "START download (attempt $attempt of 2): $PBF_URL"
    t0=$SECONDS
    fetch "$PBF_URL" "$PBF"
    PBF_MD5="$(md5_of "$PBF")"
    log "DONE  download: $(file_size "$PBF") bytes in $((SECONDS - t0))s, md5 $PBF_MD5"
    if [ "$PBF_MD5" = "$EXPECTED_MD5" ]; then
      return 0
    fi
    log "ERROR: md5 mismatch (attempt $attempt of 2): published $EXPECTED_MD5, downloaded $PBF_MD5"
    rm -f "$PBF"
    if [ "$attempt" -ge 2 ]; then die "md5 mismatch on two consecutive downloads; stopping"; fi
    attempt=$((attempt + 1))
    fetch_expected_md5   # Geofabrik refreshes the *-latest files daily: re-read the published md5
  done
}

# Last-Modified header of the remote .pbf (curl -sI), e.g. "Thu, 01 Oct 2026 20:21:32 GMT".
get_last_modified() {
  HTTP_LAST_MODIFIED="$(curl -sIL --retry 2 "$PBF_URL" | tr -d '\r' | grep -i '^last-modified:' \
    | tail -n 1 | sed 's/^[^:]*:[[:space:]]*//' || true)"
  [ -n "$HTTP_LAST_MODIFIED" ] || die "no Last-Modified header in the response headers of $PBF_URL"
}

# Make sure the pinned image is present for $PLATFORM; sets IMAGE_DIGEST.
ensure_image() {
  local have
  have="$(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$IMAGE" 2>/dev/null || true)"
  if [ "$have" != "$PLATFORM" ]; then
    log "image $IMAGE for $PLATFORM not present locally (found: ${have:-none}) -> docker pull"
    docker pull --platform "$PLATFORM" "$IMAGE"
  fi
  IMAGE_DIGEST="$(docker image inspect --format '{{index .RepoDigests 0}}' "$IMAGE")"
  log "image: $IMAGE  digest: $IMAGE_DIGEST  platform: $(docker image inspect --format '{{.Os}}/{{.Architecture}}' "$IMAGE")"
}

# run_osrm <osrm-binary> [args...]: run one OSRM tool in the pinned image with data/osrm as /data.
run_osrm() {
  local step="$1" t0="$SECONDS" rc=0 dt
  log "START $step: docker run --rm --platform $PLATFORM -t -v $OSRM_DIR:/data $IMAGE $*"
  docker run --rm --platform "$PLATFORM" -t -v "$OSRM_DIR:/data" "$IMAGE" "$@" || rc=$?
  dt=$((SECONDS - t0))
  if [ "$rc" -ne 0 ]; then
    log "FAIL  $step: exit code $rc after ${dt}s"
    if [ "$rc" -eq 137 ]; then log "      (137 = process killed, most likely out of memory)"; fi
    exit "$rc"
  fi
  log "DONE  $step in ${dt}s"
  DURATIONS="$DURATIONS $step=${dt}s"
}

write_provenance() {
  cat > "$PROV" <<EOF
{
  "source_url": "$(json_escape "$PBF_URL")",
  "md5": "$PBF_MD5",
  "size_bytes": $PBF_SIZE,
  "http_last_modified": "$(json_escape "$HTTP_LAST_MODIFIED")",
  "downloaded_utc": "$DOWNLOADED_UTC",
  "image_tag": "$(json_escape "$IMAGE")",
  "image_digest": "$(json_escape "$IMAGE_DIGEST")",
  "profile": "car.lua",
  "algorithm": "mld",
  "built_utc": "$BUILT_UTC"
}
EOF
  if grep -Eq '": ""' "$PROV"; then die "PROVENANCE.json has an empty field"; fi
}

# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
main() {
  local ext
  SECONDS=0
  log "===== build.sh start ====="
  log "root: $ROOT"
  log "data dir: $OSRM_DIR"

  command -v curl   >/dev/null 2>&1 || die "curl not found in PATH"
  command -v docker >/dev/null 2>&1 || die "docker not found in PATH"
  docker info >/dev/null 2>&1       || die "cannot reach the Docker daemon (is Docker Desktop running?)"

  # a + b. download (or skip) the extract and verify its md5
  ensure_pbf
  log "md5 verified: $PBF_MD5 (matches the published md5)"
  PBF_SIZE="$(file_size "$PBF")"
  DOWNLOADED_UTC="$(mtime_utc "$PBF")"
  get_last_modified
  log "extract: $PBF_NAME  size_bytes=$PBF_SIZE  http_last_modified='$HTTP_LAST_MODIFIED'  downloaded_utc=$DOWNLOADED_UTC"

  # c. extract / partition / customize (MLD)
  ensure_image
  rm -f "$PROV"   # stale provenance must not outlive a half-finished rebuild
  run_osrm osrm-extract   -p /opt/car.lua "/data/$PBF_NAME"
  run_osrm osrm-partition "/data/$OSRM_NAME"
  run_osrm osrm-customize "/data/$OSRM_NAME"
  BUILT_UTC="$(utc_now)"

  for ext in partition cells mldgr; do
    [ -s "$OSRM_DIR/$OSRM_NAME.$ext" ] || die "expected build output missing or empty: $OSRM_NAME.$ext"
  done

  # d. provenance
  write_provenance
  log "wrote $PROV"

  log "files in $OSRM_DIR:"
  ls -l "$OSRM_DIR"
  log "total size of $OSRM_DIR: $(du -sh "$OSRM_DIR" | awk '{print $1}')"
  log "SUMMARY:$DURATIONS"
  log "===== build.sh done in ${SECONDS}s ====="
}

# e. tee everything to the log. The pipeline (not process substitution) makes the script wait for
#    tee to flush, and with pipefail the exit code is main's exit code.
mkdir -p "$OSRM_DIR"
main 2>&1 | tee -a "$LOG"
