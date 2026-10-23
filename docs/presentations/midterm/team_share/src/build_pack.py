"""Build the team preparation pack (PDFs) from the finalized v0.4 package.

    .venv/bin/python docs/presentations/midterm/team_share/src/build_pack.py

Inputs (read-only):
  v0.4/speaking_script.md, v0.4/slide_explanations.md      narration, transitions, context, preparation notes
  v0.4/BlueJay_Midterm_v0.4_preview.pdf and .pptx           the finalized deck
  docs/technical/methodology_pdf/BlueJay_Scenario_Methodology.pdf   the rebuilt methodology PDF (v1.6)
  content.py                                                assignments, handoffs, activities, Q&A ownership
Output: team_share/v1.0/ (PDFs, presenter_briefs/, designer_Irfan_Setiadi/). LaTeX intermediates go to team_share/_build/
(not kept). Requires XeLaTeX (TinyTeX).
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402

MID = HERE.parents[1]                      # docs/presentations/midterm
V04 = MID / "v0.4"
REPO = MID.parents[2]
OUT = MID / "team_share" / "v1.0"
BUILD = MID / "team_share" / "_build"
XELATEX = os.environ.get("XELATEX", str(Path.home() / "Library/TinyTeX/bin/universal-darwin/xelatex"))
METH_PDF = REPO / "docs/technical/methodology_pdf/BlueJay_Scenario_Methodology.pdf"


# ---------------------------------------------------------------- markdown → LaTeX
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(t):
    return "".join(SPECIAL.get(c, c) for c in t)


def inline(t):
    """Convert inline markdown (code, bold, italic, links) to LaTeX; escape the rest."""
    out, i = [], 0
    pat = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\*\(optional\)\*|\*([^*]+)\*|\[([^\]]+)\]\(([^)]+)\)")
    for m in pat.finditer(t):
        out.append(esc(t[i:m.start()]))
        if m.group(1) is not None:
            out.append(r"\texttt{" + esc(m.group(1)) + "}")
        elif m.group(2) is not None:
            out.append(r"\textbf{" + inline(m.group(2)) + "}")
        elif m.group(0) == "*(optional)*":
            out.append(r"\optional{}")
        elif m.group(3) is not None:
            out.append(r"\emph{" + inline(m.group(3)) + "}")
        else:
            out.append(inline(m.group(4)))           # link text only; repository links do not travel with the pack
        i = m.end()
    out.append(esc(t[i:]))
    s = "".join(out)
    s = re.sub(r'(^|[\s(\[/])"', r"\1``", s).replace('"', "''")
    return s.replace("‘", "`").replace("’", "'").replace("“", "``").replace("”", "''")


def table(lines):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\|\s*-", l.strip())]
    n = len(rows[0])
    spec = "@{}" + ">{\\raggedright\\arraybackslash}X" * n + "@{}"
    body = [r"{\small\begin{tabularx}{\linewidth}{" + spec + "}", r"\toprule"]
    for k, r in enumerate(rows):
        cells = [inline(c) for c in r] + [""] * (n - len(r))
        if k == 0:
            cells = [r"\textbf{" + c + "}" for c in cells]
        body.append(" & ".join(cells) + r"\\")
        if k == 0:
            body.append(r"\midrule")
    body += [r"\bottomrule", r"\end{tabularx}}", ""]
    return "\n".join(body)


def md(text):
    """Block-level markdown subset: paragraphs, nested bullet and numbered lists, pipe tables."""
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        l = lines[i]
        if not l.strip() or l.strip() == "---":
            i += 1
            continue
        if l.lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            out.append(table(lines[i:j]))
            i = j
            continue
        if re.match(r"^\s*(- |\d+\. )", l):
            j, items = i, []
            while j < len(lines) and (re.match(r"^\s*(- |\d+\. )", lines[j]) or (lines[j].startswith("   ") and lines[j].strip())):
                items.append(lines[j])
                j += 1
            out.append(lists(items))
            i = j
            continue
        para = [l.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^\s*(- |\d+\. |\|)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(inline(" ".join(para)) + "\n")
    return re.sub(r"\(§(\d{1,2})\)", r"(slide \1)", "\n".join(out))


def lists(items):
    out, stack = [], []
    for raw in items:
        m = re.match(r"^(\s*)(- |\d+\. )(.*)$", raw)
        if not m:
            out[-1] += " " + inline(raw.strip())
            continue
        depth = len(m.group(1)) // 2
        kind = "itemize" if m.group(2) == "- " else "enumerate"
        while len(stack) > depth + 1:
            out.append(r"\end{" + stack.pop() + "}")
        if len(stack) == depth + 1 and stack[-1] != kind:
            out.append(r"\end{" + stack.pop() + "}")
        while len(stack) < depth + 1:
            stack.append(kind)
            out.append(r"\begin{" + kind + "}")
        out.append(r"\item " + inline(m.group(3)))
    while stack:
        out.append(r"\end{" + stack.pop() + "}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- parse the v0.4 sources
def parse_script():
    s = (V04 / "speaking_script.md").read_text()
    slides = {}
    for blk in re.split(r'(?=<a id="s\d\d"></a>)', s)[1:]:
        n = int(re.search(r'id="s(\d\d)"', blk).group(1))
        title, secs = re.search(r"^## \d+ · (.+?) \((\d+) s\)", blk, re.M).groups()
        ctx = re.search(r"\*\*Context\.\*\* (.+)", blk).group(1)
        spoken = [x for x in re.findall(r"^> (.*)$", blk, re.M)]
        tr = re.findall(r"\*\*Transition\*\* > (.*)", blk)
        slides[n] = dict(title=title.strip(), secs=int(secs), context=ctx.strip(), spoken=spoken,
                         transition=(tr[0].replace("**⇄**", "").strip() if tr else ""))
    return slides


def parse_handbook():
    s = (V04 / "slide_explanations.md").read_text()
    out = {}
    for blk in re.split(r'(?=<a id="s\d\d"></a>)', s)[1:]:
        n = int(re.search(r'id="s(\d\d)"', blk).group(1))
        body = blk.split("\n", 2)[2]                                  # drop anchor and heading lines
        body = re.sub(r"^\[Script\]\([^)]*\)\s*$", "", body, flags=re.M)
        body = re.sub(r"\[Script\]\([^)]*\)", "", body)
        body = re.sub(r"^\*\*Read:\*\*.*$", "", body, flags=re.M)      # replaced by methodology PDF references
        body = re.split(r"\n## (Backups|Source note|Glossary)", body)[0]
        out[n] = body.strip().rstrip("-").strip()
    return out


SLIDES = parse_script()
HB = parse_handbook()


def presenter_of(n):
    return next(p for p in C.PRESENTERS if p[2] <= n <= p[3])


def words(n):
    sp = " ".join(SLIDES[n]["spoken"]) + " " + spoken_transition(n)
    return len(sp.replace("*(optional)*", "").split())


def spoken_transition(n):
    if n in C.HANDOFFS:
        return C.HANDOFFS[n][2]
    return SLIDES[n]["transition"] or "(End of the talk; questions follow.)"


def section_secs(p):
    return sum(SLIDES[n]["secs"] for n in range(p[2], p[3] + 1))


def mmss(sec):
    return f"{sec // 60}:{sec % 60:02d}"


# ---------------------------------------------------------------- LaTeX building blocks
PREAMBLE = r"""
\documentclass[11pt,letterpaper]{article}
\usepackage[letterpaper,left=0.95in,right=0.95in,top=0.9in,bottom=0.9in,footskip=0.4in]{geometry}
\usepackage{fontspec}
\setmainfont{Arial}
\setsansfont{Helvetica Neue}
\setmonofont[Scale=0.85]{Menlo}
\usepackage{xcolor,graphicx,booktabs,array,tabularx,longtable,enumitem,framed,titlesec,titleps,microtype,amsmath,amssymb,multicol}
\usepackage[colorlinks=true,linkcolor=linkblue,urlcolor=linkblue,filecolor=linkblue,bookmarksnumbered=true,bookmarksopen=true]{hyperref}
\usepackage{bookmark}
\definecolor{ink}{HTML}{1E2933}\definecolor{muted}{HTML}{5B6670}\definecolor{heading}{HTML}{0B2545}
\definecolor{linkblue}{HTML}{1B5FB0}\definecolor{saybg}{HTML}{EAF2FC}\definecolor{saybar}{HTML}{2A78D6}
\definecolor{prepbg}{HTML}{F4F5F7}\definecolor{prepbar}{HTML}{8A939B}\definecolor{workbg}{HTML}{FFF8E8}\definecolor{workbar}{HTML}{C9A227}
\definecolor{refbg}{HTML}{EEF7F2}\definecolor{refbar}{HTML}{0F7A57}
\color{ink}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.5em plus 0.1em}
\setlist{itemsep=0.12em,topsep=0.2em,parsep=0.05em,leftmargin=1.3em}
\linespread{1.05}\renewcommand{\arraystretch}{1.15}\setlength{\emergencystretch}{2em}\raggedbottom
\newcolumntype{P}[1]{>{\raggedright\arraybackslash}p{#1}}
\titleformat{\section}{\sffamily\Large\bfseries\color{heading}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\sffamily\large\bfseries\color{heading}}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\sffamily\normalsize\bfseries\color{heading}}{}{0em}{}
\titlespacing*{\section}{0pt}{1.2em}{0.5em}\titlespacing*{\subsection}{0pt}{1.0em}{0.35em}\titlespacing*{\subsubsection}{0pt}{0.8em}{0.2em}
\newpagestyle{main}{\setfoot{\sffamily\footnotesize\color{muted}DOCTITLE}{}{\sffamily\footnotesize\color{muted}\thepage}}
\pagestyle{main}
% boxes: spoken (blue bar), preparation (grey bar), your working (gold), reference (green)
\newenvironment{barbox}[3]{\def\FrameCommand{{\color{#2}\vrule width 3.5pt}\fboxsep=7pt\colorbox{#1}}\MakeFramed{\advance\hsize-\width\FrameRestore}%
  {\sffamily\footnotesize\bfseries\color{#2}#3}\par\smallskip}{\endMakeFramed}
\newenvironment{say}{\begin{barbox}{saybg}{saybar}{SAY (exact narration)}\large}{\end{barbox}}
\newenvironment{prep}[1][PREPARATION (not spoken)]{\begin{barbox}{prepbg}{prepbar}{#1}\small}{\end{barbox}}
\newenvironment{work}{\begin{barbox}{workbg}{workbar}{YOUR WORKING}}{\end{barbox}}
\newenvironment{refans}{\begin{barbox}{refbg}{refbar}{REFERENCE ANSWER (compare only after finishing your own working)}}{\end{barbox}}
\newcommand{\optional}{{\sffamily\scriptsize\color{muted}[optional]}~}
\newcommand{\who}[1]{{\sffamily\small\bfseries\color{saybar}#1}}
\newcommand{\blank}[1][1]{\par\vspace{#1\baselineskip}\noindent\rule{\linewidth}{0.3pt}}
\makeatletter\newcommand{\needspace}[1]{\par\penalty-100\begingroup\setlength{\dimen@}{#1}\dimen@ii\pagegoal\advance\dimen@ii-\pagetotal\ifdim\dimen@>\dimen@ii\ifdim\dimen@ii>\z@\vfil\fi\break\fi\endgroup}\makeatother
"""


SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-"))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉", "0123456789"))


def glyphs(t):
    t = t.replace("→", r"\ensuremath{\rightarrow}").replace("≈", r"\ensuremath{\approx}").replace("≤", r"\ensuremath{\le}").replace("≥", r"\ensuremath{\ge}")
    t = re.sub("[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+", lambda m: r"\textsuperscript{" + "".join(SUP[c] for c in m.group(0)) + "}", t)
    return re.sub("[₀₁₂₃₄₅₆₇₈₉]+", lambda m: r"\textsubscript{" + "".join(SUB[c] for c in m.group(0)) + "}", t)


def doc(title, body, footer):
    return (PREAMBLE.replace("DOCTITLE", footer) + "\n\\hypersetup{pdftitle={" + title + "},pdfauthor={Team FourSight}}\n"
            + "\\begin{document}\n" + glyphs(body) + "\n\\end{document}\n")


def meth_ref(n, base):
    refs = C.METH.get(n, [])
    return "; ".join(r"\href[page=" + str(p + 1) + "]{" + base + C.METH_FILE + "}{§" + sec + " " + t + ", p.~" + str(p) + "}"
                     for sec, t, p in refs)


def deck_link(page, base, label=None):
    return r"\href[page=" + str(page) + "]{" + base + C.DECK_FILE + "}{" + (label or f"slide {page}") + "}"


def spoken_block(n):
    paras = "\n\n".join(inline(p) for p in SLIDES[n]["spoken"])
    tr = spoken_transition(n)
    head = ""
    if n in C.HANDOFFS:
        a, b, _ = C.HANDOFFS[n]
        head = r"\par\medskip{\sffamily\footnotesize\bfseries\color{saybar}HANDOFF: " + esc(a) + " → " + esc(b) + "}\\par\n"
    else:
        head = r"\par\medskip{\sffamily\footnotesize\bfseries\color{saybar}TRANSITION}\par" + "\n"
    return r"\begin{say}" + "\n" + paras + "\n" + head + inline(tr) + "\n" + r"\end{say}" + "\n"


def slide_section(n, base=""):
    t = SLIDES[n]
    p = presenter_of(n)
    bk = sorted({b for q in C.QA for b in q[3] if n in q[2]})
    bkl = ", ".join(deck_link(b, base, f"slide {b} (" + next(c for pp, c, _ in C.BACKUPS if pp == b) + ")") for b in bk) or "none specific"
    s = [r"\phantomsection\section*{Slide " + str(n) + " · " + inline(t["title"]) + r"}\label{slide:" + str(n) + "}",
         r"\addcontentsline{toc}{subsection}{" + str(n) + " · " + inline(t["title"]) + "}",
         r"\who{" + esc(p[0]) + r"} \quad {\sffamily\small\color{muted}about " + str(t["secs"]) + r" s · " +
         deck_link(n, base, "open slide " + str(n)) + "}",
         r"\par\textbf{Why it is here.} " + inline(t["context"]), spoken_block(n),
         r"\begin{prep}", md(HB[n])]
    if n in C.HANDOFFS:
        s.append(r"\textbf{Script's own transition} (alternative wording): " + inline(SLIDES[n]["transition"]) + r"\par")
    s += [r"\textbf{Backup slides:} " + bkl + r"\par",
          r"\textbf{Methodology PDF:} " + (meth_ref(n, base) or "---") + r"\par", r"\end{prep}", r"\clearpage"]
    return "\n".join(s)


# ---------------------------------------------------------------- the shared guide
def guide():
    rows = "\n".join(
        f"{esc(p[0])} & {p[2]}--{p[3]} & {inline(SLIDES[p[2]]['title'])} → {inline(SLIDES[p[3]]['title'])} & {esc(p[4])} & {mmss(section_secs(p))}\\\\"
        for p in C.PRESENTERS)
    total = sum(section_secs(p) for p in C.PRESENTERS)
    slide_rows = "\n".join(
        f"{n} & \\hyperref[slide:{n}]{{{inline(SLIDES[n]['title'])}}} & {esc(presenter_of(n)[0].split()[0])} & {SLIDES[n]['secs']}\\\\"
        for n in range(1, 29))
    handoffs = "\n".join(r"\item \textbf{" + esc(a) + " → " + esc(b) + "} (end of slide " + str(n) + "): ``" + inline(t) + "''"
                         for n, (a, b, t) in C.HANDOFFS.items())
    qa = "\n".join(
        f"{inline(top)} & {esc(own.split()[0])} & " + ", ".join(rf"\hyperref[slide:{s}]{{{s}}}" for s in sl) + " & "
        + (", ".join(deck_link(b, "", str(b)) for b in bk) or "---") + r"\\" for top, own, sl, bk in C.QA)
    shared = "\n".join(r"\item \textbf{" + a + r".} " + b for a, b in C.SHARED)
    qindex = "\n".join(f"\\hyperref[slide:{n}]{{{{{inline(q)}}}}} & {n} & {esc(presenter_of(n)[0].split()[0])}\\\\"
                       for n in range(1, 29) for q in re.findall(r"^\s*- \*\*(.+?\?)\*\*", HB[n], re.M))
    backups = "\n".join(f"{p} & {b} & {esc(t)}\\\\" for p, b, t in C.BACKUPS)
    body = rf"""
\begin{{titlepage}}\thispagestyle{{empty}}
\vspace*{{0.7in}}{{\sffamily\small\color{{muted}} Blue Jay Night Ride · Team FourSight · EN.553.602 · Midterm\par}}
\vspace{{0.2in}}{{\sffamily\fontsize{{26}}{{31}}\selectfont\bfseries\color{{heading}} Team Presentation Guide\par}}
\vspace{{0.12in}}{{\sffamily\Large\color{{heading}} When should Night Ride move a waiting request to Lyft?\par}}
\vspace{{0.35in}}
\begin{{prep}}[THE STORY IN ONE PARAGRAPH]\normalsize {C.STORY}\end{{prep}}
\vspace{{0.2in}}
{{\sffamily\small
\begin{{tabular}}{{@{{}}lp{{11.5cm}}@{{}}}}
Pack version & Team share v1.0 (23 October 2026)\\
Presentation & Final slides (built as content draft v0.4): 28 main slides, backup divider on slide 29, backups on slides 30--38\\
Methodology & {C.METH_VERSION} (file {esc(C.METH_FILE)})\\
Timing & About {mmss(total)} of narration plus about 45~s of handoffs (about 27 minutes); \textbf{{an estimate, not yet rehearsed}}\\
\end{{tabular}}}}
\vfill
{{\small\color{{muted}} How to read: blue boxes are the exact words to say; grey boxes are preparation material that is not spoken. Every slide title in the contents is a link, and every slide section links to the deck and the methodology PDF in this folder.}}
\end{{titlepage}}
\setcounter{{page}}{{2}}
\tableofcontents
\clearpage

\section{{Presenters and section boundaries}}\label{{sec:presenters}}
{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{2.6cm}}P{{1.1cm}}XP{{4.3cm}}P{{1.2cm}}@{{}}}}
\toprule\textbf{{Presenter}} & \textbf{{Slides}} & \textbf{{From → to}} & \textbf{{Responsibility}} & \textbf{{Time}}\\\midrule
{rows}
\bottomrule\end{{tabularx}}}}

Irfan Setiadi opens the talk and is also the design lead for the slides. Times are spoken narration plus about 4~s of pause per slide, from the finalized script: \textbf{{about {mmss(total)} in total plus about 45~s for three handoffs, about 27 minutes}}. Reading numbers slowly can add about a minute; dropping the \optional{{}}sentences saves about 1.5 minutes. This is an estimate until the team has timed a full rehearsal; the limit is 30 minutes.

\textbf{{Longer technical sections.}} Miles (8 slides) and Youzhi (8 slides) carry the longest sections. Rehearse them with a stopwatch per slide: slides 14--16 (architecture, decision cycle, mathematics) and 7 (workload) are the densest. Sentences marked \optional{{}} in the narration can be dropped if a section runs long; do not drop the qualifications in bold on the slides.

\subsection*{{Exact handoff sentences}}
\begin{{itemize}}
{handoffs}
\end{{itemize}}
The incoming presenter starts directly with the first sentence of the next slide, with no re-introduction.

\subsection*{{Every main slide and its presenter}}
{{\small\begin{{longtable}}{{@{{}}P{{0.6cm}}P{{10.2cm}}P{{1.9cm}}P{{1.0cm}}@{{}}}}
\toprule\textbf{{\#}} & \textbf{{Title}} & \textbf{{Presenter}} & \textbf{{s}}\\\midrule\endhead
{slide_rows}
\bottomrule\end{{longtable}}}}
\clearpage

\section{{Quick Q\&A navigation}}\label{{sec:qa}}
Route each question to its owner rather than improvising. The guide column links to the slide's preparation notes; the backup column opens the deck at that page (in slide-show mode, type the number and press Enter).

{{\small\begin{{longtable}}{{@{{}}P{{6.6cm}}P{{1.6cm}}P{{2.6cm}}P{{2.6cm}}@{{}}}}
\toprule\textbf{{Question is about}} & \textbf{{Owner}} & \textbf{{Guide (slide)}} & \textbf{{Backup slide}}\\\midrule\endhead
{qa}
\bottomrule\end{{longtable}}}}

\subsection*{{Backup slides}}
{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{1.2cm}}P{{1.0cm}}X@{{}}}}
\toprule\textbf{{Slide}} & \textbf{{Code}} & \textbf{{Content}}\\\midrule
{backups}
\bottomrule\end{{tabularx}}}}

\subsection*{{Every likely question in this guide}}
Each question links to the slide section that answers it.
{{\small\begin{{longtable}}{{@{{}}P{{11.4cm}}P{{0.9cm}}P{{1.6cm}}@{{}}}}
\toprule\textbf{{Question}} & \textbf{{Slide}} & \textbf{{Owner}}\\\midrule\endhead
{qindex}
\bottomrule\end{{longtable}}}}
\clearpage

\section{{Plain-language reference}}\label{{sec:terms}}
{{\small
\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{3.6cm}}X@{{}}}}
\toprule\textbf{{Term}} & \textbf{{Meaning in this project}}\\\midrule
Request (booking) & One Night Ride request, possibly with several passengers. Files call it a booking.\\
Lyft order & A separate order placed after a transfer decision (files: ``booking''). Placed 2~min after the decision (the ordering lag).\\
Curb arrival & A vehicle reaches the pickup location. Waiting time runs from the request to curb arrival.\\
Pickup & The rider boards. ``Reached within 15 min'' uses curb arrival, not boarding.\\
Cancellation & The rider gives up before a vehicle reaches the curb (also possible after a transfer, before the Lyft arrives).\\
No-show & The rider is absent when the vehicle arrives; the van waits 3~min.\\
Constructed night & One synthetic one-hour pilot night: 28 requests, 2 vans of 14 seats, 11 requests placed in an 18:20--18:30 burst.\\
Paired replay & The same night replayed under each rule with identical requests and hidden traits: 30 nights $\times$ 6 rules = 30 paired scenarios, not 180 independent nights.\\
Simulator / van optimizer / transfer rule & Advances time and reveals events / chooses among feasible candidate plans (a mixed-integer linear program, MILP) / decides whether an eligible request moves to Lyft.\\
Decision moment (epoch) & When the dispatcher re-plans: every 2~min, at each new request, at a cancellation or no-show while waiting for a van, and when a van comes on duty.\\
Postponement price & What the optimizer charges for leaving a request unserved this round; a large constant makes it serve as many requests as its candidates allow.\\
Verification / validation & The code implements the specified model / the model represents the real service. Only verification has been done.\\
Dominated (Pareto) & Another tested rule is at least as good on both objectives and strictly better on one. Nondominated is not recommended.\\
\bottomrule\end{{tabularx}}}}

\subsection*{{The six transfer rules (codes for files only)}}
{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{5.4cm}}XP{{1.4cm}}@{{}}}}
\toprule\textbf{{Rule}} & \textbf{{Moves a waiting request to Lyft when}} & \textbf{{Code}}\\\midrule
Vans only & never & R0\\
Wait ten / fifteen minutes & it has waited at least 10 / 15 minutes & R1(10) / R1(15)\\
Unassigned for ten minutes & it has been outside every van plan for 10 minutes in a row & R1u(10)\\
Predicted total wait exceeds fifteen minutes & predicted pickup clock time $-$ request clock time $>$ 15 min & R2(15)\\
Lyft arrives sooner & the predicted van pickup is later than now + 2 (lag) + 8 (typical delay) + 2 (margin) minutes & R3(2)\\
\bottomrule\end{{tabularx}}}}
Labels on the slides: \textbf{{evidence}} (OBSERVED, DERIVED, ASSUMED, DESIGNED, SIMULATED, ILLUSTRATIVE) and \textbf{{execution status}} (TESTED IN SIMULATION, PLANNED --- NOT YET RUN, PROPOSED --- NOT IMPLEMENTED). ``Tested'' never means validated against Hopkins.

\subsection*{{Key numbers}}
{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{6.2cm}}X@{{}}}}
\toprule
6~pm completed rides & 5,089 digitized (tooltip 5,098), a 30-day total; about 170 per evening\\
Requests per completed ride; per vehicle-hour & 2.087 (50,297 / 24,095); about 12.85 at 6~pm\\
Planned five-van evening (not run) & 64 / 50 / 54 = 168 requests\\
No-show & 4.7\% of all requests; 8.9\% per van arrival (conditional on the status mapping)\\
Reached within 15 min (30-night means) & vans only 48\%; waiting rules 50--51\%; predictive rules 73--75\%\\
Lyft orders per night & 0 / 5.9 / 3.1 / 0.2 / 9.3 / 10.5 (rules in the order above)\\
Lost after transfer & 95 of 196 under Wait ten minutes; about a third under the predictive rules\\
\bottomrule\end{{tabularx}}}}

