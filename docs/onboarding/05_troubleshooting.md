# Troubleshooting

Find the symptom you see below. For OSRM problems not listed here, see section 9 of [docs/technical/osrm_local.md](../technical/osrm_local.md#9-troubleshooting).

## Setup and Python

### python3.12 not found

Homebrew installed Python but your shell can't see it. Run the "Next steps" commands Homebrew printed at the end of its install, then open a new Terminal window. Or call it by its full path:

```bash
$(brew --prefix python@3.12)/bin/python3.12 -m venv .venv
```

### `pip install` fails building a package

The lock file is for Python 3.12 on Apple Silicon. Check that you made the environment with 3.12:

```bash
.venv/bin/python --version
```

If it's not 3.12, delete `.venv` and redo step 3.1. On an Intel Mac, if a pinned version has no Intel build, use the looser list instead:

```bash
.venv/bin/pip install -r requirements.txt
```

### `ModuleNotFoundError: No module named 'sim'` (or `'scenario'`)

You left out `PYTHONPATH=src`, or you're not in the repo root. Run `cd` to the repo root, then repeat the command exactly as written.

### `content hash ... does not match FROZEN_v2.json`

A scenario file differs from the team's copy, usually because of a partial unzip or an edited file. Delete `data/scenarios` and unzip `bluejay_data_core.zip` again (step 2.2).

### `FileNotFoundError` for something under `data/`

The zip was unzipped in the wrong place, so `data/` isn't at the repo root. `ls data` from the repo root must show `scenarios processed raw external`.

### `git clone` asks for a password and rejects it

GitHub doesn't accept your account password over HTTPS. Install the GitHub CLI (`brew install gh`), run `gh auth login`, and choose HTTPS plus browser login. Then clone again. Also check you accepted the collaborator invite.

## Docker and OSRM

### "Cannot connect to the Docker daemon"

Docker Desktop isn't running. Open it from Applications and wait for **Engine running**.

### Port 5050 already in use

```bash
lsof -nP -iTCP:5050 -sTCP:LISTEN
```

If it's Docker (`com.docke…`), the server is already running, which is fine. If it's another program, quit that program. Don't move the server to another port.

### Required files are missing

`ps` shows `Restarting (1)` and the logs say `Required files are missing, cannot continue`. This means `data/osrm/` is missing or incomplete. Unzip `bluejay_data_osrm.zip` again and repeat step 2's OSRM check.

### Exited (137)

Docker ran out of memory. Raise memory in Docker Desktop › Settings › Resources, choose Apply & restart, and start the server again.

### "no matching manifest for linux/arm64" or other platform errors

You're probably on an Intel Mac (`uname -m` prints `x86_64`). The shared routing files are Apple Silicon only. Use Track A. The simulations don't need the server.

### Health check gives different numbers from 850.8 / 6092.9

The map isn't the team's pinned one. Check `md5 -q data/osrm/maryland-latest.osm.pbf` is `ff90439cea505560649ac52f97b4ea42`. If it differs, or if `build.sh` was run, delete `data/osrm` and unzip the OSRM zip again.

### `code: Ok` but the route is 0 s, or a waypoint moved thousands of metres

Latitude and longitude are swapped. URLs take `longitude,latitude`, while the Python functions take `(lat, lon)`.

## Still stuck?

Send the project owner the exact command, the full error output, and the output of:

```bash
uname -m; sw_vers -productVersion; .venv/bin/python --version; docker --version
```
