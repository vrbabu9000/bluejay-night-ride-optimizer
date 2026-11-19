"""
Build the L6 nights (Phase 4 M4; decision D-59, approved 10 Nov 2026).

    data/scenarios/v2/L6/base_5/r00..r29   base pattern, 5 vans, 64 / 50 / 54 = 168 requests (D-36)
    data/scenarios/v2/L6/base_6/r00..r29   the SAME requests and latent draws, 6 vans (D-37)
    data/scenarios/v2/L6/high_5/r00..r29   high load (rho x 1.3), 5 vans, 83 / 66 / 70 = 219 requests
    data/scenarios/v2/L6/{base,high}_5/r30..r59   fresh nights for M5d (D-64, proposed; added 18 Nov 2026)

Each night's content hash is written to FROZEN_v2_L6.json under 'L6/<pattern>_<fleet>/rNN'. FROZEN_v2.json (L1-L5) is
never touched: the dispersed variant records its exact bytes. An existing L6 entry may only be rebuilt to the identical hash; anything else stops the build.
Burst and far-trip are deferred to M7. The first-hour slice used by M5 is the first n_0 requests of each night
(t_request_s < 3600); it is cut at run time, not stored separately.

Run: .venv/bin/python src/scenario/build_l6_v2.py
"""
import json
import sys

try:            # imported as the package scenario.*
    from . import generator_v2 as g
except ImportError:   # run as a script from src/scenario
    import generator_v2 as g

REPLICATES = range(30)
CELLS = (("base", 5), ("base", 6), ("high", 5))
# M5d (D-64, proposed, 18 Nov 2026): fresh nights for testing a rule chosen on r00-r29. Same generator and seeds
# scheme (replicate is part of the seed key), so r30-r59 are new independent draws; r00-r29 are rebuilt unchanged.
FRESH_REPLICATES = range(30, 60)
FRESH_CELLS = (("base", 5), ("high", 5))


def main():
    for pat, exp in g.L6_EXPECTED.items():
        got = g.l6_hour_counts(pat)
        if got != exp:
            sys.exit(f"hour counts for {pat}: {got} != hand calculation {exp}")
    path = g.OUT / "FROZEN_v2_L6.json"
    frozen = json.loads(path.read_text()) if path.exists() else {}
    n_new = 0
    jobs = [(c, r) for c in CELLS for r in REPLICATES] + [(c, r) for c in FRESH_CELLS for r in FRESH_REPLICATES]
    for (pat, fleet), r in jobs:
        req, lat, av, params = g.build_l6(pat, r, n_vans=fleet)
        key = f"L6/{pat}_{fleet}/r{r:02d}"
        sc = g.write_scenario(g.OUT / key, req, lat, av, params)
        if key in frozen and frozen[key] != sc["content_hash"]:
            sys.exit(f"{key}: rebuilt hash {sc['content_hash'][:12]} differs from frozen {frozen[key][:12]}")
        n_new += key not in frozen
        frozen[key] = sc["content_hash"]
    path.write_text(json.dumps(frozen, indent=2) + "\n")
    print(f"L6: {len(jobs)} nights written ({n_new} new frozen entries); "
          f"hour counts base {g.l6_hour_counts('base')}, high {g.l6_hour_counts('high')}")


if __name__ == "__main__":
    main()
