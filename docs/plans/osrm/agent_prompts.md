# Local OSRM: agent prompts (run one at a time, in order)

Each prompt is self-contained: paste it into a fresh agent. Start the next one only after the previous agent's acceptance checks are confirmed.
- The plan is in `plan.md`.
- Results are recorded in `log.md` by the main session.
- The repo root is `/Users/vigneshrbabu/Documents/Git/bluejay-night-ride-optimizer`, called ROOT below.

---

## A1: download the map data and build the routing files (Sonnet)

```
You are setting up a local OSRM routing server for a course project. Repo root: /Users/vigneshrbabu/Documents/Git/bluejay-night-ride-optimizer (ROOT).

FACTS (already checked; do not re-investigate):
- macOS on Apple Silicon (arm64). Docker Desktop is installed and running (Linux VM aarch64, 8.2 GB memory).
- Use image ghcr.io/project-osrm/osrm-backend:v6.0.0 (it has a native linux/arm64 build). Always pass --platform linux/arm64.

WRITE ONLY these files: ROOT/infra/osrm/build.sh and everything under ROOT/data/osrm/. Do not edit any other file. Do not commit or push. Do not start the routing server; a later step does that.

STEPS
1. mkdir -p ROOT/data/osrm ROOT/infra/osrm
2. Write ROOT/infra/osrm/build.sh (bash, set -euo pipefail, run from any directory). It locates ROOT from its own path and then:
   a. downloads https://download.geofabrik.de/north-america/us/maryland-latest.osm.pbf to data/osrm/ with curl -fL --retry 2. It skips the download if the file exists and its md5 matches maryland-latest.osm.pbf.md5 from the same URL folder; it also fetches the .md5 file;
   b. verifies the md5 (macOS: md5 -q);
   c. runs, with -v "$ROOT/data/osrm:/data":
      osrm-extract -p /opt/car.lua /data/maryland-latest.osm.pbf
      osrm-partition /data/maryland-latest.osrm
      osrm-customize /data/maryland-latest.osrm
      each as docker run --rm --platform linux/arm64 -t ... ghcr.io/project-osrm/osrm-backend:v6.0.0;
   d. writes data/osrm/PROVENANCE.json with: source_url, md5, size_bytes, the http_last_modified header of the .pbf (curl -sI), downloaded_utc, the image tag and image digest (docker image inspect --format '{{index .RepoDigests 0}}'), profile "car.lua", algorithm "mld", built_utc;
   e. tees all output to data/osrm/build.log.
3. Run build.sh. Steps may take several minutes; use long timeouts (up to 10 min per command), or run it in the background and poll.
4. Run build.sh a second time. It must skip the download (md5 match) and finish with exit code 0.

ACCEPTANCE (report each with evidence):
- data/osrm/ contains maryland-latest.osrm.* files, including .partition, .cells and .mldgr;
- the md5 matches;
- PROVENANCE.json has every field filled;
- the second run exits 0 and logs that it skipped the download;
- report: pbf size, extract/partition/customize durations, total size of data/osrm, and any warnings from build.log.

STOP AND REPORT (do not improvise) if: the download fails after retries; the md5 mismatches twice; any osrm command exits non-zero (exit 137 = out of memory). Report the exact error lines. Do not try clipping, other images or other settings.
```

---

## A2: serve on port 5050 and validate against the demo-server matrix (Sonnet)

