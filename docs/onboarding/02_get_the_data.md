# Step 2: Get the data

The data isn't in git. You'll get it as one or two zip files from a Google Drive link. Each zip already contains the `data/...` folder structure, so you unzip it **at the root of the repo** and the files land in the right place.

| Zip | Size | Contains | Needed for |
|---|---|---|---|
| `bluejay_data_core.zip` | about 40 MB | `data/scenarios/` (frozen simulation inputs), `data/processed/` (travel-time matrix and other processed tables), `data/raw/` (cached road answers, April data), `data/external/` | Track A and B |
| `bluejay_data_osrm.zip` | about 1 GB | `data/osrm/` (pinned Maryland map and prebuilt routing files) | Track B only |

## 2.1 Download

Open the Drive link and download the zip(s) you need. They usually land in `~/Downloads`.

## 2.2 Unzip at the repo root

From the repo folder (the one with `README.md` in it):

```bash
cd ~/Documents/Git/bluejay-night-ride-optimizer
```

```bash
unzip -q ~/Downloads/bluejay_data_core.zip -d .
```

Track B only:

```bash
unzip -q ~/Downloads/bluejay_data_osrm.zip -d .
```

> Don't double-click the zip in Finder. That creates a separate `bluejay_data_core` folder in Downloads, and you'd have to move things by hand. If you already did, move the `data` folder from inside it into the repo root.

## ✅ Check: core data (Track A)

```bash
ls data
```

Expected: `external  processed  raw  scenarios` (plus `osrm` if you also unzipped the Track B file).

```bash
ls data/scenarios/v2
```

Expected: `FROZEN_v2.json  FROZEN_v2_L6.json  L1  L2  L3  L4  L5  L6  MANIFEST.json`

```bash
ls -l data/processed/tt_locations_v2.csv
```

Expected: the file exists. This is the travel-time matrix every simulation uses.

The stronger check (each scenario's content hash) runs in step 3, after Python is set up.

## ✅ Check: OSRM data (Track B)

```bash
md5 -q data/osrm/maryland-latest.osm.pbf
```

Expected, exactly: `ff90439cea505560649ac52f97b4ea42`

```bash
ls data/osrm | grep -c '^maryland-latest.osrm'
```

Expected: a number around 25 (one per routing file). If you get `0`, the routing files are missing. See [05_troubleshooting.md](05_troubleshooting.md#required-files-are-missing).

```bash
du -sh data/osrm
```

Expected: about `1.1G`.

**Next:** [03_run_simulations.md](03_run_simulations.md)
