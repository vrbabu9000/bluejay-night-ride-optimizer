#!/usr/bin/env bash
# Rebuild the Lyft-budget proposal PDF (personal draft, not a team deliverable).
# Usage (from anywhere): docs/report/proposals/miles_lyft_budget/build.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v pdflatex >/dev/null 2>&1; then
  PDFLATEX="pdflatex"
elif [ -x "$HOME/Library/TinyTeX/bin/universal-darwin/pdflatex" ]; then
  PDFLATEX="$HOME/Library/TinyTeX/bin/universal-darwin/pdflatex"
else
  echo "No pdflatex found (checked PATH and ~/Library/TinyTeX). Install TinyTeX or MacTeX first." >&2
  exit 1
fi

BUILD="$HERE/_build"
mkdir -p "$BUILD"
cd "$HERE"
for pass in 1 2; do
  "$PDFLATEX" -interaction=nonstopmode -halt-on-error -output-directory="$BUILD" BlueJay_LyftBudget_Proposal.tex > "$BUILD/pass$pass.out"
done
cp "$BUILD/BlueJay_LyftBudget_Proposal.pdf" "$HERE/BlueJay_LyftBudget_Proposal.pdf"
echo "Wrote $HERE/BlueJay_LyftBudget_Proposal.pdf"
grep -E "Overfull|undefined|LaTeX Warning" "$BUILD/BlueJay_LyftBudget_Proposal.log" || echo "No overfull boxes or LaTeX warnings."
