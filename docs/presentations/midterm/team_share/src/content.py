"""Team-pack content that is not already in the v0.4 script and handbook.

Everything here is LaTeX (XeLaTeX). The slide narration, transitions, context and preparation notes are read from
docs/presentations/midterm/v0.4/speaking_script.md and slide_explanations.md by build_pack.py, so the shared guide
and the four presenter briefs always use the same words.
"""

METH_VERSION = "v1.6"
METH_FILE = "03_Scenario_Methodology_v1.6.pdf"
GUIDE_FILE = "01_Team_Presentation_Guide.pdf"
DECK_FILE = "02_Final_Presentation.pdf"

STORY = (r"We wanted to study dispatch decisions. April's data described aggregate patterns rather than individual "
         r"journeys, so we built plausible evenings from evidence and explicit assumptions. We checked the "
         r"implementation, replayed identical evenings under different transfer rules, and found a conditional "
         r"trade-off between timely service and Lyft use. Our next work tests how robust those findings are.")

# name, file stem, first slide, last slide, responsibility, role note
PRESENTERS = [
    ("Irfan Setiadi", "Irfan_Setiadi", 1, 5,
     "Introduction, service context, proposal recap and refined research question",
     "Opening presenter and design lead"),
    ("Miles Zhou", "Miles_Zhou", 6, 13,
     "Aggregate evidence, workload, scenario construction and assumptions", "Presenter"),
    ("Youzhi Zhang", "Youzhi_Zhang", 14, 21,
     "Architecture, decision cycle, mathematics, transfer rules, worked example, postponement issue and verification",
     "Presenter"),
    ("Vignesh Rajesh Babu", "Vignesh_Rajesh_Babu", 22, 28,
     "Findings, transfer outcomes, Pareto trade-offs, leader--follower extension, limitations, next steps and conclusion",
     "Presenter"),
]

# Handoff sentences replace the spoken transition on the last slide of each section (the script's own transition is
# kept as the alternative wording inside the guide's notes).
HANDOFFS = {
    5: ("Irfan Setiadi", "Miles Zhou",
        "That gives us the question. Miles will now explain how April's aggregate data became the ingredients of our scenarios."),
    13: ("Miles Zhou", "Youzhi Zhang",
         "Those inputs define the constructed evening. Youzhi will explain how the model makes decisions as that evening unfolds."),
    21: ("Youzhi Zhang", "Vignesh Rajesh Babu",
         "We then replayed the same evenings under different transfer rules. Vignesh will explain what changed, what it means and what remains uncertain."),
}

# Methodology PDF references per slide: (section, title, printed page). Physical page = printed page + 1.
METH = {
    1: [("1.1", "The question", 6)],
    2: [("1.3", "System boundaries", 6), ("4.6", "Transfers and the Lyft service", 22)],
    3: [("1.4", "From the September proposal to the current study", 8)],
    4: [("1.4", "From the September proposal to the current study", 8), ("3.1", "Volume: how many requests", 12)],
    5: [("1.4", "From the September proposal to the current study", 8), ("5.6", "The dispatchers and the held-fixed choice", 31)],
    6: [("2.1", "What the dashboard gives", 10), ("2.2", "Why aggregates cannot pin down one scenario", 11)],
    7: [("3.1", "Volume: how many requests", 12)],
    8: [("7.7", "M3: the L5 pilot and the 30-night batch", 40), ("4.12", "Designed checks: the level ladder", 25)],
    9: [("3.3", "Geography", 14), ("3.4", "Origin--destination pairing", 15)],
    10: [("3.5", "Parties: how many riders per booking", 15)],
    11: [("3.7", "Patience: when a waiting rider gives up", 16)],
    12: [("3.8", "No-shows: who is at the curb", 17)],
    13: [("3.10", "Patterns, seeds and pairing", 19), ("1.2", "Three things kept apart", 6)],
    14: [("1.2", "Three things kept apart", 6), ("Fig. 1", "The system in one picture", 7), ("4", "The simulator contract in plain language", 19)],
    15: [("4.3", "Same-second events", 21), ("4.4", "Epochs: when the dispatcher re-plans", 21), ("4.5", "The Lyft rule pass", 21)],
    16: [("5.2", "What a ``good'' plan means", 26), ("5.3", "The route-selection model", 28), ("5.4", "Worked example", 29), ("5.5", "What ``optimal'' means here", 31)],
    17: [("4.5", "The Lyft rule pass", 21), ("6.2", "The transfer path", 34)],
    18: [("4.6", "Transfers and the Lyft service", 22), ("6.2", "The transfer path", 34)],
    19: [("7.4", "A property of the objective that M1 exposed", 37), ("7.5", "The pending-price decision experiment", 37)],
    20: [("3.10", "Patterns, seeds and pairing", 19), ("7.7", "M3: the L5 pilot and the 30-night batch", 40)],
    21: [("7.2", "What was verified", 36), ("7.7", "M3 verification", 40)],
    22: [("7.7", "M3: the L5 pilot (mechanism 5: the 15-minute measure)", 41)],
    23: [("7.7", "M3: the L5 pilot (mechanism 1 and its interpretation)", 41), ("3.9", "Lyft: what happens after a transfer", 18)],
    24: [("7.8", "Reading the results as trade-offs", 42)],
    25: [("7.9", "A leader--follower reading", 43)],
    26: [("7.11", "Limitations to keep in view", 44), ("2.3", "Calibration keeps a set, not a point", 11)],
    27: [("7.12", "Next milestone and how the work grows", 45), ("7.13", "Open decisions for the team", 46)],
    28: [("7.10", "Status by item", 44)],
}

