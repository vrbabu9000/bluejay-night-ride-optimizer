# Scenario methodology companion (PDF)

A readable explanation of how a simulated Night Ride evening is built, what the simulator must do, and how the van dispatcher scores plans. It is an **explanatory companion** to `scenario_methodology.md`, `scenario_spec.md` (§17), `model_design.md` and `decision_log.md`. It adds no rule, number or decision; where the sources disagree it lists the point in `CONFLICTS.md` instead of resolving it.

**Status:** companion for `scenario_methodology.md` **v1.6** (23 Oct 2026). Section 7 reports the verified M0–M2 status and the M3 batch; its tables are re-derived from saved outputs (`SOURCES.md`).

**Archive:** superseded builds are kept in `archive/` as `BlueJay_Scenario_Methodology_methodology-v{X}_{date}.pdf`, named after the methodology version they reflect (the same convention as `docs/technical/archive/`).

## Files

| File | What it is |
|---|---|
| `BlueJay_Scenario_Methodology.pdf` | The built document |
| `methodology.tex` | LaTeX source (XeLaTeX) |
| `make_figures.py` | Draws the eight figures into `figures/` with matplotlib (no simulation output) |
| `figures/*.pdf` | Generated figures |
| `build.sh` | Rebuilds figures and PDF |
| `SOURCES.md` | Source documents, versions and SHA-256 fingerprints |
| `CONFLICTS.md` | Conflicts and gaps found between the sources, and where the authoritative documents settled them |
| `_build/` | Created by `build.sh` for LaTeX intermediates; not kept (delete after building) |

## Rebuild

```bash
docs/technical/methodology_pdf/build.sh
```

Requirements: XeLaTeX from TinyTeX (`~/Library/TinyTeX/bin/universal-darwin/xelatex`, or set `XELATEX=`), and the project Python (`.venv/bin/python`, or set `PY=`) with matplotlib. The build runs three LaTeX passes (for the contents and cross-references) and prints any overfull-box warnings.

Fonts: Charter, STIX Two Math, Helvetica Neue and Menlo (macOS system fonts); the source falls back to Latin Modern elsewhere. Figures use Arial.

## Conventions in the PDF

- Statement kinds: **ASSUMED** (input rule we chose), **DESIGNED CHECK** (L1–L4 hand-checks), **SIMULATED** (outcomes only the simulation produces), plus **APRIL EVIDENCE** and **DERIVED** for dashboard numbers and arithmetic on them.
- Approval status: accepted / provisional / proposed, not approved / open, following the decision log.
