"""
Phase 3, step 3.6: the pre-registered scenario grid (docs/technical/preregistration.md).

Base cell = scenario M. Every other cell changes exactly one factor (one at a
time), except the L check. Replicate r uses the same seeds in every cell
(common random numbers), so cells differ only by the factor they change: the
capacity and start cells even share the base cell's requests byte for byte.
The batching window W is a dispatcher setting, not a scenario: the rho x W heat
map runs the four rho cells under each W in {30, 60, 120} s.

Run: .venv/bin/python src/scenario/build_grid.py      (writes 11 cells x 30 replicates)
"""
import pandas as pd

try:            # imported as the package scenario.*
    from .demand import ROOT
    from .generator import build_scenario, default_params
except ImportError:   # run as a script from src/scenario
    from demand import ROOT
    from generator import build_scenario, default_params

OUT = ROOT / "data" / "scenarios" / "grid"
REPLICATES = 30
CELLS = {
    "base":            {},                                    # M: rho 6, Poisson, beta 0.1, month average, cap 4, hotspot
    "rho4":            {"n_requests": 20},
    "rho9":            {"n_requests": 45},
    "rho12":           {"n_requests": 60},                    # = "as requested"
    "burst":           {"arrivals": "burst"},
    "beta0":           {"beta_per_min": 0.0},
    "beta0.2":         {"beta_per_min": 0.2},
    "campus_outbound": {"direction": "campus_outbound_6pm"},
    "cap7":            {"capacity": 7},
    "depot":           {"start_rule": "depot"},
    "L170":            {"n_vans": 27, "n_requests": 170},     # one real-density check (players A, B, C only)
}
WINDOWS_S = (30, 60, 120)


def main():
    rows = []
    for cell, over in CELLS.items():
        p = default_params()
        p.update({"cell": cell, **over})
        for r in range(REPLICATES):
            sc = build_scenario(p, r, OUT / cell / f"r{r:02d}")
            rows.append({"cell": cell, "replicate": r, "requests": sc["summary"]["requests"],
                         "passengers": sc["summary"]["passengers"], "content_hash": sc["content_hash"]})
        print(f"{cell:16s} {REPLICATES} replicates")
    m = pd.DataFrame(rows)
    m.to_csv(OUT / "manifest.csv", index=False, lineterminator="\n")
    print(f"{len(m)} scenarios; manifest {OUT / 'manifest.csv'}")


if __name__ == "__main__":
    main()