BACKUPS = [
    (30, "B1", "Code key: plain rule names and file codes"), (31, "B2", "The route-selection MILP and the M bound"),
    (32, "B3", "Event order, triggers and commitments"), (33, "B4", "Where each input comes from"),
    (34, "B5", "Three postponement prices compared"), (35, "B6", "All metrics by rule, 30 nights"),
    (36, "B7", "Trade-off night by night"), (37, "B8", "Numerical diagnostics"), (38, "B9", "Corrected proposal claims"),
]

# Q&A ownership: topic, owner, guide slides, backup slides (deck page numbers)
QA = [
    ("Why this project; what the service is", "Irfan Setiadi", [1, 2], []),
    ("The original proposal and what changed", "Irfan Setiadi", [3, 4], [38]),
    ("Why hold one dispatcher fixed (the pivot)", "Irfan Setiadi", [5], [38]),
    ("What April's data do and do not contain", "Miles Zhou", [6], [33]),
    ("Where 168 requests and 12.85 per vehicle come from", "Miles Zhou", [7], [33]),
    ("The two-van pilot and the burst", "Miles Zhou", [8], [33, 35]),
    ("Trip pairing, party sizes, patience, no-shows", "Miles Zhou", [9, 10, 11, 12], [33]),
    ("What is observed, derived or assumed", "Miles Zhou", [6, 13], [33]),
    ("Simulator, optimizer and rule: who does what", "Youzhi Zhang", [14, 15], [32]),
    ("The objective, `optimal', candidate restriction", "Youzhi Zhang", [16], [31, 37]),
    ("Exact rule definitions and eligibility", "Youzhi Zhang", [17], [30]),
    ("The worked transfer timeline", "Youzhi Zhang", [18], []),
    ("The postponement-price flaw and fix", "Youzhi Zhang", [19], [34]),
    ("Paired replay; 30 nights, not 180", "Youzhi Zhang", [20], [36]),
    ("Verification vs validation; AI-written code", "Youzhi Zhang", [21], [37]),
    ("Results and the 15-minute measure", "Vignesh Rajesh Babu", [22], [35]),
    ("Losses after transfer; patience interpretation", "Vignesh Rajesh Babu", [23], [35]),
    ("Pareto dominance and its limits", "Vignesh Rajesh Babu", [24], [36]),
    ("Leader--follower / bilevel extension", "Vignesh Rajesh Babu", [25], [31]),
    ("Limits, next experiments, the conditional answer", "Vignesh Rajesh Babu", [26, 27, 28], [37]),
]

