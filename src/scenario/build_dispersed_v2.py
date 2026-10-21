"""
Build the dispersed-geography variant (D-34) of the L5 rehearsal nights, aligned with the frozen reference.

Each night is read from the reference (data/scenarios/v2/L5/rNN): request times, cluster-level O-D, party sizes,
rider traits and van availability are copied unchanged; only endpoints at coarse city clusters move to one of the
cluster's road satellites (src/scenario/spread.py). L1-L4 stay on the reference geography: they are
hand-checked mechanism tests whose answer keys depend on exact travel times.

Outputs: data/scenarios/v2_dispersed/{MANIFEST.json, FROZEN_v2_dispersed.json, L5/rNN/}
Run: .venv/bin/python src/scenario/build_dispersed_v2.py      (after spread.py; no routing calls)
"""
import hashlib
import json

import pandas as pd

try:
    from . import generator_v2 as g
except ImportError:
    import generator_v2 as g

VARIANT = "dispersed_v1"
REF = g.OUT
OUT = g.ROOT / "data" / "scenarios" / "v2_dispersed"


def main():
    sites = pd.read_csv(g.PROCESSED / f"locations_{VARIANT}.csv")
    mat = pd.read_csv(g.PROCESSED / f"tt_locations_{VARIANT}.csv")
    sec = dict(zip(zip(mat.origin, mat.dest), mat.seconds))
    prov_path = g.PROCESSED / f"{VARIANT}_provenance.json"
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"variant": VARIANT, "reference_manifest_sha256": g.sha256(REF / "MANIFEST.json"),
                "reference_frozen_sha256": g.sha256(REF / "FROZEN_v2.json"),
                "files": {f: g.sha256(g.PROCESSED / f) for f in
                          (f"locations_{VARIANT}.csv", f"tt_locations_{VARIANT}.csv", f"{VARIANT}_provenance.json")}}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    frozen, total_redraws = {}, 0
    for f in sorted((REF / "L5").glob("r*")):
        ref_sc = json.loads((f / "scenario.json").read_text())
        req = pd.read_csv(f / "requests.csv")
        disp, redraws = g.disperse_requests(req, "L5", "base", ref_sc["params"]["replicate"], sites, sec)
        total_redraws += redraws
        params = dict(ref_sc["params"])
        params["geography"] = {"variant": VARIANT, "reference_content_hash": ref_sc["content_hash"],
                               "sites_sha256": manifest["files"][f"locations_{VARIANT}.csv"], "satellite_redraws": redraws}
        sc = g.write_scenario(OUT / "L5" / f.name, disp, pd.read_csv(f / "latent.csv"),
                              pd.read_csv(f / "availability.csv"), params, manifest_path=OUT / "MANIFEST.json")
        frozen[f"L5/{f.name}"] = sc["content_hash"]
    (OUT / "FROZEN_v2_dispersed.json").write_text(json.dumps(frozen, indent=2) + "\n")
    print(f"built {len(frozen)} dispersed nights; satellite redraws for the 60-s minimum trip: {total_redraws}; "
          f"provenance {prov_path.name}")


if __name__ == "__main__":
    main()
