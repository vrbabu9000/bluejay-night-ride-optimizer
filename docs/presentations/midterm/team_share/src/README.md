# Team preparation pack: authoring source

This folder holds the source of the team-facing pack in `../v1.0/`. Teammates use only the PDFs in `../v1.0/`; nothing here needs to be shared.

## Rebuild
```
.venv/bin/python docs/presentations/midterm/team_share/src/build_pack.py
```
Requirements:
- XeLaTeX from TinyTeX (`~/Library/TinyTeX/bin/universal-darwin/xelatex`, or set `XELATEX=`);
- the macOS fonts Arial, Helvetica Neue and Menlo.

LaTeX intermediates are written to `../_build/` and can be deleted after a build.

## Single content source
`build_pack.py` generates the shared guide, the four presenter briefs and *Start here* from the same inputs, so the narration never diverges between documents:
- **Narration, context and transitions:** `../../v0.4/speaking_script.md`, the finalized script.
- **Preparation notes and likely questions:** `../../v0.4/slide_explanations.md`. Its repository links are dropped; each slide instead gets page references into the methodology PDF.
- **Pack-specific content:** `content.py`, which holds:
  - presenter assignments and handoff sentences;
  - methodology page map, Q&A ownership and backup list;
  - shared-understanding points;
  - the four verification activities, with their reference answers;
  - designer notes.

## Copied artifacts
- **The deck:** `02_Final_Presentation.pdf` is `../../v0.4/BlueJay_Midterm_v0.4_preview.pdf`, unchanged.
- **The designer copy:** `designer_Irfan_Setiadi/BlueJay_Midterm_v0.4.pptx` is the finalized v0.4 deck, unchanged.
- **The methodology:** `03_Scenario_Methodology_v1.6.pdf` is `docs/technical/methodology_pdf/BlueJay_Scenario_Methodology.pdf`, rebuilt for methodology v1.6 (`docs/technical/methodology_pdf/build.sh`).

## Conventions
- **Methodology pages:** references use printed page numbers. Links open the physical page, which is the printed page + 1.
- **Guide pages:** printed and physical page numbers are the same.
- **Cross-document links:** relative to the share folder (`../` from `presenter_briefs/`), so they work after the folder is copied or zipped. PDF viewers differ in how they follow links between files; the printed page references are the fallback.
- **Verification records:** every record starts as "Awaiting human completion". Never pre-fill names, dates or results.