SHARED = [
    ("Why the data could not reconstruct individual journeys",
     r"April's dashboards give totals and shares (statuses, rides by hour, place counts, percentiles); no record links one rider's request time, place, wait and outcome. So every evening is constructed. (Slides 6, 9.)"),
    ("What is observed, derived and assumed",
     r"Observed: read from the dashboards (for example 50,297 requests). Derived: computed from observed numbers with a stated formula (12.85 requests per vehicle-hour, 8.9\% no-show per arrival). Assumed: our choices (trip pairing, patience, Lyft delay). Designed: experiment settings we chose (two vans, the burst). (Slides 6, 13.)"),
    ("Why one dispatcher is held fixed",
     r"A scope choice: the question we chose is the transfer rule, the real dispatcher's internals are unknown to us, and a controlled comparison needs everything else fixed. Synthetic data do not forbid comparing dispatch algorithms. (Slide 5.)"),
    ("Why a transfer does not end waiting",
     r"After a transfer the rider still waits for the 2-minute ordering lag and the Lyft's travel, and their patience clock keeps running from the original request. Riders can cancel before the Lyft arrives. (Slide 23.)"),
    ("Verification versus validation",
     r"Verification: does the code implement the specified model (hand keys, enumeration, tests, reruns)? Validation: does the model represent the real service? We have done verification, not validation. (Slide 21.)"),
    ("Why more service with more Lyft is a trade-off, not a universal winner",
     r"The predictive rules reached more requests within 15 minutes but used about 9--10.5 Lyft orders a night. Choosing needs a value on Lyft use, and the 15-minute measure itself favours early transfer. (Slides 22, 24.)"),
    ("Why the findings do not establish real Hopkins effects",
     r"They come from 30 constructed two-van nights with placeholder rider behaviour and a dispatcher modelled on a published design, verified but not validated. They are conditional statements about our model. (Slides 20, 26, 28.)"),
]

HUMAN_VERIFICATION = (r"A program can generate and check an answer. Human verification means a teammate independently "
                      r"works through a defined example, records their calculation and compares it with the implementation.")

ACTIVITY_INTRO = (r"This is a guided preparation activity, not a quiz or an exam. Work through the procedure on your own "
                  r"first and write down your result. Only then turn to the reference answer, which is on a separate page. "
                  r"If your result differs, record the difference rather than adjusting your working to match: a disagreement "
                  r"is useful information. The reference answer was produced with AI assistance from the project files; it "
                  r"does not count as a teammate's verification.")

# ---------------------------------------------------------------- activities (LaTeX)
ACTIVITIES = {}

ACTIVITIES["Irfan Setiadi"] = dict(
    title="Units and the proposal correction",
    slides="Slides 3--4; also slide 7",
    goal=r"Explain independently why ``about 5,100 completed rides at 6~pm'' summed over thirty days does not mean 5,100 rides in one evening's hour, and convert it to rides per evening.",
    inputs=r"""
\begin{tabularx}{\textwidth}{@{}P{5.2cm}P{3.0cm}X@{}}
\toprule
\textbf{Input} & \textbf{Value} & \textbf{Provenance}\\
\midrule
April dashboard chart ``Completed rides by hour'', 18:00 bar & 30-day total & Chart subtitle: summed over the 30 days of April; filtered to Homewood Night Ride as printed\\
Tooltip value for that bar & 5,098 & Read on the dashboard (restricted source; number only)\\
Digitized value for that bar & 5,089.09 & Our pixel reading, project file \texttt{obs\_p09\_rides\_by\_hour.csv}\\
Proposal wording & ``approximately 5,100 rides per hour'' & September proposal, slide 7 (rounded, illustrative)\\
Days in April & 30 & Calendar\\
April status totals (context only) & 50,297 requests; 24,095 completed & Dashboard status totals\\
\bottomrule
\end{tabularx}""",
    procedure=[
        r"Write down, in words, what one bar of the chart counts: which rides, which hour, over how many days.",
        r"Divide the digitized value by the number of days. Repeat with the tooltip value and with the rounded 5,100. Keep two decimals for the exact values; round only at the end.",
        r"State the result as ``completed rides in one evening's 6~pm hour'', with units.",
        r"Explain in one or two sentences why ``5,100 rides per hour'' is a units error, not a small rounding difference.",
        r"List what this calculation establishes, and what it does \emph{not} establish about (a) total requests, which include bookings that were not completed, and (b) a Homewood-specific load per vehicle.",
    ],
    reference=r"""
\textbf{Calculation.} 5,089.09 / 30 = 169.64; 5,098 / 30 = 169.93; 5,100 / 30 = 170.00. All three give about \textbf{170 completed rides in one April evening's 6~pm hour, on average}. The 5,089.09 and 5,098 are two readings of the same bar (digitized and tooltip); ``about 5,100'' and ``about 170'' are rounded, illustrative values.

\textbf{Why ``5,100 per hour'' is wrong.} The bar adds up the 6~pm hour over thirty evenings. Reading it as one hour overstates a single evening's hourly rides by a factor of 30, not by a rounding margin.

\textbf{What it establishes.} The average number of \emph{completed} rides recorded in the 18:00--19:00 hour per April evening.

\textbf{What it does not establish.}
\begin{itemize}
\item \emph{Total requests.} Completed rides are a subset of requests. Getting to about 355 requests needs the monthly ratio 50,297 / 24,095 = 2.087 requests per completed ride, and the further \textbf{assumption} that this monthly ratio holds within the hour (slide 7).
\item \emph{A Homewood-specific load per vehicle.} The rides chart is filtered to Homewood Night Ride as printed, but the vehicle count used next on slide 7 (27.6) is an ``All services'' figure, so the per-vehicle load is not Homewood-specific.
\item \emph{Night-to-night variation.} A 30-day average says nothing about how busy any one evening was.
\end{itemize}""",
    checklist=[
        r"Did I treat the bar as a 30-day total, not one hour?",
        r"Is my per-evening value within rounding of 170 for each of the three inputs?",
        r"Did I keep the exact digitized and tooltip values separate from the rounded 5,100 and 170?",
        r"Did I say that completed rides are not requests, and name the assumption needed to reach requests?",
        r"Did I note that the per-vehicle load mixes a Homewood ride count with an ``All services'' vehicle count?",
    ],
)

