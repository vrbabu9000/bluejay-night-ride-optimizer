#!/usr/bin/env bash
# Rebuild the midterm report PDF.  Usage (from anywhere):  docs/report/midterm/build.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PDFLATEX="${PDFLATEX:-$HOME/Library/TinyTeX/bin/universal-darwin/pdflatex}"
PY="${PY:-$REPO/.venv/bin/python}"

"$PY" "$HERE/make_report_figures.py"
"$PY" "$HERE/fig_charts.py"
"$PY" "$HERE/fig_diagrams.py"

BUILD="$HERE/_build"
mkdir -p "$BUILD"
cd "$HERE"
for pass in 1 2 3; do
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD" BlueJayNightRide_Midterm.tex > "$BUILD/pass$pass.out"
done
cp "$BUILD/BlueJayNightRide_Midterm.pdf" "$HERE/BlueJayNightRide_Midterm.pdf"
echo "Wrote $HERE/BlueJayNightRide_Midterm.pdf"
grep -E "Overfull|undefined|LaTeX Warning" "$BUILD/BlueJayNightRide_Midterm.log" || echo "No overfull boxes or LaTeX warnings."
