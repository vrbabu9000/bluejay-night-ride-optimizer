# For the project owner: packaging the data to share

This makes the two zips that [02_get_the_data.md](02_get_the_data.md) expects. Run it from the repo root on the machine that holds the team's data. Both zips keep the `data/...` paths, so the recipient unzips them at their repo root.

```bash
cd ~/Documents/Git/bluejay-night-ride-optimizer
```

Core data (simulations, about 40 MB unzipped; everything in `data/` except `data/osrm/`):

```bash
zip -rq ~/Desktop/bluejay_data_core.zip data -x "data/osrm/*" -x "*.DS_Store"
```

OSRM map data (Track B, about 1.1 GB unzipped):

```bash
zip -rq ~/Desktop/bluejay_data_osrm.zip data/osrm -x "*.DS_Store"
```

Check the contents before uploading:

```bash
unzip -l ~/Desktop/bluejay_data_core.zip | tail -1
```

```bash
unzip -l ~/Desktop/bluejay_data_osrm.zip | grep -c "maryland-latest.osrm"
```

Upload both to Google Drive and share **only with the named recipient**, not with "anyone with the link". Some of the data is derived from a restricted JHU document.

Send the recipient:
1. the Drive link,
2. a GitHub collaborator invite to the repo,
3. a pointer to `docs/onboarding/README.md`.