```
You are starting and validating a local OSRM server. Repo root: /Users/vigneshrbabu/Documents/Git/bluejay-night-ride-optimizer (ROOT). The previous step built ROOT/data/osrm/maryland-latest.osrm.* (MLD), with image ghcr.io/project-osrm/osrm-backend:v6.0.0 (linux/arm64). See ROOT/data/osrm/PROVENANCE.json.

FACTS: host port 5000 is taken by macOS AirPlay, so use host port 5050 -> container 5000. Docker is running.

WRITE ONLY: ROOT/infra/osrm/docker-compose.yml, ROOT/infra/osrm/validate_local.py, ROOT/data/osrm/validation_report.md, ROOT/data/osrm/validation_pairs.csv. Do not edit other files. Do not commit.

STEPS
1. docker-compose.yml: one service "osrm" with:
   - image pinned to v6.0.0 and platform linux/arm64;
   - command: osrm-routed --algorithm mld --max-table-size 500 /data/maryland-latest.osrm;
   - ports "5050:5000";
   - volume ../../data/osrm:/data:ro;
   - restart: unless-stopped;
   - container_name: bluejay-osrm.
2. docker compose -f ROOT/infra/osrm/docker-compose.yml up -d, then poll until this returns "code":"Ok" (max 2 min):
   curl -s "http://localhost:5050/route/v1/driving/-76.6205,39.3299;-76.6155,39.2904?overview=false"
3. validate_local.py (uses ROOT/.venv/bin/python; pandas and numpy are available). It:
   - reads ROOT/data/processed/locations_v1.csv (loc_id, lat, lon; 188 rows);
   - sends ONE table request for all 188 points to http://localhost:5050/table/v1/driving/{lon,lat;...}?annotations=duration,distance;
   - compares with ROOT/data/processed/tt_locations_v1.csv (columns origin, dest, seconds, meters; OSRM demo server, retrieved 2026-10-01) on all 35,344 ordered pairs, excluding the diagonal from the ratio stats;
   - reports: n pairs; nulls; median and P95 of |local - demo| seconds; median and P95 relative difference; Pearson r and Spearman rho of seconds; the same for meters; the max snapping distance (the "distance" field of each source/destination waypoint in the table response) and the loc_id with the largest snap; the 10 pairs with the largest relative difference;
   - writes validation_pairs.csv (origin, dest, demo_s, local_s, demo_m, local_m) and validation_report.md (numbers plus a 3-line interpretation). The interpretation should note that differences mainly reflect different OSM data dates.

ACCEPTANCE: table code Ok; 188x188 with no nulls; Pearson r (seconds) >= 0.95; median relative difference <= 10%; max snap <= 75 m. Leave the container running at the end and report `docker compose ps`.

STOP AND REPORT if any acceptance check fails: give the numbers and the 10 worst pairs. Do not change OSRM settings or data to make it pass. Also stop if the container exits; report `docker compose logs --tail 50`.
```

---

## A3: integrate with the project code (Sonnet)

```
You are wiring a local OSRM server into a Python project. Repo root: /Users/vigneshrbabu/Documents/Git/bluejay-night-ride-optimizer (ROOT). A local OSRM is running at http://localhost:5050 (MLD, max-table-size 500); provenance is in ROOT/data/osrm/PROVENANCE.json. Python: ROOT/.venv/bin/python.

READ FIRST: ROOT/src/scenario/travel_times.py (the current OSRM client: demo server, chunked table calls, cache in ROOT/data/raw/osrm_cache keyed by a stable sha1 of the coordinates) and ROOT/docs/plans/osrm/plan.md.

WRITE ONLY: ROOT/src/scenario/travel_times.py (edit), ROOT/src/scenario/travel_times_v2.py (new), ROOT/data/processed/tt_locations_v2.csv, ROOT/data/processed/routes_M_v2.geojson, ROOT/data/processed/locations_snap_v2.csv, and new cache files under ROOT/data/raw/osrm_cache/local_v6.0.0/. Do NOT edit tests/, demand.py, generator.py, locations.py, figures.py, build_*.py, validate.py, or any *_v1 file. Do not commit.

CHANGES TO travel_times.py (keep its existing public functions working):
1. Server choice via the environment variable OSRM_URL; default "https://router.project-osrm.org" (the current behaviour, so existing scripts are unchanged). Export a helper set_server(url).
2. Separate caches per server, so local and demo results can never mix: the demo server keeps the existing cache folder ROOT/data/raw/osrm_cache (do not rename or move existing files); any other server uses ROOT/data/raw/osrm_cache/<slug>/. The slug for http://localhost:5050 is "local_v6.0.0"; derive it from the image tag in PROVENANCE.json.
3. Chunk size: 50 for the demo server, 200 for local.
4. No silent fallback: if the chosen server is unreachable, raise RuntimeError with the message "OSRM server <url> not reachable; see docs/technical/osrm_local.md". Never retry against a different server.
5. New function route(lat_lon_list) -> dict(duration_s, distance_m, coords=[[lon,lat],...]). It uses /route/v1/driving/...?overview=full&geometries=geojson and is cached the same way.

NEW travel_times_v2.py (run as a script from ROOT/src/scenario):
- sets the server to http://localhost:5050;
- builds the full matrix over ROOT/data/processed/locations_v1.csv (all ordered pairs, 188x188) with the same columns as tt_locations_v1.csv: origin, dest, seconds, meters, source, retrieval_date;
  - set the diagonal to 0;
  - source = "OSRM local v6.0.0, Geofabrik maryland-latest (Last-Modified <date from PROVENANCE>), car, free-flow";
  - sort by origin, dest; write ROOT/data/processed/tt_locations_v2.csv;
- builds route geometries for the 30 requests in ROOT/data/scenarios/ladder/M/requests.csv (o_lat,o_lon -> d_lat,d_lon). Writes ROOT/data/processed/routes_M_v2.geojson as a FeatureCollection of LineStrings with properties request_id, duration_s, distance_m;
- writes ROOT/data/processed/locations_snap_v2.csv with one row per location: loc_id, snap_m, snapped_lat, snapped_lon, road_name. It uses the local /nearest/v1/driving service (number=1). These are the points where a van actually stops; a validation step found one location over 75 m (p04_b037, 94.9 m to Poole St), a documented exception;
- prints the HTTP request count (count actual network calls, not cache hits).

ACCEPTANCE (report each with evidence):
- tt_locations_v2.csv: 35,344 rows, diagonal 0, all finite and >= 0;
- a second run of travel_times_v2.py makes 0 network calls;
- routes_M_v2.geojson: 30 features; each first/last coordinate within 75 m of its request's pickup/drop-off, except where that endpoint's snap_m exceeds 75 m (only p04_b037 is expected); compare to the snapped point instead;
- locations_snap_v2.csv: 188 rows; the max snap_m is about 94.9 m at p04_b037; report the count over 75 m and the median;
- `ROOT/.venv/bin/python -m pytest ROOT/tests -q` still shows 32 passed;
- `cd ROOT/src/scenario && OSRM_URL=http://localhost:5999 ../../.venv/bin/python -c "import travel_times as t; t.table([(39.33,-76.62)],[(39.32,-76.62)])"` raises the RuntimeError message above. Port 5999 is unused; it proves there is no silent fallback.

