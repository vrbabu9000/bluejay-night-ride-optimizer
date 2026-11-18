# Start here: setting up the Blue Jay Night Ride project on your Mac

This folder walks you from an empty Mac to running the project's simulations. If you also want it, there's an optional step to run the local OSRM road-routing server in Docker. There are two tracks:

- **Track A: simulations only (recommended start).** You need Python and a small data download (about 40 MB). All travel times are already computed, so you don't need Docker or a routing server.
- **Track B: Track A plus the local OSRM server in Docker.** Only needed to compute *new* road travel times or street routes. It adds Docker Desktop and a 1.1 GB map download, and it works only on an **Apple Silicon** Mac (M1/M2/M3/M4…).

Do Track A first even if you want Track B. Track B builds on it.

## The files, in order

| Step | File | Track | Time |
|---|---|---|---|
| 1 | [01_prerequisites.md](01_prerequisites.md): check your Mac, install the tools, clone the repo | A + B | 15–30 min |
| 2 | [02_get_the_data.md](02_get_the_data.md): download the data zips and put them in place | A + B | 5–15 min |
| 3 | [03_run_simulations.md](03_run_simulations.md): Python environment, tests, first simulation | A + B | 15–20 min |
| 4 | [04_docker_osrm.md](04_docker_osrm.md): install Docker Desktop, start the routing server, check it | B only | 15–20 min |
| — | [05_troubleshooting.md](05_troubleshooting.md): fixes for the usual problems | any | — |

Every step ends with a **✅ Check**: a command and the output you should see. Don't move on until the check passes.

## Doing this with Claude Code (recommended)

You can do every step yourself by reading the files, or let Claude Code guide you through them.

1. Do step 1 of [01_prerequisites.md](01_prerequisites.md) up to and including "Clone the repository". Claude needs the repo on your disk to read these files.
2. Open the repo folder in Claude Code (the desktop app's Code tab, or run `claude` in a terminal inside the folder).
3. Paste this as your first message:

   > Read docs/onboarding/README.md and walk me through the setup one step at a time. I want Track A (or: Track A, then Track B). Before each command, tell me what it does. After each step, run its ✅ Check and show me the result before moving on.

### Notes for Claude (the assistant guiding this setup)

- Follow the files in order. Run each ✅ Check and compare its output with the expected output before going on. If they differ, use [05_troubleshooting.md](05_troubleshooting.md) before improvising.
- **Never run `infra/osrm/build.sh`.** It downloads a newer map and rebuilds the routing data, and the team's travel times would no longer match. The shared `data/osrm/` folder is the pinned copy.
- **Never edit, move or regenerate anything in `data/`.** The simulator checks each scenario's content hash and refuses to run if a file changed.
- Don't change the `platform: linux/arm64` lines in `infra/osrm/docker-compose.yml` or `infra/osrm/build.sh`, and don't change port 5050.
- Write simulation output to `outputs/` (the default) or a scratch folder. Don't commit anything. This repo's `CLAUDE.md` says git is manual. Its GitHub account rules apply to the repo owner, not to this setup.
- Installing apps (Homebrew, Python, Docker Desktop) and accepting their licence terms is the user's job. Explain what to click, then wait for them to confirm.

## Background reading (optional)

- [README.md](../../README.md): what the project is.
- [docs/technical/osrm_local.md](../technical/osrm_local.md): the full reference for the OSRM server. Step 4 here is a shorter, guided version of it.
- [docs/README.md](../README.md): index of all project documents.

## A note on the data

`data/` is not in git. Some of it is derived from a restricted JHU document, so it's shared only with team members. Keep the zips private: don't re-share them or upload them anywhere else.
