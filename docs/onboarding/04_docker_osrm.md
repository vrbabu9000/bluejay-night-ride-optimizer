# Step 4 (Track B): Docker Desktop and the local OSRM server

OSRM is an open-source road router: give it two points and it returns the drive time, distance and street path. The project runs its own copy in Docker with a pinned Maryland map, so road times are reproducible. **You only need this to compute new travel times or routes.** The simulations in step 3 already work without it.

Before you start, make sure that:
- `uname -m` prints `arm64` (Apple Silicon). The shared map files don't work on Intel Macs.
- step 2's OSRM check passed (the md5 is `ff90439cea505560649ac52f97b4ea42`).

## 4.1 Install Docker Desktop

1. Go to https://www.docker.com/products/docker-desktop/ and download **Docker Desktop for Mac – Apple Silicon**.
2. Open the `.dmg` and drag **Docker** into **Applications**.
3. Start Docker from Applications. Accept the service agreement. You can skip signing in.
4. Wait until the whale icon in the menu bar stops animating and the Docker window says **Engine running**.

✅ **Check**

```bash
docker --version
```

```bash
docker compose version
```

```bash
docker info --format '{{.Architecture}}'
```

Expected: a Docker version, a Compose `v2.x` version, and `aarch64`.

## 4.2 Give Docker enough memory

Docker Desktop › **Settings** (gear icon) › **Resources**: set **Memory to at least 4 GB** (the team uses 8 GB) and click **Apply & restart**. The server itself uses about 700 MB, so the extra is headroom.

## 4.3 Start the server

From the repo root:

```bash
cd ~/Documents/Git/bluejay-night-ride-optimizer
```

```bash
docker compose -f infra/osrm/docker-compose.yml up -d
```

The first time, Docker downloads the pinned image `ghcr.io/project-osrm/osrm-backend:v6.0.0` (about 100 MB). After that it starts in about a second.

✅ **Check: the container is up**

```bash
docker compose -f infra/osrm/docker-compose.yml ps
```

Expected: one row named `bluejay-osrm` with status `Up …` and ports `127.0.0.1:5050->5000/tcp`.

```bash
docker compose -f infra/osrm/docker-compose.yml logs --tail 5
```

Expected: a line `running and waiting for requests`.

## 4.4 Health check: ask for a route

Homewood campus to a downtown point:

```bash
curl -sS "http://localhost:5050/route/v1/driving/-76.6205,39.3299;-76.6155,39.2904?overview=false"
```

✅ Expected: the reply starts with `{"code":"Ok"` and contains `"duration":850.8,"distance":6092.9`. Those exact numbers prove you have the team's pinned map. Other numbers mean a different map.

Note that the server uses **port 5050**, not 5000, because macOS reserves 5000 for AirPlay. Coordinates in the URL are **longitude,latitude**.

## 4.5 Use it from Python

The project's travel-time code uses the public demo server unless `OSRM_URL` is set. Point it at your local server for one command:

```bash
OSRM_URL=http://localhost:5050 PYTHONPATH=src .venv/bin/python -c "
from scenario import travel_times as t
r = t.route([(39.323779, -76.614754), (39.287418, -76.611692)])
print(r['duration_s'], 's,', r['distance_m'], 'm')
print(t.nearest(39.344767, -76.626706))
"
```

✅ Expected:

```
524.3 s, 4645 m
{'snap_m': 18.08905342, 'snapped_lat': 39.344823, 'snapped_lon': -76.626509, 'road_name': 'Meadow Lane'}
```

The cache in `data/raw/osrm_cache/local_v6.0.0_ff90439c/` already holds these answers, so they come back instantly. New questions go to the server and are cached.

If the server isn't running, you get `RuntimeError: OSRM server http://localhost:5050 not reachable`. The code never silently falls back to another server.

## 4.6 Day to day

```bash
docker compose -f infra/osrm/docker-compose.yml up -d
```

```bash
docker compose -f infra/osrm/docker-compose.yml down
```

- The compose file uses `restart: unless-stopped`, so the server comes back by itself when Docker Desktop starts, unless you stopped it with `down`.
- `down` removes only the container. Your `data/osrm/` files aren't touched (they're mounted read-only).
- Docker Desktop must be running for any of this. You can quit it when you don't need the router.

## 4.7 What not to do

- **Don't run `infra/osrm/build.sh`.** It downloads *today's* Maryland map and rebuilds everything, so your travel times would no longer match the team's.
- Don't change the port or the `platform: linux/arm64` line in `infra/osrm/docker-compose.yml`.

For the full reference (table queries, validation, updating the map, licence attribution), see [docs/technical/osrm_local.md](../technical/osrm_local.md). Any figure that shows routes or maps must credit "© OpenStreetMap contributors".

**Track B is done.** Problems: [05_troubleshooting.md](05_troubleshooting.md).