\subsection*{{References you will see in the notes}}
The preparation notes keep some references to the team's repository for teammates who have access. You do not need them for Q\&A: use the methodology page references instead.
{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{4.0cm}}X@{{}}}}
\toprule\textbf{{Reference}} & \textbf{{What it is, and where to look in this pack}}\\\midrule
D-xx (for example D-49) & A numbered entry in the project decision log (repository). The methodology summarizes the decision history in Appendix~A (p.~47).\\
spec §N; model design §N & The scenario specification and the model-design document (repository). Their rules are restated in methodology §4 (simulator) and §5 (mathematics).\\
Technical review A, B, C & The v0.4 review that settled the patience interpretation (A), the reason for the pivot (B) and the leader--follower wording (C). Its conclusions are in the notes for slides 23, 5 and 25.\\
TransLoc notes §N & Team research notes on the vendor's published dispatch design (repository).\\
Phase 4 log; L1--L5 & The project's build log (repository); L1--L4 are the small designed evenings and L5 the two-van pilot (code key on slide 30).\\
File paths (data/\dots, outputs/\dots, src/\dots, .py, .md, .csv) & Repository files, for teammates with access only.\\
Slide source lines & Some deck footers cite ``methodology v1.5 §1a'' or ``§7b''; in the v1.6 PDF these are §1.4 (p.~8) and §7.8--7.9 (pp.~42--43).\\
\bottomrule\end{{tabularx}}}}
\clearpage