ACTIVITIES["Miles Zhou"] = dict(
    title="The no-show denominator",
    slides="Slide 12; also slide 11",
    goal=r"Calculate the two no-show rates from the verified April counts, explain why they answer different questions, and name the status-mapping assumptions needed before using the second as a probability at vehicle arrival.",
    inputs=r"""
\begin{tabularx}{\textwidth}{@{}P{5.6cm}P{2.6cm}X@{}}
\toprule
\textbf{Input (April 2026, whole month)} & \textbf{Count} & \textbf{Provenance}\\
\midrule
All requests (all statuses) & 50,297 & Dashboard status totals\\
Completed & 24,095 & Dashboard status totals\\
No Show & 2,359 & Dashboard status totals\\
Canceled & 23,843 & 50,297 $-$ 24,095 $-$ 2,359 (the digitized status sums also show 99 ``Denied'')\\
\bottomrule
\end{tabularx}""",
    procedure=[
        r"Compute Rate~1 = No Show / all requests. Write it as a decimal and as a percentage (one decimal place).",
        r"Compute Rate~2 = No Show / (Completed + No Show). Write it the same way.",
        r"For each rate, write the question it answers in one sentence (``Of all requests, \dots'' / ``When a vehicle reaches the curb, \dots'').",
        r"Explain why most cancelled requests do not belong in the denominator of the second rate.",
        r"List the status-mapping assumptions that must hold before Rate~2 can be used as the probability that a rider is absent when a vehicle arrives.",
    ],
    reference=r"""
\textbf{Rate 1.} 2,359 / 50,297 = 0.0469, about \textbf{4.7\%}: the share of \emph{all requests} that ended as ``No Show''.

\textbf{Rate 2.} Completed + No Show = 24,095 + 2,359 = 26,454. Then 2,359 / 26,454 = 0.0892, about \textbf{8.9\%}: the share of \emph{van arrivals at the curb} where the rider was absent, \emph{if} the statuses mean what we assume.

\textbf{Why they differ.} A no-show can only happen when a vehicle reaches the curb. Most ``Canceled'' requests never had a vehicle arrive (the rider gave up, or the request was moved to Lyft), so including them in the denominator dilutes the rate by about half.

\textbf{Assumptions needed for Rate 2} (the status mapping):
\begin{itemize}
\item ``Completed'' counts van-completed trips, each with exactly one van arrival;
\item ``No Show'' was recorded only after a real van arrival and the 3-minute curb wait;
\item requests handed to Lyft were recorded as ``Canceled'', not as completed or no-show.
\end{itemize}
These are set out in the methodology, §3.8, p.~17. None of them is confirmed by the data, so 8.9\% is a \emph{conditional derivation}, used provisionally; it is not a verified operating probability. The simulator also applies the same probability to Lyft arrivals, which is a further assumption (D-48).""",
    checklist=[
        r"Do my two rates match 4.7\% and 8.9\% to one decimal place?",
        r"Did I state a different question for each rate?",
        r"Did I explain why cancelled requests leave the second denominator?",
        r"Did I list all three mapping assumptions, and say they are unconfirmed?",
        r"Did I avoid calling 8.9\% a measured probability?",
    ],
)

