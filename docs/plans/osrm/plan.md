# Local OSRM for Baltimore: plan (v1, 2 Oct 2026)

**Status:** approved by the team on 2 Oct 2026; running.

**Why:** our travel times come from the public OSRM demo server (car profile, no traffic; v0 tables retrieved 29 Sep, the full v1 matrix on 1 Oct). That server:
- is for light use only;
- can change its map data without notice;
- gives us no control over the data version.

The figures also draw straight lines between pickup and drop-off, not road paths. A local OSRM with pinned map data gives:
- reproducible road times;
- unlimited queries;
- real route shapes for the figures and the replay viewer.

**What does not change:** OSRM is still a car on free-flowing roads, with no traffic and no van-specific rules. The scenario's travel-time multiplier, calibrated in Phase 6, still covers evening traffic and van speed.

## Environment facts (checked 2 Oct by the main session)
| Item | Value |
|---|---|
| Machine | Apple Silicon (arm64), 16 GB RAM, 141 GB free |
| Docker | Desktop 29.0.1, running; Linux VM aarch64, 10 CPUs, 8.2 GB memory |
| Image | `ghcr.io/project-osrm/osrm-backend:v6.0.0` has a native `linux/arm64` build (also `latest` and `v5.27.1`). **Pinned to v6.0.0** |
| Port 5000 | **Taken by macOS AirPlay Receiver (ControlCenter)**. The local server listens on host port **5050** |
| Port 5050 | Free |

## Design
- **Map data:** the Geofabrik Maryland extract (`maryland-latest.osm.pbf`), recorded with its md5, its Last-Modified date and its download date. Clipping to Baltimore is not needed at this size; it is a fallback only.
- **Pipeline:** the MLD pipeline, `osrm-extract` (car.lua) → `osrm-partition` → `osrm-customize` → `osrm-routed --algorithm mld --max-table-size 500`. The default table limit (100) is below our 188 locations.
- **Where files live:**
  - data: `data/osrm/` (gitignored);
  - infrastructure: `infra/osrm/` (tracked): `build.sh`, `docker-compose.yml`, `validate_local.py`;
  - docs: `docs/technical/osrm_local.md`.
- **No silent fallback:** if the local server is down, code that asks for local times fails with a clear message. It does not quietly use the demo server. Each source has its own cache, so local and demo results never mix.
- **The v1 files are not touched.** `tt_locations_v1.csv` and the frozen Phase 3 scenarios stay as they are. The local matrix is written as `tt_locations_v2.csv`. Switching the generator to v2 is a team decision for Phase 3 v2.

## Steps
One small agent per step, run in order. Each starts only after the previous one passed its acceptance checks; prompts are in `agent_prompts.md`.

| Step | Who | What | Accept when |
|---|---|---|---|
| A0 | Main session | Preflight (the facts above) | Done 2 Oct ✓ |
| A1 | Agent (Sonnet) | Download the Maryland data, build the routing files, write `build.sh` and `PROVENANCE.json` | The routing files exist; the md5 matches; `build.sh` reruns cleanly |
| A2 | Agent (Sonnet) | `docker-compose.yml` on 127.0.0.1:5050, then validate against the cached demo-server matrix | 188 × 188 complete; r ≥ 0.95; median relative difference ≤ 10%; snapping ≤ 75 m (one documented exception, see log) |
| A3 | Agent (Sonnet) | Add a server switch and per-server caches to `travel_times.py`; build `tt_locations_v2.csv` and route shapes for scenario M | A second run makes zero HTTP calls; 35,344 rows; all 32 tests still pass; the 30 routes start and end within 75 m of their points |
| A4 | Agent (Sonnet) | Write `docs/technical/osrm_local.md` (how to use it) | Every query in the doc was run once and worked; the server is left running |
| A5 | Main session | Review, then re-draw figure (b) with real routes; write the log and the AI-use log | Figure inspected |

## Rules for every agent
- Write only the files named in your prompt.
- Do not commit or push.
- Do not edit `tests/`, `demand.py`, `generator.py`, `figures.py`, or any `*_v1` data file.
- **Stop and report** instead of improvising when a STOP condition is hit. A failed check is reported with its numbers, not tuned until it passes.

## Risks and fallbacks
| Risk | Sign | Fallback (needs main-session approval) |
|---|---|---|
| Extraction runs out of memory | Exit code 137 | Clip to a Baltimore bounding box with osmium, or raise Docker's memory |
| Geofabrik download fails | curl error twice | Retry later, or use the dated Geofabrik file |
| Table request too large | `TooBig` error | Raise `--max-table-size`, or chunk the request |
| Local and demo times disagree beyond tolerance | A2 report | Investigate the map dates and snapping. This is not a tuning job |