\section{{What every member must be able to explain}}\label{{sec:shared}}
\begin{{enumerate}}
{shared}
\end{{enumerate}}

\section{{Human verification activities}}\label{{sec:human}}
\begin{{prep}}[THE DISTINCTION]\normalsize {C.HUMAN_VERIFICATION}\end{{prep}}
Each presenter has one guided activity in their presenter brief (folder \texttt{{presenter\_briefs}}). Every record starts as \textbf{{Awaiting human completion}}. Reference answers produced with AI assistance do not count as a teammate's verification.

{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{3.2cm}}XP{{3.6cm}}@{{}}}}
\toprule\textbf{{Presenter}} & \textbf{{Activity}} & \textbf{{Status}}\\\midrule
""" + "\n".join(f"{esc(p[0])} & {C.ACTIVITIES[p[0]]['title']} ({C.ACTIVITIES[p[0]]['slides']}) & Awaiting human completion\\\\" for p in C.PRESENTERS) + rf"""
\bottomrule\end{{tabularx}}}}
\clearpage

\section{{Slide by slide}}\label{{sec:slides}}
Each slide below has the exact narration (blue) and the preparation material (grey). At a handoff, the blue box ends with the handoff sentence.
\clearpage
""" + "\n".join(slide_section(n) for n in range(1, 29))
    return doc("Team Presentation Guide", body, "Team Presentation Guide · v1.0")


# ---------------------------------------------------------------- presenter briefs
def brief(p, guide_pages):
    name, stem, a, b, resp, role = p
    act = C.ACTIVITIES[name]
    gl = lambda n: r"\href[page=" + str(guide_pages.get(n, 1)) + "]{../" + C.GUIDE_FILE + "}{guide, slide " + str(n) + "} (guide p.~" + str(guide_pages.get(n, 1)) + ")"
    reading = "\n".join(rf"\item Slide {n} · {inline(SLIDES[n]['title'])}: {gl(n)}; methodology {meth_ref(n, '../')}" for n in range(a, b + 1))
    narr = "\n".join(r"\needspace{0.45\textheight}\subsection*{Slide " + str(n) + " · " + inline(SLIDES[n]["title"]) + r"}" + "\n" +
                     r"{\sffamily\small\color{muted}about " + str(SLIDES[n]["secs"]) + r" s · " + deck_link(n, "../", "open slide") + "}\n" +
                     spoken_block(n) for n in range(a, b + 1))
    concepts = {
        "Irfan Setiadi": ["the service and one request's journey (request, wait, curb arrival, boarding, drop-off; cancellation and no-show)",
                          "why a Lyft order has a price (an extra trip Hopkins pays for; cost unknown)",
                          "what the original proposal planned and what changed (trip records never arrived)",
                          "the four corrected proposal numbers, especially the 30-day total",
                          "why holding one dispatcher fixed is a scope choice, not a claim about synthetic data"],
        "Miles Zhou": ["observed vs derived vs assumed vs designed", "the workload chain and its two stated assumptions; 168 is planned, not run",
                       "the two-van pilot: 28 requests, the 18:20--18:30 burst, 30 nights $\\times$ 6 rules",
                       "why place totals do not identify trips; why one average does not fix a distribution",
                       "``Canceled'' as an observation, an assumed mapping and hidden patience; the two no-show denominators"],
        "Youzhi Zhang": ["the three components and what the dispatcher can and cannot see", "the eight-step decision cycle; one rule pass and at most one re-plan",
                         "the objective blocks and what `optimal' means (best among generated candidates at that moment)",
                         "the six rules' exact definitions and eligibility", "the worked transfer; the postponement-price flaw and its partial fix",
                         "paired replay; verification vs validation, and that AI wrote the code and checks"],
        "Vignesh Rajesh Babu": ["the main result and that the 15-minute measure favours early transfer", "why a transfer does not end waiting, and the corrected patience interpretation",
                                "dominance, why vans only stays nondominated, and why nondominated is not recommended",
                                "leader--follower as a proposed extension: what a finite search can and cannot show",
                                "which assumptions could change the answer, the order of next experiments, and the conditional conclusion"],
    }[name]
    qa = "\n".join(rf"\item {inline(top)} --- guide slides " + ", ".join(gl(s) for s in sl) +
                   ("; backups " + ", ".join(deck_link(bk, "../", str(bk)) for bk in bks) if bks else "")
                   for top, own, sl, bks in C.QA if own == name)
    opening = (r"You open the talk with slide 1's narration." if a == 1 else
               r"You start immediately after the handoff sentence: ``" + inline(C.HANDOFFS[a - 1][2]) + r"'' Begin with slide " + str(a) + "'s first sentence; do not re-introduce yourself.")
    closing = (r"You end the talk with ``Thank you; we welcome your questions.''" if b == 28 else
               r"Your handoff sentence (end of slide " + str(b) + r"): ``" + inline(C.HANDOFFS[b][2]) + "''")
    designer = ""
    if name == "Irfan Setiadi":
        designer = (r"\section{Design lead: instructions for restyling}" + "\n" +
                    r"The editable deck is in the folder \texttt{designer\_Irfan\_Setiadi} (file \texttt{BlueJay\_Midterm\_v0.4.pptx}). The PDFs in this pack remain the reference for content." +
                    "\n\\begin{itemize}\n" + "\n".join(r"\item " + x for x in C.DESIGNER_NOTES) + "\n\\end{itemize}\n")
    proc = "\n".join(r"\item " + x for x in act["procedure"])
    check = "\n".join(r"\item[$\square$] " + x for x in act["checklist"])
    body = rf"""
{{\sffamily\small\color{{muted}} Blue Jay Night Ride · Team FourSight · Midterm presenter brief\par}}
{{\sffamily\fontsize{{22}}{{27}}\selectfont\bfseries\color{{heading}} {esc(name)}\par}}
{{\sffamily\large\color{{heading}} {esc(role)} · slides {a}--{b} · about {mmss(section_secs(p))} of narration\par}}
\begin{{prep}}[THE PROJECT STORY]\normalsize {C.STORY}\end{{prep}}
\tableofcontents
\section{{Your section}}
\textbf{{Slides {a}--{b}:}} {inline(SLIDES[a]['title'])} → {inline(SLIDES[b]['title'])}.\par
\textbf{{Purpose:}} {esc(resp)}.\par
{opening}\par
{closing}

