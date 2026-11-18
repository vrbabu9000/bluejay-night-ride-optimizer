# Step 3: Python environment and your first simulation

Here you create the project's Python environment, prove the data is intact, and run simulations. Nothing here needs Docker or the internet beyond installing packages. All travel times come from `data/processed/tt_locations_v2.csv`.

Run everything from the repo root:

```bash
cd ~/Documents/Git/bluejay-night-ride-optimizer
```

## 3.1 Create the environment

```bash
python3.12 -m venv .venv
```

```bash
.venv/bin/pip install --upgrade pip
```

Install the exact package versions the team uses:

```bash
.venv/bin/pip install -r requirements-lock.txt
```

✅ **Check**

```bash
.venv/bin/python -c "import numpy, pandas, scipy, highspy; print('ok', pandas.__version__)"
```

Expected: `ok 3.x.x`

## 3.2 Check the data really is the team's data

The simulator recomputes each scenario's content hash and compares it with `data/scenarios/v2/FROZEN_v2.json`:

```bash
PYTHONPATH=src .venv/bin/python -c "
from sim import inputs
for n in ['L1', 'L4', 'L5/r00']:
    inputs.load(n)
    print(n, 'OK')
"
```

✅ Expected:

```
L1 OK
L4 OK
L5/r00 OK
```

A `RuntimeError: ... content hash ... does not match` means a file in `data/scenarios` differs from the team's copy. Download and unzip the core zip again.

## 3.3 First simulation (takes under a second)

L1 is the smallest hand-checked validation case: 16 requests.

```bash
PYTHONPATH=src .venv/bin/python -m sim.run --level L1 --rule R0
```

✅ Expected last line: `wrote .../outputs/sim/L1_R0`

Open the human-readable summary:

```bash
open outputs/sim/L1_R0/narrative.md
```

It should start with `# L1 under R0: what happened` and report `Outcomes: van_completed 16`.

Each run folder contains:

| File | What it is |
|---|---|
| `narrative.md` | Short readable account of the night, with one worked comparison of competing plans |
| `outcomes.csv` | One row per ride request: wait, ride time, outcome |
| `events.csv` | Every event in time order |
| `epochs.jsonl` | Each re-planning moment: state, candidate plans, solver result |
| `run_manifest.json` | Input hashes, settings, code and solver versions |

## 3.4 A bigger run (about 35 seconds)

```bash
PYTHONPATH=src .venv/bin/python -m sim.run --level L4 --rule R0
```

Useful options (`--help` shows them all):

- `--level` picks the scenario: `L1` … `L5`, or one night such as `L5/r00`.
- `--rule` picks the Lyft transfer rule, e.g. `R0` (no Lyft), `R1(10)`.
- `--out some/folder` writes somewhere other than `outputs/sim/`.

The larger experiment runners (`sim.batch`, `sim.m5`) take many minutes to hours and use several CPU cores. Their usage is at the top of `src/sim/batch.py` and `src/sim/m5.py`. Ask the team before starting one, so you run the agreed settings.

## 3.5 Run the tests (optional, slower)

A quick subset of the engine tests (about 3 minutes):

```bash
.venv/bin/python -m pytest tests/test_sim_engine.py -q
```

✅ Expected: `32 passed`

The full suite (about 9 minutes on an M-series Mac):

```bash
.venv/bin/python -m pytest tests -q
```

✅ Expected: `286 passed` (the exact number may grow as tests are added; what matters is `0 failed`).

**Track A is done.** For Track B, continue with [04_docker_osrm.md](04_docker_osrm.md).