ACTIVITIES["Youzhi Zhang"] = dict(
    title="One decision moment on a small designed evening",
    slides="Slides 15--16",
    goal=r"Check by hand one complete decision of the van optimizer on the small designed evening \textbf{L1}: request \textbf{R004} at decision moment \textbf{\(\tau\) = 1,853~s (18:30:53)}. You will list the feasible choices, check order and capacity, compute each objective term, and identify the selected plan.",
    inputs=r"""
\textbf{The situation at 18:30:53 (\(\tau\) = 1,853 s after 18:00).} On L1, requests are designed to arrive only when both vans are idle, so the optimizer faces a single open request.

\begin{tabularx}{\textwidth}{@{}P{4.2cm}X@{}}
\toprule
\textbf{Item} & \textbf{Value}\\
\midrule
Van V1 & idle at location \texttt{p05\_b033}, free now, no riders aboard\\
Van V2 & idle at location \texttt{p03\_b016}, free now, no riders aboard\\
Open request R004 & requested at 1,853 s; party of 1; pickup \texttt{p04\_b076}; drop-off \texttt{p05\_b015}\\
Seats & 14 per van\\
Dwell & 30 s at the pickup, counted in the ride\\
\bottomrule
\end{tabularx}

\medskip
\textbf{Travel table} (road-network times rounded to whole seconds; distances in metres; travel multiplier 1.0 on L1):

\begin{tabularx}{\textwidth}{@{}XP{2.6cm}P{2.6cm}@{}}
\toprule
\textbf{Leg} & \textbf{Seconds} & \textbf{Metres}\\
\midrule
V1 location \texttt{p05\_b033} \(\to\) pickup \texttt{p04\_b076} & 278 & 2,041.3\\
V2 location \texttt{p03\_b016} \(\to\) pickup \texttt{p04\_b076} & 56 & 383.0\\
Pickup \texttt{p04\_b076} \(\to\) drop-off \texttt{p05\_b015} & 309 & 2,449.9\\
\bottomrule
\end{tabularx}

\medskip
\textbf{Scoring rules} (slide 16). For a route: points = party \(\times\) \(\varphi\)(wait in minutes) + 0.5 \(\times\) party \(\times\) ride minutes + 0.1 \(\times\) km driven.
\begin{itemize}
\item \(\varphi\): 1 point per minute for the first 5 minutes of waiting (then 2.5, 5, 10, 20 after 5, 10, 15, 20 minutes).
\item Wait = vehicle's curb arrival $-$ request time. Ride = 30-s dwell + pickup-to-drop-off travel.
\item km driven = all legs of the route (to the pickup, then to the drop-off).
\item Ride-time guardrail: ride must not exceed max(25 min, 2 \(\times\) direct + 5 min). Direct time for R004 is 309~s.
\item Leaving R004 unserved (postponed) costs at least the large constant M, which at this moment is 15,678,893 internal units = 13.07 points (internal units are points \(\times\) 1,200,000).
\end{itemize}

{\raggedright\textbf{Sources} (for anyone with repository access):
\begin{itemize}
\item \texttt{data/scenarios/v2/L1/requests.csv} and \texttt{handcheck.csv} (row R004)
\item \texttt{outputs/sim/L1\_R0/epochs.jsonl} (the record with \(\tau\) = 1853)
\item \texttt{data/processed/tt\_locations\_v2.csv}
\end{itemize}}""",
    procedure=[
        r"List every feasible choice for this moment. (Hint: each van either takes R004 or stays idle, and R004 is served at most once. Include ``postpone R004''.)",
        r"For each choice that serves R004, check: pickup comes before drop-off; the van's load stays within 14 seats; the ride respects the guardrail.",
        r"For ``V1 serves R004'': compute the wait (minutes), the waiting term, the ride minutes, the riding term, the km driven and the driving term. Add them.",
        r"Repeat for ``V2 serves R004''.",
        r"Compare the totals with each other and with the postponement cost, and identify the plan the optimizer should choose.",
        r"Write the predicted pickup and drop-off clock times for the chosen plan.",
    ],
    reference=r"""
\textbf{Feasible choices.} (a) V1 serves R004, V2 idle; (b) V2 serves R004, V1 idle; (c) both idle, R004 postponed. Serving R004 with both vans is not allowed (served once).

\textbf{Order and capacity.} Each serving route is pickup then drop-off; load goes 0 \(\to\) 1 \(\to\) 0, well within 14 seats. Ride = 30 + 309 = 339~s = 5.65~min, within the guardrail max(25, 2 \(\times\) 5.15 + 5 = 15.3) = 25~min.

\begin{tabularx}{\textwidth}{@{}Xccc@{}}
\toprule
 & \textbf{(a) V1 serves} & \textbf{(b) V2 serves} & \textbf{(c) postpone}\\
\midrule
Wait & 278 s = 4.6333 min & 56 s = 0.9333 min & ---\\
Waiting term, 1 \(\times\) \(\varphi\)(wait) & 4.6333 & 0.9333 & ---\\
Riding term, 0.5 \(\times\) 1 \(\times\) 5.65 & 2.8250 & 2.8250 & ---\\
km driven & 2.0413 + 2.4499 = 4.4912 & 0.3830 + 2.4499 = 2.8329 & 0\\
Driving term, 0.1 \(\times\) km & 0.4491 & 0.2833 & ---\\
\textbf{Total points} & \textbf{7.9075} & \textbf{4.0416} & \(\ge\) \textbf{13.07}\\
\bottomrule
\end{tabularx}

\textbf{Selected plan: (b), V2 serves R004.} Predicted pickup = 1,853 + 56 = 1,909~s (18:31:49); drop-off = 1,909 + 30 + 309 = 2,248~s (18:37:28).

\textbf{Comparison with the implementation.} The answer key (\texttt{handcheck.csv}, row R004) lists van V2, cost\_V1 = 7.907453, cost\_V2 = 4.041623, pickup 1,909~s, drop-off 2,248~s. The simulator's decision log at \(\tau\) = 1,853 records the same two candidate routes (7.9075 and 4.0416 points, as 9,488,944 and 4,849,948 internal units), the V2 route chosen, an optimal solve and a unique optimum.

\textbf{What this verifies, and what it does not.} It verifies this one defined decision: the scoring arithmetic, the feasibility checks and the choice the optimizer made for R004 at 18:30:53. It does \emph{not} verify the MILP in general, decisions with several open requests or riders aboard, the candidate-generation limit of three new pickups, the postponement price, or the rest of the evening.""",
    checklist=[
        r"Did I list three choices, including postponement?",
        r"Do my two serving totals match 7.9075 and 4.0416 within 0.001?",
        r"Did I include the 30-s dwell in the ride minutes and both legs in the km?",
        r"Did I select V2 and state why (lower total, far below the postponement cost)?",
        r"Did I state that this checks one decision only, not the whole optimizer?",
    ],
)