\section{{Essential preparation reading}}
Read these in the shared guide (\texttt{{{esc(C.GUIDE_FILE)}}}, one folder up) and the methodology PDF:
\begin{{itemize}}
{reading}
\item Everyone: guide sections ``What every member must be able to explain'' and ``Quick Q\&A navigation''.
\end{{itemize}}

\section{{Concepts you must explain confidently}}
\begin{{itemize}}
""" + "\n".join(r"\item " + c for c in concepts) + rf"""
\end{{itemize}}

\section{{Questions you lead on}}
Answer these first; route anything else to its owner (guide, Quick Q\&A navigation).
\begin{{itemize}}
{qa}
\end{{itemize}}
\clearpage
\section{{Your narration (exact words)}}
{narr}
\clearpage
\section{{Manual verification activity: {act['title']}}}
\begin{{prep}}[WHAT HUMAN VERIFICATION MEANS]\normalsize {C.HUMAN_VERIFICATION}\end{{prep}}
{C.ACTIVITY_INTRO}

\textbf{{Related slides:}} {act['slides']}.\quad \textbf{{Goal:}} {act['goal']}

\subsection*{{Source inputs}}
{act['inputs']}

\subsection*{{Procedure}}
\begin{{enumerate}}
{proc}
\end{{enumerate}}
\clearpage
\subsection*{{Worksheet}}
\begin{{work}}
\textbf{{Step-by-step working}} (use the lines, or attach your own sheet)
\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]\blank[1.6]
\par\medskip\textbf{{My result}}\blank[1.6]\blank[1.6]\blank[1.6]
\end{{work}}