STOP AND REPORT if pytest fails, or if any acceptance check fails; give the exact output. Do not modify tests to pass.
```

---

> **Changed after A4 (main session, 2 Oct):** the local cache slug now includes the first 8 hex of the map-data md5 (`local_v6.0.0_ff90439c`), so a new extract never reuses old answers. The existing cache folder was renamed, and outputs were verified byte-identical with 0 network calls.

## A4: write the how-to (Sonnet; changed from Haiku because the server must be left running)

```
Write ROOT/docs/technical/osrm_local.md, a how-to for teammates on the project's local OSRM server. Repo root: /Users/vigneshrbabu/Documents/Git/bluejay-night-ride-optimizer (ROOT).

READ: ROOT/docs/plans/osrm/plan.md, ROOT/docs/plans/osrm/log.md, ROOT/infra/osrm/build.sh, ROOT/infra/osrm/docker-compose.yml (bound to 127.0.0.1:5050), ROOT/infra/osrm/validate_local.py, ROOT/data/osrm/PROVENANCE.json, ROOT/data/osrm/validation_report.md, ROOT/src/scenario/travel_times.py (set_server, table, matrix, route, nearest, HTTP_CALLS), ROOT/src/scenario/travel_times_v2.py.

WRITE ONLY ROOT/docs/technical/osrm_local.md. Do not commit.

SECTIONS
1. What it is and why we use it (3-4 lines; free-flow car times, not traffic).
2. Prerequisites: Docker Desktop on Apple Silicon (image linux/arm64); macOS uses port 5000 for AirPlay, so we use 5050.
3. One-time build: `infra/osrm/build.sh`, what it downloads, how long it took, and the disk use (take the numbers from PROVENANCE.json / build.log).
4. Start, stop, status and logs (docker compose -f infra/osrm/docker-compose.yml up -d / down / ps / logs).
5. Health check and two example queries (route and table) with curl, plus what "code": "Ok" means.
6. How the project uses it: the OSRM_URL variable, per-server caches, the no-silent-fallback rule, route() and nearest(), travel_times_v2.py and its outputs (tt_locations_v2.csv, routes_M_v2.geojson, locations_snap_v2.csv); locations.py refuses to run when OSRM_URL points to a non-demo server; the v1 files are untouched (the demo server, retrieved 1 Oct; the v0 tables 29 Sep).
7. Validation results: the key numbers from validation_report.md, plus the one documented snapping exception (p04_b037, 94.9 m; see log.md) and why local times run about 1% slower (the v6 car profile's 2 s per signal or stop sign).
8. Updating the map data: how build.sh handles a newer Geofabrik extract (read the script and describe exactly when it re-downloads). The new data date goes into PROVENANCE.json; restart the server after a rebuild. Rebuild any v2 outputs, and note that matrices built from different data dates must not be mixed in one experiment.
9. Troubleshooting: port in use; exit 137 (memory: Docker Desktop > Settings > Resources); "TooBig" (--max-table-size); image platform errors; the container not running.
10. License: OSM data is ODbL ("© OpenStreetMap contributors" on any figure with routes or maps).

RULES:
- Run every query and status command you put in the doc once against the running server, and check that it works. Do not include a query you did not run successfully.
- Do NOT run infra/osrm/build.sh (it rebuilds the data); document it from build.log and PROVENANCE.json, and describe its update behaviour exactly as the script implements it (read the script).
- You may run `docker compose ... down` only if you immediately run `up -d` and the health check passes again. The server must be running when you finish; show `docker compose ps`.
- Note that the server must be restarted after a rebuild.
- At the end, list the commands you ran and their results.
```
