"""Build the plain-language project update PDF (17 Nov 2026).

Run from the repo root:
    .venv/bin/python docs/presentations/status/build_status_update.py

Every number is copied from a dated research note:
- m5b_preview_2026-11-16.md (C vs G results)
- m5b_run_record_2026-11.md (compute, r26)
- m5c_preregistration_2026-11.md (C-F probe compute, decision table)
No M5c rider outcome is used: the M5c runs are still in progress and blind.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
OUT = HERE / "BlueJay_Project_Update_2026-11-17.pdf"

NAVY = "#002D72"   # Hopkins blue
SKY = "#4A90C8"
GREY = "#6B7280"
LIGHT = "#EEF3F9"
GREEN = "#2E7D4F"
AMBER = "#B7791F"

# ---------------------------------------------------------------- figures

def fig_gap():
    """C - G gap by load per van, with 95% intervals and the 2-pp band."""
    rows = [  # label, estimate, lo, hi  (pp; negative = C reaches more riders)
        ("6 vans, normal demand", -4.17, -5.68, -2.71),
        ("5 vans, normal demand", -6.35, -8.65, -4.17),
        ("5 vans, high demand", -12.47, -14.78, -10.10),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 2.5), dpi=220)
    ax.axvspan(-2, 2, color="#E5E7EB", zorder=0)
    ax.text(0, 2.65, "practically\nequal (±2)", ha="center", va="center",
            fontsize=7.5, color=GREY)
    ax.axvline(0, color=GREY, lw=0.8)
    for i, (lab, est, lo, hi) in enumerate(rows):
        y = i
        ax.hlines(y, -lo, -hi, color=NAVY, lw=2.2)
        ax.plot(-est, y, "o", color=NAVY, ms=7)
        ax.text(-lo + 0.4, y, "%.1f points" % round(abs(est) + 1e-6, 1), va="center",
                fontsize=8.5, color=NAVY, fontweight="bold")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.5)
    ax.set_ylim(-0.5, 3.0)
    ax.set_xlim(-3, 19)
    ax.set_xlabel("Gain from the optimizer C over greedy G:\n"
                  "extra share of requests reached within 20 min (percentage points)",
                  fontsize=8)
    ax.tick_params(axis="x", labelsize=8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    p = FIG / "gap_by_load.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def fig_compute():
    """Wall time per high-demand night: C vs C-F (compute only)."""
    nights = ["night 1", "night 2", "night 3", "night 4"]
    c = [76, 250, 103, 1396]
    cf = [4.4, 15.5, 10.6, 25.6]
    fig, ax = plt.subplots(figsize=(6.6, 2.4), dpi=220)
    x = range(len(nights))
    w = 0.38
    ax.bar([i - w / 2 for i in x], c, w, color=GREY, label="C (free drop-off order)")
    ax.bar([i + w / 2 for i in x], cf, w, color=SKY, label="C-F (aboard riders' order fixed)")
    ax.set_yscale("log")
    ax.set_yticks([5, 15, 60, 240, 1440])
    ax.set_yticklabels(["5 min", "15 min", "1 h", "4 h", "24 h"], fontsize=8)
    ax.axhline(15, color=AMBER, lw=1, ls="--", label="15-min speed gate")
    for i in x:
        ax.text(i - w / 2, c[i] * 1.12, f"{c[i]/60:.1f} h" if c[i] >= 60 else f"{c[i]} min",
                ha="center", fontsize=7.5, color=GREY)
        ax.text(i + w / 2, cf[i] * 1.12, f"{cf[i]:.0f} min", ha="center",
                fontsize=7.5, color=SKY)
    ax.set_xticks(list(x))
    ax.set_xticklabels(nights, fontsize=8.5)
    ax.set_ylabel("Computer time per night\n(first hour of service)", fontsize=8)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left")
    ax.set_ylim(2, 4000)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    p = FIG / "compute_c_vs_cf.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ---------------------------------------------------------------- styles

H1 = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=19, leading=23,
                    textColor=colors.HexColor(NAVY), spaceAfter=2)
SUB = ParagraphStyle("SUB", fontName="Helvetica", fontSize=9.5, leading=12,
                     textColor=colors.HexColor(GREY), spaceAfter=10)
H2 = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=13, leading=16,
                    textColor=colors.HexColor(NAVY), spaceBefore=8, spaceAfter=5)
BODY = ParagraphStyle("BODY", fontName="Helvetica", fontSize=10, leading=13.5,
                      alignment=TA_LEFT, spaceAfter=5)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8.5, leading=11,
                       textColor=colors.HexColor(GREY))
BIG = ParagraphStyle("BIG", parent=BODY, fontSize=12, leading=16,
                     textColor=colors.HexColor(NAVY))
CELL = ParagraphStyle("CELL", parent=BODY, fontSize=9, leading=11.5, spaceAfter=0)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold")


def box(flowables, bg=LIGHT, border=NAVY):
    t = Table([[flowables]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
        ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(border)),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def grid(rows, widths, header=True):
    data = [[Paragraph(c, CELLB if (header and r == 0) else CELL) for c in row]
            for r, row in enumerate(rows)]
    t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(LIGHT)),
                  ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor(NAVY))]
    t.setStyle(TableStyle(style))
    return t


def img(path, width_in):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    return Image(str(path), width=width_in * inch, height=width_in * inch * h / w)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor(GREY))
    canvas.drawString(0.75 * inch, 0.5 * inch,
                      "Blue Jay Night Ride optimizer · project update · 17 Nov 2026 · "
                      "all nights are synthetic, built from April 2026 aggregates")
    canvas.drawRightString(7.75 * inch, 0.5 * inch, f"{doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------- content

def build():
    FIG.mkdir(exist_ok=True)
    gap = fig_gap()
    comp = fig_compute()
    s = []

    # ---- page 1: the one-page answer
    s += [Paragraph("Blue Jay Night Ride: where the project stands", H1),
          Paragraph("Project update, 17 November 2026 · for the team and Prof. Kearsley", SUB)]
    s.append(Paragraph(
        "<b>The question.</b> Using the same vans, can a dispatcher that re-plans "
        "<i>all</i> open requests together reach more riders within 20 minutes than one "
        "that slots each new request in and never revisits it?", BODY))
    s.append(Spacer(1, 4))
    s.append(box([Paragraph(
        "<b>Answer so far: yes, and the busier the vans, the bigger the gain.</b> "
        "On the first hour of service with 5 vans, the optimizer left "
        "<b>22.3%</b> of requests unreached within 20 minutes, against <b>28.7%</b> for "
        "the greedy baseline: <b>6.4 points better</b> (95% interval 4.2 to 8.7), "
        "over 30 paired nights.", BIG)]))
    s.append(Spacer(1, 8))
    s.append(img(gap, 6.9))
    s.append(Paragraph(
        "Each dot is the average gain over 30 nights (26 at high demand); the line is its "
        "95% interval. All three sit well outside the grey band, so none is a tie.", SMALL))
    s.append(Spacer(1, 6))
    s.append(Paragraph("Status at a glance", H2))
    s.append(grid([
        ["Done", "Running now", "Next"],
        ["Synthetic nights built from the April dashboard; simulator and both "
         "dispatchers built and tested; main comparison C vs G (300 simulated nights).",
         "A test of a faster version of the optimizer (C-F) on 60 nights. "
         "21 of 60 finished; rules fixed before any result.",
         "Team decisions on the dispatcher; result figure; a full evening (6 pm to 9 pm); "
         "preview to Prof. Kearsley before 26 Nov; final on 1 Dec."],
    ], [2.33, 2.33, 2.34]))
    s.append(Spacer(1, 6))
    s.append(Paragraph(
        "<b>Names used here.</b> <b>C</b>: our optimizer, which re-plans every van's route "
        "exactly at each event. <b>G</b>: greedy insertion, which never moves a request once "
        "placed. <b>C-F</b>: C with the drop-off order of riders already aboard kept fixed. "
        "<b>Points</b>: percentage points.", SMALL))
    s.append(PageBreak())

    # ---- page 2: how we got here
    s.append(Paragraph("How we got here", H2))
    s.append(Paragraph(
        "We have no trip-level records, only the April 2026 TransLoc dashboard (44,374 riders). "
        "So we followed the route Prof. Kearsley suggested: pull sufficient statistics out of "
        "the aggregates, separate the operating regimes, and build synthetic nights consistent "
        "with them. Every dispatcher then plays the same nights, so differences come from the "
        "dispatcher, not from luck.", BODY))
    s.append(grid([
        ["Stage", "What it means", "Status"],
        ["1. Digitize", "Read the April dashboard into numbers and check them against each other",
         "Done (Sep)"],
        ["2. Analyze", "Find the patterns: supply-limited service, cancellations rising with "
         "wait, a quarter of riders moved to Lyft", "Done (Sep to Oct)"],
        ["3. Build nights", "Generate realistic request streams on real Baltimore roads; "
         "freeze them with fingerprints", "Done (Oct to 10 Nov)"],
        ["4. Simulate and compare", "A referee engine runs each dispatcher on the same nights",
         "In progress"],
        ["5. Recommend", "Which Lyft-transfer rules help riders, and at what cost",
         "After the preview"],
    ], [1.5, 4.2, 1.3]))
    s.append(Spacer(1, 8))
    s.append(Paragraph("Simulator milestones", H2))
    s.append(grid([
        ["Milestone", "Content", "Status"],
        ["M0 to M3", "Engine, optimizer, Lyft rules, 30-night rehearsal with intervals",
         "Done (22 Oct to 10 Nov)"],
        ["M4", "Build the 60 study nights (normal and high demand)", "Done (10 Nov)"],
        ["M5a", "Speed check of C, without looking at any rider result", "Done (10 Nov)"],
        ["M5b", "C vs G, the main comparison (300 runs)", "Done (15 Nov); result on page 1"],
        ["M5c", "Does the faster C-F lose riders? (60 runs)", "Running (17 Nov)"],
        ["M6", "A full evening, 168 requests, 5 vans", "Next"],
        ["M7", "The Lyft-transfer rule grid (the core research question)", "After 26 Nov"],
    ], [1.1, 4.4, 1.5]))
    s.append(PageBreak())

    # ---- page 3: what we learned about speed
    s.append(Paragraph("The one problem we hit: speed on busy nights", H2))
    s.append(Paragraph(
        "C is exact: at every event it reconsiders the order of every stop, including the "
        "drop-offs of riders already in the van. That is what makes it good, and also what "
        "makes it slow when vans are full. A typical re-plan took 0.2 seconds with 3 riders "
        "aboard and over 6 minutes with 7. On one high-demand night, a single simulated hour "
        "took 23 hours of computer time. That is fine for a one-hour test, but not for whole "
        "evenings.", BODY))
    s.append(Paragraph(
        "<b>The fix we are testing (C-F):</b> keep the drop-off order of riders already aboard "
        "fixed, and still place every new pickup and drop-off in the best position. On four "
        "busy nights it was 16 to 55 times faster.", BODY))
    s.append(img(comp, 6.9))
    s.append(Paragraph("Computer time only; no rider result from C-F has been looked at.", SMALL))
    s.append(Spacer(1, 4))
    s.append(Paragraph(
        "<b>But faster is not enough.</b> Before we switch, we test whether C-F reaches fewer "
        "riders than C. The pass mark was written down and frozen earlier today, before the "
        "runs started: C-F must not be worse than C by 2 points or more. What each outcome "
        "leads to was also fixed in advance:", BODY))
    s.append(grid([
        ["Speed (median busy night)", "Rider result vs C", "What we would propose to the team"],
        ["15 min or less", "Not worse by 2 points", "Use C-F for busy nights, and say openly "
         "that C was changed to handle high demand, with this test as the evidence"],
        ["15 min or less", "Unclear, or worse", "Keep C. Busy full evenings stay a stated "
         "computing limit"],
        ["Over 15 min", "Any", "Keep C. C-F does not solve the problem"],
    ], [1.7, 1.6, 3.7]))
    s.append(PageBreak())

    # ---- page 4: honest + next + limits
    s.append(Paragraph("How we keep the result honest", H2))
    for t in [
        "<b>Rules before results.</b> The measure, the 2-point margin, the statistics and the "
        "stopping rule were written down, frozen and committed to git before the first run. "
        "Git timestamps prove the order.",
        "<b>Speed measured blind.</b> We timed C before looking at any rider result, so no "
        "setting could be tuned to make it win.",
        "<b>Same nights for both.</b> C and G face identical requests and identical "
        "no-shows; we compare them night by night.",
        "<b>Stop on any failure.</b> One run failed a safety check. We paused, found the fault "
        "was in the check itself, kept the frozen rule (26 nights instead of 30) and reported "
        "all 30 separately. The answer did not change (12.5 vs 11.9 points).",
        "<b>Claim the difference, not the levels.</b> Rider patience, no-show rate and Lyft "
        "delay are assumptions, so \"22% unreached\" is not a Hopkins fact. The gap between "
        "dispatchers is the claim.",
    ]:
        s.append(Paragraph("• " + t, BODY))
    s.append(Paragraph("What comes next", H2))
    s.append(grid([
        ["When", "Step"],
        ["17 to 18 Nov", "C-F test finishes; result read against the frozen rules"],
        ["This week", "Team decides which dispatcher to hold fixed (D-51) and whether to "
         "adopt C-F (D-63); final result figure"],
        ["Before M6", "Fix the safety check that misfired, under a new code fingerprint"],
        ["By 25 Nov", "Full-evening demonstration if time allows; preview package to "
         "Prof. Kearsley"],
        ["1 Dec", "Final presentation"],
        ["After 26 Nov", "Lyft-transfer rule comparison on the fixed dispatcher"],
    ], [1.3, 5.7]))
    s.append(Paragraph("What these results do not show yet", H2))
    for t in [
        "Whole evenings: everything so far is the 6 pm to 7 pm peak.",
        "Real nights: the nights are synthetic, consistent with April's aggregates.",
        "TransLoc: the real dispatcher also re-plans, so greedy G is a baseline, not the "
        "status quo.",
        "Lyft rules: the study's main question comes after the dispatcher is settled.",
    ]:
        s.append(Paragraph("• " + t, BODY))

    doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch,
                            rightMargin=0.75 * inch, topMargin=0.7 * inch,
                            bottomMargin=0.75 * inch,
                            title="Blue Jay Night Ride: project update (17 Nov 2026)",
                            author="Blue Jay Night Ride project team")
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    build()