\subsection*{{Record}}
{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{4.4cm}}X@{{}}}}
\toprule
Status & \textbf{{Awaiting human completion}}\\\midrule
Name & \\[1.2em]\midrule
Date completed & \\[1.2em]\midrule
My result & \\[2.4em]\midrule
Matches the reference? (yes / partly / no) & \\[1.2em]\midrule
Discrepancy, and what I did about it & \\[2.4em]\midrule
What remains unverified & \\[2.4em]\\
\bottomrule
\end{{tabularx}}}}
\clearpage
\subsection*{{Reference answer}}
\begin{{refans}}
{act['reference']}
\end{{refans}}
\subsection*{{Comparison checklist}}
\begin{{itemize}}[label={{}},leftmargin=1.6em]
{check}
\end{{itemize}}
Record any disagreement in the table above. Do not change your own working to match the reference.

\section{{Rehearsal and readiness checklist}}
\begin{{itemize}}[label={{}},leftmargin=1.6em]
\item[$\square$] Read my slides' preparation notes in the shared guide.
\item[$\square$] Read my slides in the final deck (\texttt{{{esc(C.DECK_FILE)}}}) and know which backup slides I may need.
\item[$\square$] Said my narration aloud with a stopwatch; my section took \underline{{\hspace{{2cm}}}} (estimate {mmss(section_secs(p))}).
\item[$\square$] Practised my opening and handoff sentences with the neighbouring presenter.
\item[$\square$] Can explain every concept listed above without the slides.
\item[$\square$] Completed my verification activity and filled in the record (status changed from ``Awaiting human completion'' only by me).
\item[$\square$] Took part in one timed full-team rehearsal (total time: \underline{{\hspace{{2cm}}}}).
\end{{itemize}}
""" + designer
    return doc(f"Presenter brief: {name}", body, f"Presenter brief · {name} · v1.0")


# ---------------------------------------------------------------- start here
def start_here():
    total = sum(section_secs(p) for p in C.PRESENTERS)
    rows = "\n".join(f"{esc(p[0])} & {esc(p[5])} & {p[2]}--{p[3]} & {inline(SLIDES[p[2]]['title'])} → {inline(SLIDES[p[3]]['title'])} & {mmss(section_secs(p))}\\\\"
                     for p in C.PRESENTERS)
    files = [(C.GUIDE_FILE, "Shared reference for everyone, also during the presentation: assignments, handoffs, Q\\&A navigation, terms, and every slide's narration and preparation notes."),
             (C.DECK_FILE, "The finalized slides as a PDF: 28 main slides, the backup divider on slide 29, backups on 30--38. The slide count and order are frozen. Some slide footers cite repository files and ``methodology v1.5'' section labels; use the guide's page references to the v1.6 PDF instead."),
             (C.METH_FILE, f"The scenario methodology {C.METH_VERSION}: the scientific source. Use the page references in the guide; you do not need to read it all."),
             ("presenter\\_briefs/", "One brief per presenter: your narration, handoffs, concepts, questions you lead on, your verification activity and a readiness checklist."),
             ("designer\\_Irfan\\_Setiadi/", "The editable PowerPoint for the design lead. Content is frozen; restyling must not change meaning.")]
    fl = "\n".join(r"\item " + (r"\href{" + f + "}{" + esc(f) + "}" if f.endswith(".pdf") else r"\texttt{" + f + "}") + ": " + d for f, d in files)
    body = rf"""
{{\sffamily\small\color{{muted}} Blue Jay Night Ride · Team FourSight · EN.553.602 · Midterm preparation pack v1.0 · 23 October 2026\par}}
{{\sffamily\fontsize{{26}}{{31}}\selectfont\bfseries\color{{heading}} Start here\par}}
\begin{{prep}}[THE PROJECT STORY]\normalsize {C.STORY}\end{{prep}}