ACTIVITIES["Vignesh Rajesh Babu"] = dict(
    title="One transfer timeline (``Lyft arrives sooner'')",
    slides="Slides 18 and 23; also slide 17",
    goal=r"Work through the verified designed-case transfer independently: the expected Lyft arrival, the comparison with the predicted van pickup, the transfer margin, the rider's total wait, and why the van time is not an observed counterfactual.",
    inputs=r"""
\textbf{Designed evening L4, rule ``Lyft arrives sooner'', request R011.} On this small designed evening the Lyft delay is fixed at 8 minutes by design, so realized and expected Lyft times coincide.

\begin{tabularx}{\textwidth}{@{}P{6.4cm}P{2.4cm}X@{}}
\toprule
\textbf{Input} & \textbf{Value} & \textbf{Kind}\\
\midrule
Request time & 18:16:30 & Recorded event\\
Decision moment (rule evaluated) & 18:17:00 & Recorded event\\
Van plan's predicted pickup for R011 at 18:17:00 & 18:30:08 & \textbf{Prediction}\\
Ordering lag (decision to Lyft order) & 2 min & Assumed setting\\
Typical Lyft delay used by the rule & 8 min & Assumed setting\\
Transfer margin & 2 min & Rule parameter\\
Lyft ordered & 18:19:00 & Recorded event\\
Lyft at the curb & 18:27:00 & Recorded event\\
Rider dropped off by the Lyft & 18:30:25 & Recorded event\\
\bottomrule
\end{tabularx}

{\raggedright\textbf{Sources} (with repository access): \texttt{outputs/sim/L4\_R3-2/epochs.jsonl} (decision at 1,020~s) and \texttt{outcomes.csv} (R011).\par}""",
    procedure=[
        r"Compute the expected Lyft pickup at the decision moment: decision time + ordering lag + typical delay.",
        r"Compute the difference between the predicted van pickup and the expected Lyft pickup, in minutes and seconds.",
        r"Decide whether the rule fires: is the Lyft expected \emph{more than} 2 minutes sooner?",
        r"Compute the rider's wait from request to the vehicle's curb arrival.",
        r"Compare the drop-off time 18:30:25 with the predicted van pickup 18:30:08 and state the exact difference.",
        r"Explain in two sentences why the predicted van time cannot be used to claim that the transfer helped this rider.",
    ],
    reference=r"""
\textbf{Expected Lyft pickup.} 18:17:00 + 2 min + 8 min = \textbf{18:27:00}.

\textbf{Difference.} 18:30:08 $-$ 18:27:00 = \textbf{3 min 8 s}. This is more than the 2-minute margin, so the rule fires and R011 is moved to Lyft. (Equivalently: the rule fires when the predicted van pickup is later than now + 12 minutes, that is, later than 18:29:00.)

\textbf{Wait.} The Lyft reached the curb at 18:27:00, so the wait was 18:27:00 $-$ 18:16:30 = \textbf{10 min 30 s}.

\textbf{Drop-off versus predicted van pickup.} 18:30:25 is \textbf{17 seconds after} 18:30:08, not before it. A drop-off and a predicted pickup are different events, so this comparison shows nothing about which option was better.

\textbf{Why the van time is not a counterfactual.} 18:30:08 is the van plan's \emph{prediction} at 18:17:00, made before later events. Once R011 moved to Lyft, the vans re-planned without it, so we never observe when, or whether, a van would actually have picked this rider up. The example shows how the rule compares two predictions; it is not evidence of a saving. Whole evenings are compared instead (slide 20).""",
    checklist=[
        r"Did I include the 2-minute ordering lag in the expected Lyft time?",
        r"Is my difference exactly 3 min 8 s, and did I compare it with the 2-minute margin using ``more than''?",
        r"Is my wait 10 min 30 s, measured to curb arrival, not to drop-off?",
        r"Did I state that 18:30:25 is 17 seconds after 18:30:08?",
        r"Did I explain that the van time is a prediction, not an observed outcome?",
    ],
)

