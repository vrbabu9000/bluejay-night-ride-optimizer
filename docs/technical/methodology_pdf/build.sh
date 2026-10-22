#!/usr/bin/env bash
# Rebuild the scenario-methodology companion PDF.
# Usage (from anywhere):  docs/technical/methodology_pdf/build.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
XELATEX="${XELATEX:-$HOME/Library/TinyTeX/bin/universal-darwin/xelatex}"
PY="${PY:-$REPO/.venv/bin/python}"

"$PY" "$HERE/make_figures.py"

BUILD="$HERE/_build"
mkdir -p "$BUILD"
cd "$HERE"
for pass in 1 2 3; do
  "$XELATEX" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD" methodology.tex > "$BUILD/pass$pass.out"
done
cp "$BUILD/methodology.pdf" "$HERE/BlueJay_Scenario_Methodology.pdf"
echo "Wrote $HERE/BlueJay_Scenario_Methodology.pdf"
grep -E "Overfull|Underfull \\\\hbox \(badness 10000\)|LaTeX Warning" "$BUILD/methodology.log" || echo "No overfull boxes or LaTeX warnings."