\section*{{Team, roles and slides}}
{{\small\begin{{tabularx}}{{\linewidth}}{{@{{}}P{{2.7cm}}P{{2.6cm}}P{{1.2cm}}XP{{1.0cm}}@{{}}}}
\toprule\textbf{{Name}} & \textbf{{Role}} & \textbf{{Slides}} & \textbf{{From → to}} & \textbf{{Time}}\\\midrule
{rows}
\bottomrule\end{{tabularx}}}}
Estimated total: about {mmss(total)} of narration with pauses, plus about 45~s of handoffs: \textbf{{about 27 minutes}}. Reading numbers slowly can add about a minute; dropping the sentences marked [optional] saves about 1.5 minutes. \textbf{{Timing remains an estimate until the team has rehearsed}}; the limit is 30 minutes.

\section*{{Key dates (fill in)}}
Presentation: \underline{{\hspace{{3.5cm}}}}\quad Full timed rehearsal: \underline{{\hspace{{3.5cm}}}}\quad Verification records due: \underline{{\hspace{{3.5cm}}}}

\section*{{Open team action}}
\textbf{{Youzhi Zhang}} (verification section), before the presentation: confirm which designed-evening answer keys, if any, a team member re-derived by hand, so that slide 21 is stated honestly. Until then, say that the keys and checks were produced with AI assistance and checked by programs.