DESIGNER_NOTES = [
    r"The presentation content is frozen. Restyling must not change meaning, numbers, rule names or slide order.",
    r"Keep every factual sentence as written, including the lead sentences in blue and the statements of what a result does \emph{not} show.",
    r"Keep both label systems and their wording: evidence labels (OBSERVED, DERIVED, ASSUMED, DESIGNED, SIMULATED, ILLUSTRATIVE, and combinations such as DERIVED + ASSUMED) and execution-status bands (TESTED IN SIMULATION, PLANNED --- NOT YET RUN, PROPOSED --- NOT IMPLEMENTED). Do not rely on colour alone.",
    r"Keep the component colours consistent: simulator grey, van optimizer blue, transfer rule orange, hidden information violet (dashed).",
    r"Keep sources readable. Do not move essential qualifications (for example ``curb arrival, not boarding'', ``this measure favours early transfer'', ``no noise margin applied'') into footnotes or small print.",
    r"\textbf{The slide count and order are frozen} (28 main slides, the divider on slide 29, backups on 30--38): every slide number in the guide, the briefs and the Q\&A table depends on them. Do not add, remove or reorder slides.",
    r"Keep the original proposal slides framed and labelled ORIGINAL PROPOSAL, with the masked maps and the numbered correction markers on slide 4.",
    r"Charts are native and editable; keep direct labels and a single value axis. Keep backup slides and their ``back to slide'' links working.",
    r"Check slides 7, 14, 16 and 22--25 for text fit after any font change; the preview was rendered with LibreOffice.",
]
