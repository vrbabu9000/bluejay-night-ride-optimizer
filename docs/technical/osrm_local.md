# Local OSRM server: how to use it (2 Oct 2026)

For teammates. Background and the step log: `docs/plans/osrm/plan.md` and `docs/plans/osrm/log.md`. Run every command from the repo root.

Every command in this file was run on 2 Oct 2026 against the running server (sections 6 to 8 were updated the same day after two fixes: the local cache is now keyed by the map extract, and the validation report reads the newest build; the examples were re-run) (Apple Silicon Mac, Docker Desktop 29.0.1, Compose v2.40.3, osrm-backend v6.0.0). Three things were not run in place: `infra/osrm/build.sh` (it rebuilds the data, so its numbers come from `data/osrm/build.log`), and `travel_times_v2.py` and `validate_local.py` (they overwrite data files, so they were run in a scratch copy of the repo; they reproduced the project's files and numbers).

## 1. What it is and why we use it

OSRM is an open-source road router: it turns two points on a map into a drive time, a distance and a street path. We run our own copy on this Mac, in Docker, with a pinned Maryland map from OpenStreetMap, so road times are reproducible and we can ask as many questions as we like; the public demo server we used for the v0 and v1 tables is for light use and can change its map without notice. The times are free-flow car times: a car on an empty road, with no traffic and no van rules. An evening-traffic and van-speed factor is applied later as a named scenario parameter (calibrated in Phase 6).

## 2. Prerequisites

- **An Apple Silicon Mac.** The image `ghcr.io/project-osrm/osrm-backend:v6.0.0` runs as `linux/arm64`, and both `docker-compose.yml` and `build.sh` pin that platform. We have not tried other machines. `[12 Oct]` The same image tag is also published for `linux/amd64` (Intel/AMD Windows or Linux), but that is **untested** for us: an x86-64 build is not guaranteed to give bit-identical travel times, and serving these arm64-built files with the amd64 image is undocumented. **Copy `data/osrm/` only between machines of the same architecture.** For simulations, teammates need only the matrix file and its fingerprints, not this server (proposal P-02, `compute_feasibility.md` §4). `PROVENANCE.json` records the multi-architecture *index* digest; the arm64 manifest digest should be added when provenance is next updated.
- **Docker Desktop, running.** We used 29.0.1 with a VM of 10 CPUs and 8.2 GB of memory.
- **Disk:** about 1.2 GB for the map data in `data/osrm/`, plus about 100 MB for the image.
- **`curl`** for the examples and the project's Python environment (`.venv`) for the Python examples.
- **Port 5050, not 5000.** macOS keeps port 5000 for the AirPlay Receiver (on this Mac it is held by `ControlCenter`). The container's port 5000 is published on host port **5050**, on `127.0.0.1` only, so the server is reachable from this Mac and not from the network. Every URL below uses 5050.

## 3. One-time build

```bash
infra/osrm/build.sh
```

You can run it from any directory. It was run on 2 Oct 2026 and the data is already on the machine that built it (`data/osrm/`). The numbers here come from `data/osrm/build.log` and `data/osrm/PROVENANCE.json`.

What it downloads and builds:

1. The Geofabrik Maryland extract `maryland-latest.osm.pbf` (214,986,055 bytes, about 215 MB) from `https://download.geofabrik.de/north-america/us/`, checked against the md5 that Geofabrik publishes next to it.
2. The OSRM image `ghcr.io/project-osrm/osrm-backend:v6.0.0` for `linux/arm64` (about 100 MB), only if the machine does not have it yet.
3. The routing files `data/osrm/maryland-latest.osrm.*`, made by `osrm-extract` (car profile), `osrm-partition` and `osrm-customize` (together they build the files for OSRM's MLD routing method).
4. `data/osrm/PROVENANCE.json`: source URL, the extract's md5, size and dates, image tag and digest.

Everything it prints is also appended to `data/osrm/build.log`. It does not start the server (section 4). The first build printed 15 warnings (about u-turns and unreachable boundary nodes) and no errors (`log.md`, step A1).

| Step | Time on 2 Oct 2026 |
|---|---|
| Download of the extract | 35 s |
| Image pull (first time only) | about 6 s |
| `osrm-extract` | 27 s |
| `osrm-partition` | 11 s |
| `osrm-customize` | 2 s |
| **Whole script, first run** | **84 s** |
| Whole script, rerun (download skipped, routing files rebuilt) | 42 s |

**Disk use:** `data/osrm/` is about 1.2 GB (`du -sh data/osrm` prints `1.2G`): the 215 MB extract plus about 1 GB of routing files.

**Building on your own machine.** `data/` is in `.gitignore`, so a fresh clone has no map data and the server will not start (section 9). Ask before you run `build.sh` yourself: it fetches whatever `maryland-latest` Geofabrik has that day, and Geofabrik refreshes that file daily, so your map (and your travel times) would differ from the team's. For team results, copy the whole `data/osrm/` folder from the machine that built it and check that the extract is the pinned one:

```bash
md5 -q data/osrm/maryland-latest.osm.pbf
```

The answer must equal `md5` in `data/osrm/PROVENANCE.json` (now `ff90439cea505560649ac52f97b4ea42`). Copy the folder rather than rebuild: a rebuild from the same extract is not byte-identical (`log.md`, step A1).

## 4. Start, stop, status and logs

```bash
docker compose -f infra/osrm/docker-compose.yml up -d            # start
docker compose -f infra/osrm/docker-compose.yml ps               # status
docker compose -f infra/osrm/docker-compose.yml logs --tail 20   # last 20 log lines
docker compose -f infra/osrm/docker-compose.yml down             # stop and remove the container
```

While it runs, `ps` shows one container, `bluejay-osrm`, and the port mapping:

```
NAME           IMAGE                                      COMMAND                  SERVICE   CREATED         STATUS         PORTS
bluejay-osrm   ghcr.io/project-osrm/osrm-backend:v6.0.0   "osrm-routed --algor…"   osrm      4 minutes ago   Up 4 minutes   127.0.0.1:5050->5000/tcp
```

After `down`, `ps` shows an empty list. The log of a fresh start looks like this (timestamps left out):

```
bluejay-osrm  | [info] starting up engines, v6.0.0
bluejay-osrm  | [info] Listening on: 0.0.0.0:5000
bluejay-osrm  | [info] running and waiting for requests
bluejay-osrm  | [info] 02-10-2026 17:58:20 2.287ms 172.18.0.1 - curl/8.7.1 200 /route/v1/driving/-76.6205,39.3299;-76.6155,39.2904?overview=false
```

After "running and waiting for requests" there is one line per request: the time it took, the status code (200 answered, 400 refused) and the request. "Listening on 0.0.0.0:5000" is inside the container; Docker publishes it on `127.0.0.1:5050` of your Mac.

- It starts in about a second (0.8 s from `up -d` to the first answer).
- `up -d` on a server that is already running does nothing (it prints `Running`).
- `down` removes the container and its log. The data in `data/osrm/` is not touched.
- The compose file sets `restart: unless-stopped`, so Docker brings the server back when Docker Desktop starts, unless you stopped it with `down`.
- The data folder is mounted read-only. The server runs with `--algorithm mld` (the routing files were built for MLD; the default method cannot load them, so keep that flag) and `--max-table-size 500`.

## 5. Health check and two example queries

**Health check.** A short route query:

```bash
curl -sS "http://localhost:5050/route/v1/driving/-76.6205,39.3299;-76.6155,39.2904?overview=false"
```

A healthy server answers like this (shortened: the long `hint` strings are replaced by `...`):

```json
{"code":"Ok","routes":[{"legs":[{"steps":[],"weight":892.1,"summary":"","duration":850.8,"distance":6092.9}],"weight_name":"routability","weight":892.1,"duration":850.8,"distance":6092.9}],"waypoints":[{"hint":"...","location":[-76.62049,39.3299],"name":"","distance":0.8622871427},{"hint":"...","location":[-76.615501,39.290408],"name":"","distance":0.8923477994}]}
```

If the server is not running, curl prints `curl: (7) Failed to connect to localhost port 5050 after 0 ms: Couldn't connect to server` (see section 9).

How to read it:

- Coordinates are **longitude,latitude** (the other way round from the usual "lat, lon"), one pair per point, joined by `;`. The Python functions take `(lat, lon)` and do the swap for you.
- `duration` is in seconds (850.8 s, about 14 minutes) and `distance` in metres (6,093 m, about 6.1 km) for the whole route.
- `waypoints` says where each point landed on the road. Its `distance` is how many metres the point was moved to reach the road (the "snap distance").

**Example 1, a route.** The health check above is one: Homewood to a point downtown.

**Example 2, a table** (every pair among three points, here Homewood and two downtown points):

```bash
curl -sS "http://localhost:5050/table/v1/driving/-76.6205,39.3299;-76.6155,39.2904;-76.6122,39.2897?annotations=duration,distance"
```

```json
{"code":"Ok","distances":[[0,6092.9,6186.5],[6310.1,0,813.2],[7566,510,0]],"destinations":[...],"durations":[[0,850.8,865.6],[965.3,0,127.3],[888.7,76.3,0]],"sources":[...]}
```

Rows are origins and columns are destinations, in the order you listed the points. So `durations[0][1]` is 850.8 s, from point 1 to point 2. The matrix is not symmetric (850.8 s there, 965.3 s back) because of one-way streets and turn rules; that is why our matrices are directed.

**What `"code": "Ok"` means.** Every reply has a `code`. `Ok` means the server understood the request and worked out an answer. Anything else is an error with a `message`, for example:

- `TooBig`, "Too many table coordinates": the table asks for more pairs than the server allows (section 9).
- `NoSegment`, "Could not find a matching segment for coordinate 0": no road within the radius you gave (below).

**`Ok` does not mean your points are near a road.** This server moves every point to the nearest road in the Maryland map, however far away that is. A point at 0,0, or a latitude and longitude written the wrong way round, still gets `"code":"Ok"` and a route. For example, with latitude first:

```bash
curl -sS "http://localhost:5050/route/v1/driving/39.3299,-76.6205;39.2904,-76.6155?overview=false"
```

This answers `"code":"Ok"` with a route of 0 s and 0 m, and both waypoints moved about 17,500 km, to the same spot on the road network. Always look at the waypoint `distance`: for our 188 locations the largest is 94.9 m (section 7). Thousands of metres means the point is outside Maryland or swapped.

To make the server refuse such points, give a radius in metres for each point:

```bash
curl -sS "http://localhost:5050/route/v1/driving/0,0;-76.6155,39.2904?overview=false&radiuses=75;75"
```

```json
{"message":"Could not find a matching segment for coordinate 0","code":"NoSegment"}
```

Our Python functions do not set a radius. They rely on the snap check recorded in `locations_snap_v2.csv` (section 6).

## 6. How the project uses it

**Choosing the server: `OSRM_URL`.** `src/scenario/travel_times.py` reads the environment variable `OSRM_URL` when it is imported. If it is not set, the code uses the public demo server (`https://router.project-osrm.org`), so every v0 and v1 script runs as before. In code, `set_server("http://localhost:5050")` does the same. Set the variable for one command, as below, rather than in your shell profile.

```bash
OSRM_URL=http://localhost:5050 PYTHONPATH=src .venv/bin/python - <<'EOF'
from scenario import travel_times as t

print(t.SERVER, t.CACHE_DIR.relative_to(t.ROOT))
r = t.route([(39.323779, -76.614754), (39.287418, -76.611692)])   # (lat, lon) pairs: pickup and drop-off of request R001
print(r["duration_s"], "s,", r["distance_m"], "m,", len(r["coords"]), "points")
print(t.nearest(39.344767, -76.626706))                           # location p02_b001
print("HTTP calls:", t.HTTP_CALLS)
EOF
```

```
http://localhost:5050 data/raw/osrm_cache/local_v6.0.0_ff90439c
524.3 s, 4645 m, 190 points
{'snap_m': 18.08905342, 'snapped_lat': 39.344823, 'snapped_lon': -76.626509, 'road_name': 'Meadow Lane'}
HTTP calls: 0
```

`HTTP calls: 0` because these two answers are already in the cache. On a machine without the cache the same script makes 2 calls. (Scripts inside `src/scenario` import the module as `travel_times`; from the repo root use `PYTHONPATH=src` as above.)

**What `travel_times.py` offers** (points are always `(lat, lon)`):

| Name | What it gives you |
|---|---|
| `table(src, dst)` | Durations (s) and distances (m) as nested lists, for lists of points |
| `matrix(src_df, dst_df, src_id, dst_id)` | A DataFrame `origin, dest, seconds, meters` of all ordered pairs. Local: blocks of 200 x 200. Demo: blocks of 50 x 50, about 1 s apart |
| `route(points)` | `duration_s`, `distance_m` and `coords`, the street path as `[lon, lat]` points (ready for GeoJSON) |
| `nearest(lat, lon)` | `snap_m` (metres moved to the road), `snapped_lat`, `snapped_lon`, `road_name`. A van stops at the snapped point, not at the digitized coordinate |
| `HTTP_CALLS` | The number of real network calls this Python process has made. Cache hits are not counted; a failed attempt is |

**Per-server caches.** Every answer is saved to disk the first time, so a rerun does not ask again. Each server has its own folder, so local and demo answers never mix:

| Server | Cache folder |
|---|---|
| Demo (the default) | `data/raw/osrm_cache/` (unchanged since v0) |
| Local, port 5050 | `data/raw/osrm_cache/local_v6.0.0_ff90439c/` |
| Local, another port | `data/raw/osrm_cache/local_v6.0.0_ff90439c_port<N>/` |
| Any other server | `data/raw/osrm_cache/<host and path>/`, for example `osrm.example.org_8443_osrm` |

A cache file is named from a hash of the request, and keeps the request, the answer, the server and the UTC time it was fetched. The local folder name holds the OSRM version **and the first 8 characters of the map extract's md5** (`ff90439c`, from `PROVENANCE.json`), so a new map build starts a fresh cache and old travel times can never come back under a new data date (section 8).

**No silent fallback.** If the server you chose cannot be reached, the call stops with an error. It never quietly switches to another server, so local and demo numbers cannot get mixed by accident:

```
RuntimeError: OSRM server http://localhost:5050 not reachable; see docs/technical/osrm_local.md
```

That message sends you to this page: start the server (section 4). A question that is already in the cache is answered from disk without the server, so reruns work even when it is down; a new question needs the server. If the server answers but refuses the request, the message is `RuntimeError: OSRM server ... refused the request: {...}` with OSRM's own reply (see `TooBig` in section 9).

**`travel_times_v2.py`** builds the road products from the local server:

```bash
.venv/bin/python src/scenario/travel_times_v2.py
```

| Output in `data/processed/` | What it holds |
|---|---|
| `tt_locations_v2.csv` | All 188 x 188 = 35,344 ordered pairs of `locations_v1.csv`, with the same columns as `tt_locations_v1.csv` (`origin, dest, seconds, meters, source, retrieval_date`). The diagonal is 0. The `source` column names the build, for example `OSRM local v6.0.0, Geofabrik maryland-latest (Last-Modified 2026-10-02), car, free-flow` |
| `routes_M_v2.geojson` | The street path of the 30 trips of scenario M, pickup to drop-off: 61.0 km in all, against 45.6 km as straight lines (`log.md`, step A3) |
| `locations_snap_v2.csv` | For each of the 188 locations: `snap_m`, the snapped point and the road name |

If the server is down it stops with an error; it never falls back to the demo server. Checked on 2 Oct: from an empty cache it made 218 requests in about a second and wrote files byte-identical to the project's; the next run made 0 requests.

**The v1 files are untouched.** `tt_locations_v1.csv` (demo server, retrieved 1 Oct), the v0 tables `tt_zones_v0.csv` and `tt_points_v0.csv` (demo server, retrieved 29 Sep) and the frozen Phase 3 scenarios are as they were. The scenario generator still uses the v1 matrix; moving it to v2 is a separate team decision (`plan.md`).

**A guard against mixing.** `src/scenario/locations.py` builds the v1 matrix from the demo server. If `OSRM_URL` points to any other server, it refuses to run (so local times cannot overwrite the demo matrix):

```
RuntimeError: locations.py builds the v1 matrix from the demo server, but OSRM_URL points to http://localhost:5050; unset it to run this script
```

Running `travel_times.py` as a script, which rebuilds the v0 tables, has the same guard.

## 7. Validation results

The local server was compared with the demo-server matrix `tt_locations_v1.csv` on all 188 x 188 pairs, by `infra/osrm/validate_local.py`. The full report is `data/osrm/validation_report.md`. Evidence label: DERIVED (comparison statistics from two routing tables; neither is a measured van time).

| Check | Limit | Result |
|---|---|---|
| Table reply code | `Ok` | `Ok` |
| Complete, no missing values | 188 x 188 | 188 x 188, 0 missing (35,344 pairs) |
| Pearson r, seconds | at least 0.95 | **0.9993** |
| Median relative difference, seconds | at most 10% | **1.25%** |
| Largest snap distance | at most 75 m | 94.9 m at `p04_b037` (the one exception, below) |

In plain terms: half of the pairs differ by 1.25% or less, 95% by 5.3% or less, and 99.7% by 10% or less (the worst single pair is 23.5%, a 2 s gap on an 8.5 s trip). Local is slower by 1.14% at the median. Snapping: median 11.1 m, 95th percentile 31.1 m; 19 locations are over 25 m, 2 over 50 m and 1 over 75 m.

**The one snapping exception.** Location `p04_b037` (Hampden, a small bubble: April weight 2.0 of 48,112, or 0.004%) lands 94.9 m away, on Poole Street. The next worst is 60.3 m (`p02_b004`, Underwood Road). It was waived on 2 Oct and recorded in `docs/plans/osrm/log.md` (step A2):

- it is a large-block location with a georeference uncertainty of 28 m (how precisely the bubble could be placed on the map);
- both servers snap it the same way;
- its pairs differ from the demo times by 2.9% at the median, against 1.2% for the rest;
- the coordinate was not moved (provenance). Instead, every location's snap distance is recorded in `locations_snap_v2.csv`.

Because of this one location the script prints `[FAIL] Max snapping distance` and exits with code 1, and the report says FAIL (4 of 5 checks). That is the known state, not a new problem. Any other failed check, or numbers that move after a data update, should be looked at before the data is used.

**Why local times run about 1% slower.** On 83% of the pairs both servers chose a route of the same length. On those, local is a median 2.0 s slower, and where the times differ, 97% of the gaps are a multiple of 2 s. That matches the penalty the v6.0.0 car profile adds for each traffic signal or stop sign (2 s; 1 s for a give-way sign), so part of the gap comes from the OSRM version or profile, not only from the map. The other 17% of pairs took a different route length, which fits different map dates (the demo server does not publish its map date). The test cannot separate these causes.

**What this does not show.** It compares two routers on free-flowing roads. It says nothing about real night traffic or van times; Phase 6 calibrates that.

## 8. Updating the map data

Update only when the team decides to move to newer data: between experiments, never in the middle of one, and never to change results you have already seen. Everything built from the old data must then be rebuilt (steps 6 to 8).

**When `build.sh` downloads.** The decision is made on the file's md5, not on a date:

1. Every run first reads the md5 that Geofabrik publishes next to the extract (`maryland-latest.osm.pbf.md5`).
2. No local `data/osrm/maryland-latest.osm.pbf`: it downloads one.
3. Local file present and its md5 equals the published md5: it skips the download (the log says `SKIP download`).
4. Local file present and its md5 differs: Geofabrik has published a newer extract (it refreshes the file daily), so the script downloads it again and replaces the file.
5. After a download it checks the md5 again. On a mismatch it deletes the file, reads the published md5 again and tries once more; a second mismatch stops the build. A failed download (after two retries) also stops the build.
6. Whether or not it downloaded, it then rebuilds the routing files (about 40 s). So do not run it just to check for news: it always replaces the routing files.
7. It deletes `PROVENANCE.json` before the rebuild and writes it again only when the build has finished. If the file is there, the routing files were built from exactly that extract. If a build stops half-way there is no `PROVENANCE.json`, and the routing files cannot be trusted: run `build.sh` again.

**Where the new data date goes.** `build.sh` writes it into `PROVENANCE.json` itself: `http_last_modified` (Geofabrik's date for the file), `downloaded_utc`, `built_utc`, `md5` and `size_bytes`. The date of the newest edit inside the extract (the OSM timestamp, 2026-10-01T20:22:06Z for our data) is logged in `build.log`, not in `PROVENANCE.json`.

**Steps**

1. Tell the team, and finish or archive any experiment that runs on the old data.
2. Stop the server, so nothing reads the files while they change (`build.sh` does not touch the server):
   ```bash
   docker compose -f infra/osrm/docker-compose.yml down
   ```
3. Rebuild:
   ```bash
   infra/osrm/build.sh
   ```
4. Check the new record. The `md5` and dates must be the new ones:
   ```bash
   cat data/osrm/PROVENANCE.json
   grep -a "timestamp:" data/osrm/build.log | tail -1
   ```
   The second line prints the newest OSM timestamp.
5. Start the server again and run the health check (section 5). **The server only reads the files when it starts, so it must be restarted after every rebuild.**
   ```bash
   docker compose -f infra/osrm/docker-compose.yml up -d
   ```
6. Rebuild the v2 outputs. A new extract has a new md5, so `travel_times.py` uses a new cache folder (`local_v6.0.0_<new md5>`) by itself; the old folder stays as the record of the old build. Copy the old v2 files first if you want to keep them (`data/` is not in git):
   ```bash
   .venv/bin/python src/scenario/travel_times_v2.py
   ```
   After an update the script must report about 218 HTTP requests. **If it reports 0, the cache folder did not change**, which means `PROVENANCE.json` still names the old extract (the build did not finish): go back to step 3. (Until 2 Oct the folder was named after the OSRM version only, and a scratch test showed old answers being relabelled with the new date; keying the folder by the extract's md5 fixed that.)
7. Run the validation again (it overwrites `validation_report.md` and `validation_pairs.csv`). Today it exits with code 1 only because of the `p04_b037` exception; after an update, read the numbers against section 7 and look into any other failure. The report takes its "OSM data timestamp" from the **last** `timestamp:` line in `build.log`, the build now being served (fixed on 2 Oct; it used to read the first line).
   ```bash
   .venv/bin/python infra/osrm/validate_local.py
   ```
8. Rebuild everything made from the old v2 files (figures that draw routes, scenarios, results) and record the new data date and the reason in `docs/technical/decision_log.md`.

**One data date per experiment.** Matrices built from different map-data dates must not be mixed in one experiment. Every policy, scenario and figure in an experiment uses files from one build. `tt_locations_v2.csv` and `routes_M_v2.geojson` carry the build in their `source` label (it includes the `Last-Modified` date); `locations_snap_v2.csv` has no label, so always rebuild the three together. Do not treat a v1 (demo) number and a v2 (local) number as one source. To see which build a matrix came from:

```bash
sed -n 2p data/processed/tt_locations_v2.csv
```

```
p02_b001,p02_b001,0.0,0.0,"OSRM local v6.0.0, Geofabrik maryland-latest (Last-Modified 2026-10-02), car, free-flow",2026-10-02
```

## 9. Troubleshooting

**Port in use.** `up -d` fails with a message that mentions port 5050, for example `Bind for 127.0.0.1:5050 failed: port is already allocated`. See who holds the port:

```bash
lsof -nP -iTCP:5050 -sTCP:LISTEN
```

When our server is running this shows Docker Desktop (`com.docke...`) on `127.0.0.1:5050`; that is normal. If it is another program, stop that program. Do not move our server to another port: `travel_times_v2.py` expects 5050, and another port gets its own cache folder. Port 5000 is not an option on a Mac (AirPlay Receiver).

**Exit 137 (out of memory).** `build.sh` stops with a line like `FAIL  osrm-extract: exit code 137 after 12s` and the note "137 = process killed, most likely out of memory". The build worked with 8.2 GB for Docker. Raise the memory in Docker Desktop > Settings > Resources, choose Apply & restart, and run `build.sh` again. If you cannot, ask the team: the plan's fallback is to clip the map to a Baltimore box first. A running server that was killed shows `Exited (137)` in `ps -a`; the same fix applies. The server itself is small:

```bash
docker stats --no-stream bluejay-osrm
```

```
CONTAINER ID   NAME           CPU %     MEM USAGE / LIMIT     MEM %     NET I/O          BLOCK I/O   PIDS
3567882e8791   bluejay-osrm   0.00%     684.8MiB / 7.653GiB   8.74%     368kB / 4.04MB   0B / 0B     12
```

**`TooBig`.** The reply is `{"code":"TooBig","message":"Too many table coordinates"}`. A table request is refused when sources x destinations is more than 500 x 500 = 250,000 pairs (set by `--max-table-size 500` in `infra/osrm/docker-compose.yml`; OSRM's own default is 100, which is below our 188 locations). We checked the edge: 500 x 500 is answered, 500 x 501 is refused. Our code asks for at most 200 x 200, so you only meet this with a hand-made request. In Python it appears as `RuntimeError: OSRM server http://localhost:5050 refused the request: {'message': 'Too many table coordinates', 'code': 'TooBig'}`. Fix it by asking for smaller blocks, or by raising `--max-table-size` in the compose file and restarting the server (`down`, then `up -d`).

**Image platform errors.** Messages about a platform or manifest mismatch (for example "no matching manifest for linux/arm64") mean Docker has, or wants, an image for the wrong CPU type. The image must be the Apple Silicon one; check it:

```bash
docker image inspect --format '{{.Os}}/{{.Architecture}}' ghcr.io/project-osrm/osrm-backend:v6.0.0
```

```
linux/arm64
```

If it prints something else, the image has to be pulled again for `linux/arm64`. `build.sh` does that itself when the local image is not `linux/arm64` (it then also rebuilds the routing files). On an Intel Mac or a Windows/Linux PC the pinned image is untested: ask before changing the `platform` lines in `docker-compose.yml` and `build.sh`.

**The container is not running.** Symptoms: `curl: (7) Failed to connect to localhost port 5050`, or `RuntimeError: ... not reachable`. Look at all containers, including stopped ones:

```bash
docker compose -f infra/osrm/docker-compose.yml ps -a
```

- **An empty list:** the server was never started, or `down` was run. Use `up -d`.
- **Docker commands fail with a message about connecting to the Docker daemon:** Docker Desktop is not running. Open it and wait until it says it is running.
- **`Restarting (1)`, and `logs` ends with `[error] Required files are missing, cannot continue`:** `data/osrm/` has no routing files, as on a fresh clone. Get the folder (section 3).
- **`Exited (137)`:** out of memory (above).

**`Ok`, but the numbers look wrong.** A zero-length route or a huge waypoint `distance` means a point is outside Maryland or latitude and longitude are swapped (section 5).

## 10. License

The map data is OpenStreetMap data, © OpenStreetMap contributors, available under the Open Database License (ODbL). Put "© OpenStreetMap contributors" on any figure or slide that shows routes, snapped points or a map, for example in a corner of the figure or in its caption. The Geofabrik extract, the routes and the travel times we derive from it all come from that data. If we ever share the route or travel-time files themselves, not only figures, check the ODbL rules first. More: https://www.openstreetmap.org/copyright