\section*{{What is in this folder}}
\begin{{itemize}}
{fl}
\end{{itemize}}

\section*{{Study order}}
\begin{{enumerate}}
\item Read the story above and skim the deck ({esc(C.DECK_FILE)}) once from start to finish.
\item Read the guide's ``Presenters'', ``Plain-language reference'' and ``What every member must be able to explain''.
\item Open your presenter brief. Read your slides' preparation notes in the guide (linked from your brief).
\item Do your verification activity: calculate first, then compare with the reference answer.
\item Rehearse your narration aloud with a stopwatch; then rehearse handoffs with your neighbours; then one timed full run.
\end{{enumerate}}

\section*{{What everyone must understand, and what your section requires}}
\textbf{{Everyone}} must be able to explain the seven points in the guide's section ``What every member must be able to explain'': why the data could not reconstruct journeys; observed vs derived vs assumed; why one dispatcher is held fixed; why a transfer does not end waiting; verification vs validation; why more service with more Lyft is a trade-off; and why the findings do not establish real Hopkins effects.

\textbf{{Your section}} additionally requires the concepts and questions listed in your brief. Route other questions to their owner (guide, ``Quick Q\&A navigation'').

\section*{{Recording your verification and rehearsal}}
\begin{{prep}}[HUMAN VERIFICATION]\normalsize {C.HUMAN_VERIFICATION}\end{{prep}}
Each brief contains one guided activity with a worksheet, a separately placed reference answer, a comparison checklist and a record table. Every record starts as \textbf{{Awaiting human completion}}. Fill in the record yourself (on paper or in a copy of the PDF): your name, the date, your result, any discrepancy, and what remains unverified. Then tick the readiness checklist at the end of your brief, including your own measured section time.
"""
    return doc("Start here", body, "Start here · Team share v1.0")


# ---------------------------------------------------------------- build
def compile_tex(name, tex, outdir, passes=3):
    BUILD.mkdir(parents=True, exist_ok=True)
    src = BUILD / f"{name}.tex"
    src.write_text(tex)
    for _ in range(passes):
        r = subprocess.run([XELATEX, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={BUILD}", str(src)],
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-3000:])
            sys.exit(f"LaTeX failed for {name}")
    log = (BUILD / f"{name}.log").read_text(errors="ignore")
    missing = sorted(set(re.findall(r"Missing character: There is no (.) ", log)))
    over = len(re.findall(r"Overfull \\hbox", log))
    print(f"{name}: overfull={over} missing_glyphs={missing}")
    outdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(BUILD / f"{name}.pdf", outdir / f"{name}.pdf")
    return BUILD / f"{name}.aux"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    aux = compile_tex("01_Team_Presentation_Guide", guide(), OUT)
    pages = {int(m.group(1)): int(m.group(2)) for m in re.finditer(r"\\newlabel\{slide:(\d+)\}\{\{[^}]*\}\{(\d+)\}", aux.read_text())}
    for p in C.PRESENTERS:
        compile_tex(p[1], brief(p, pages), OUT / "presenter_briefs", passes=2)
    compile_tex("00_Start_Here", start_here(), OUT, passes=2)
    shutil.copy(V04 / "BlueJay_Midterm_v0.4_preview.pdf", OUT / C.DECK_FILE)
    shutil.copy(METH_PDF, OUT / C.METH_FILE)
    (OUT / "designer_Irfan_Setiadi").mkdir(exist_ok=True)
    shutil.copy(V04 / "BlueJay_Midterm_v0.4.pptx", OUT / "designer_Irfan_Setiadi" / "BlueJay_Midterm_v0.4.pptx")
    print("slide pages in guide:", pages)


if __name__ == "__main__":
    main()
