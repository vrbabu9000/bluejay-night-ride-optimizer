# Guide history

These files are read-only snapshots of the Team Technical Guide builder at each version, kept for reading and diffing.
Do not run them. They are frozen, and each computes its output path from its own location, so a run from this folder would write to a stray `docs/output/`.
The current builder is `docs/technical/build_team_guide.py`. Every build also archives its PDF.
Archived PDFs are in `output/pdf/archive/`, one per version.
The change log is `docs/technical/guide_changelog.md`.
The v1 builder stays at `docs/technical/build_team_guide_v1.py`. It rewrites the config template, so never run it either.
