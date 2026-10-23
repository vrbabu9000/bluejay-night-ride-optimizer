"""Resolve the handbook's short link tokens to real heading anchors, and check every relative link in the v0.4 package.

    python3 docs/presentations/midterm/v0.4/resolve_links.py

Token form, used while authoring: ](@M:7a.)  = the methodology heading whose text starts with "7a."; ](@D:#) = the file itself.
Files: M scenario_methodology.md, D decision_log.md, S scenario_spec.md, Z model_design.md, T transloc_operations.md.
GitHub anchor rule: lower-case, drop characters other than letters, digits, spaces, hyphens and underscores, spaces -> hyphens.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TECH = HERE.parents[2] / "technical"
FILES = {"M": "scenario_methodology.md", "D": "decision_log.md", "S": "scenario_spec.md", "Z": "model_design.md", "T": "transloc_operations.md"}


def slug(h):
    return re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-")


def headings(path):
    return [m.group(1) for m in re.finditer(r"^#{1,6} (.+)$", path.read_text(), re.M)]


def resolve(text):
    def sub(m):
        key, pre = m.group(1), m.group(2)
        rel = f"../../../technical/{FILES[key]}"
        if pre == "#":
            return f"]({rel})"
        hits = [h for h in headings(TECH / FILES[key]) if h.startswith(pre) and (not pre.endswith(".") or h[len(pre):len(pre) + 1] == " ")]
        if len(hits) != 1:
            sys.exit(f"token @{key}:{pre} matches {len(hits)} headings: {hits[:3]}")
        return f"]({rel}#{slug(hits[0])})"
    return re.sub(r"\]\(@([MDSZT]):([^)]+)\)", sub, text)


def check(md):
    bad = []
    for target in re.findall(r"\]\(([^)]+)\)", md.read_text()):
        if target.startswith("http"):
            continue
        f, _, anchor = target.partition("#")
        p = (md.parent / f).resolve() if f else md
        if not p.exists():
            bad.append(f"{md.name}: missing file {target}")
            continue
        if anchor and p.suffix == ".md":
            t = p.read_text()
            ok = anchor in {slug(h) for h in headings(p)} or f'id="{anchor}"' in t
            if not ok:
                bad.append(f"{md.name}: missing anchor {target}")
    return bad


if __name__ == "__main__":
    for name in ("slide_explanations.md",):
        p = HERE / name
        p.write_text(resolve(p.read_text()))
    problems = [b for md in sorted(HERE.glob("*.md")) for b in check(md)] + [b for md in sorted((HERE / "reviews").glob("*.md")) for b in check(md)]
    print("\n".join(problems) or "all relative links and anchors resolve")
    sys.exit(1 if problems else 0)
