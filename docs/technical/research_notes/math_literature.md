# Mathematical formulation and literature: research notes

**Workstream:** formulation and literature (Phase 3, input to 3B scenario framing). **Date:** 12 Oct 2026. **Status:** research notes for team review. This is not a decision record. Nothing here changes `decision_log.md`, the guide or the preregistration until the team adopts it.

**Scope:** Homewood only. Curb-to-curb inside the service region; designated-stop consolidation is out of scope. Whether Peabody belongs inside the Homewood scope is **an open boundary decision, flagged here and not decided** (see §7, R-9).

**Labels used in this note**

| Label | Meaning |
|---|---|
| **VERIFIED** | I read the passage myself (full text, or the abstract when the claim is only at abstract level) |
| **SECONDARY** | A search-engine summary, a repository listing or a third-party description. I did not read the source |
| **RECALLED** | From my prior knowledge of the paper, not re-read in this pass. Treat as **UNVERIFIED** until someone checks the full text |
| **INFERENCE** | My reasoning from verified material |
| **HYPOTHESIS** | A claim the simulation should test |

"Access" in the source table means the most I actually read: **Full** (full text, or the relevant sections of it), **Abs** (the abstract), **Meta** (bibliographic metadata, plus at most an auto-generated one-line summary), **Sec** (secondary description only).

---

## 0. Ten-line summary

1. **Our problem is a dynamic, immediate-request, multi-vehicle DARP** without rejection. Hopkins essentially never denies a request; overflow goes to Lyft instead. The closest formal relatives are the dynamic DARP/PDP literature (Psaraftis 1980; Berbeglia et al. 2010), ride-pooling assignment (Alonso-Mora et al. 2017), and the VRP with private fleet and common carrier for the Lyft leg.
2. **A route-selection (set-partitioning) MILP per epoch is the right centerpiece.** This is RTV-style, as the team's player C already plans. Capacity, precedence, pairing, onboard commitments, shift end and ride caps are all checked when candidate routes are generated. The MILP itself is then a small assignment problem.
3. **In a route-selection MILP, the convex wait penalty costs nothing.** Each candidate route's cost is computed outside the solver, so φ(w) can be any function and the model stays a linear MILP. Convexity only matters in a node-arc model (needed for the clairvoyant benchmark H). There a **piecewise-linear epigraph** keeps it an exact MILP for the PWL function, with no extra binaries. A quadratic penalty would make it an **MIQP, not a linear model**, and HiGHS does not solve MIQPs (SECONDARY).
4. **The only quantitative clue about TransLoc's penalty implies strong convexity.** The 2016 example prefers cutting 1 min from a 10-min wait over cutting 2 min from a 5-min wait. With a power law w^p, that needs **p > 1.80**: linear fails, and quadratic passes only narrowly (INFERENCE, §2.4).
5. **Recommendation:** use a **weighted** objective (convex wait + linear ride + small miles) with a **hard but elastic ride-time/detour cap**, not a lexicographic one. Lexicographic "wait first" is the extreme version of "safety first" and reproduces the long-ride tail; keep it as a variant.
6. **Rolling-horizon reassignment is standard and valuable, but it causes "nervousness".** Riders see their ETA change. Freeze assignments inside a commit window, and **report an ETA-churn metric**; Hopkins riders already complain about ETAs.
7. **The Lyft literature splits two ways.** Hopkins uses a **separate after-the-fact rule** (dispatcher, pending ride, wait threshold). The OR literature mostly **integrates** the outsourcing choice by comparing marginal costs (VRPPC; Grahn et al. 2023; Gonzales et al. 2019). Both are legitimate *policies*. Compare them as a **frontier** (Lyft trips vs. P90 wait), because we have no defensible $ cost per Lyft trip.
8. **Greedy can tie optimization at low load.** Bertsimas, Jaillet & Martin (2019) find greedy within 2% of optimal at low demand, and a large gap only at medium to high demand. Our L1–L4 levels (2 vans, 16 rides) will probably show **no** C − A gap. That is a valid finding, not a failure; pre-register it.
9. **The clairvoyant H is an upper bound only under strict conditions:** the same objective, the same rules, solved to proven optimality (or its dual bound used), and a clear treatment of cancellations and Lyft. Otherwise "H − C" is not "the value of information".
10. **Disagreements with current docs:** the preregistered primary metric (20/25-min "timely served") uses East Baltimore limits and a step function the optimizers don't minimize. AS-03's "lexicographic or weighted" should be decided as weighted plus a cap. The "TransLoc-like" baseline supports claims about *a policy structured like the vendor's 2016 design*, not about TransLoc.

---

## 1. Source table

Ordered by role. Rows 1–3 are the sources the project already cites.

| # | Citation | DOI / URL | Access | Method | Applicability to us | Limitation | Implication for our model |
|---|---|---|---|---|---|---|---|
| 1 | Cordeau, J.-F. & Laporte, G. (2007). The dial-a-ride problem: models and algorithms. *Ann. Oper. Res.* 153(1), 29–46 | 10.1007/s10479-007-0170-8; abstract at gerad.ca/en/papers/G-2006-78 | **Abs** (GERAD working-paper page) | Survey of DARP models and algorithms. VERIFIED at abstract level: minimum-cost routes for *n* users under a set of constraints, with paratransit as the main application | Defines the problem class and vocabulary (pairing, precedence, ride time) | Pre-2007, and mainly static / advance-request. Specific contents RECALLED: the static vs. dynamic distinction, user-inconvenience objectives, ride-time limits | Cite it for the definitions only. Don't cite it for any dynamic-dispatch claim without reading the full text |
| 2 | Jaw, J.-J., Odoni, A., Psaraftis, H. & Wilson, N. (1986). A heuristic algorithm for the multi-vehicle advance request DARP with time windows. *Transp. Res. B* 20(3), 243–257 | 10.1016/0191-2615(86)90020-2 | **Abs** (RePEc, read through a summarizing fetch) | Sequential insertion. VERIFIED (abstract): two upper bounds, one on deviation from the desired time and one on ride time (a maximum ride time); a flexible objective trading operator cost against customer disutility. Tested on 2,600 customers and about 20 vehicles | The canonical **insertion heuristic**: our greedy A and the inner move of any local search | Advance-request, not immediate. RECALLED, not re-read: max ride time as an affine function of direct ride time, and the exact disutility form | Use insertion with a ride-time cap as the baseline A. If we cite the "MRT = a + b·direct" form, verify it in the full text first |
| 3 | Alonso-Mora, J., Samaranayake, S., Wallar, A., Frazzoli, E. & Rus, D. (2017). On-demand high-capacity ride-sharing via dynamic trip-vehicle assignment. *PNAS* 114(3), 462–467 | 10.1073/pnas.1611675114 (PMC5255617) | **Full** (Europe PMC XML) | VERIFIED: batch assignment through a request-trip-vehicle (RTV) graph, then an ILP choosing one trip per vehicle; each request is assigned or pays a large constant c_ko. Hard **max wait Ω** (e.g. 2 min) and **max total delay Δ** (e.g. 4 min, wait included). Cost = sum of delays. Requests are re-pooled each batch; onboard riders keep their delay guarantee. Anytime: greedy warm start, timeouts. Rebalancing of idle vehicles | **Template for player C**: route selection over feasible candidate trips, re-solved each batch with reassignment | Taxi-scale NYC with tight Ω/Δ. Unserved requests are *dropped* if not matched within Ω (we must defer, not drop). The cost is linear in delay | Use the RTV structure. Replace "drop after Ω" with "defer with a growing penalty" (no denials at Homewood). Replace the linear delay cost with a convex wait term (§2) |
| 4 | Cordeau, J.-F. (2006). A branch-and-cut algorithm for the dial-a-ride problem. *Oper. Res.* 54(3), 573–586 | 10.1287/opre.1060.0283 | **Abs** (Crossref) | VERIFIED: MIP formulation with **capacity, duration, time-window, pairing, precedence and ride-time** constraints; branch-and-cut with DARP-specific, TSP, VRP and PDP valid inequalities; solves "small to medium-size" instances. RECALLED: a 3-index formulation with service-start, load and ride-time variables linked by big-M time propagation | The **node-arc formulation for H** (the offline benchmark) and for hand-checkable L1 instances | Static, minimum-cost objective; exact solution only at small size | Base the H formulation on it. Expect H to close only at L1–L2 sizes, and report [incumbent, bound] otherwise (as the preregistration already says) |
| 5 | Ropke, S., Cordeau, J.-F. & Laporte, G. (2007). Models and branch-and-cut algorithms for PDPTW. *Networks* 49(4), 258–272 | 10.1002/net.20177 | **Abs** | VERIFIED: two new PDPTW/DARP formulations with a ride-time limit, valid inequalities, branch-and-cut; up to 8 vehicles and 96 requests solved | Stronger node-arc alternatives for H | Static, cost objective | If the 3-index H model is too weak, the 2-index formulations here are the next step |
| 6 | Psaraftis, H. (1980). A dynamic programming solution to the single vehicle many-to-many immediate request DARP. *Transp. Sci.* 14(2), 130–154 | 10.1287/trsc.14.2.130 | **Abs** (Crossref) | VERIFIED: DP. Objective = weighted completion time + customer "dissatisfaction", linear in wait and ride time. The dynamic version re-solves after every new request and **does not anticipate future requests**. **Priority rules prevent indefinite deferment** | The original **immediate-request, re-plan-on-every-request** model, i.e. TransLoc's event trigger | One vehicle; DP is exponential | **Starvation is a known failure of re-optimization.** Under a linear wait cost, re-planning can push an old request back indefinitely. We need either a convex wait penalty or an explicit position/age guard (§2.4, §4) |
| 7 | Berbeglia, G., Cordeau, J.-F. & Laporte, G. (2010). Dynamic pickup and delivery problems. *EJOR* 202(1), 8–15 | 10.1016/j.ejor.2009.04.024 | **Abs** (RePEc; first sentence verbatim, rest paraphrased) | Survey of dynamic PDPs where people or objects are collected and delivered in real time: general issues and solution strategies | The problem class of our engine | I could not read the full text. Its specific taxonomy and claims are **UNVERIFIED** | Cite it as the class survey only |
| 8 | Ho, S.C., Szeto, W.Y., Kuo, Y.-H., Leung, J.M.Y., Petering, M. & Tou, T.W.H. (2018). A survey of dial-a-ride problems: literature review and recent developments. *Transp. Res. B* 111, 395–421 | 10.1016/j.trb.2018.02.001 | **Abs** (RePEc paraphrase) | Survey of DARP research since 2007: classification of variants and methods, benchmark instances, applications, future directions | The up-to-date map of variants and methods | Full text not read; specific claims **UNVERIFIED** | Cite it as the post-2007 survey. Someone with library access should read its dynamic-DARP and objective-function sections before the oral exam |
| 9 | Psaraftis, H., Wen, M. & Kontovas, C. (2016). Dynamic vehicle routing problems: three decades and counting. *Networks* 67(1), 3–31 (online 2015) | 10.1002/net.21628 | **Abs** | VERIFIED: taxonomy of DVRP papers on 11 criteria, including **the objective function, time constraints, the ability to reject customers and the nature of the stochasticity** | Places our model on standard axes: no rejection, soft time targets, stochastic arrivals | Survey; no method | Use its 11 criteria to describe our scenario in the report, so classmates and the professor can place it |
| 10 | Pillac, V., Gendreau, M., Guéret, C. & Medaglia, A. (2013). A review of dynamic vehicle routing problems. *EJOR* 225(1), 1–11 | 10.1016/j.ejor.2012.08.015 | **Abs** (RePEc paraphrase) | Classifies routing problems by the **quality and evolution of information**; introduces a **degree of dynamism** | Lets us quantify how dynamic each ladder level is | The abstract does not cover periodic vs. event re-optimization | Report the degree of dynamism per level (INFERENCE: near 1 for immediate requests, so anticipation matters) |
| 11 | Bertsimas, D., Jaillet, P. & Martin, S. (2019). Online vehicle routing: the edge of optimization in large-scale applications. *Oper. Res.* 67(1), 143–162 | 10.1287/opre.2018.1763; preprint mit.edu/~jaillet/general/online-routing-18.pdf | **Full** (author preprint, Mar 2018) | VERIFIED: rolling-horizon **re-optimization every Δt = 30 s with a 15 s solve limit**; offline MIO, greedy insertion, 2-OPT and a "backbone" sparsification; warm starts. Offline full-information optimum = **upper bound for any online strategy**. "When demand is low, the greedy heuristic performs almost optimally, always within 2% of the optimum"; a large edge for optimization at medium to high demand with non-trivial time windows | The **most direct evidence on when greedy vs. MILP differ**, and how to build a rolling horizon with time budgets | Taxi, **no pooling** (one customer per trip); profit/throughput objective; much of the online edge uses **advance request information** (mean prior request time 15 min), which our riders do not give | Pre-register "C ≈ A at low load". Run C under a fixed solve budget < cadence. Our gains will be smaller than theirs, because we have no advance information |
| 12 | Gaul, D., Klamroth, K. & Stiglmayr, M. (2021). Solving the dynamic DARP using a rolling-horizon event-based graph. *ATMOS 2021*, OASIcs 96, 8:1–8:16 | 10.4230/OASIcs.ATMOS.2021.8 | **Full** (abstract and model sections) | VERIFIED: re-solves an event-based MILP when requests arrive; accepted-but-not-picked-up requests **may be reassigned**; **picked-up users are never relocated**; every accepted request must be served; 99.5% of iterations optimal within 30 s; mean response 2.8 s on more than 500 real requests | Shows that an **exact per-epoch MILP is feasible in practice** at our scale (small fleet, hundreds of requests a night) | Has accept/reject, which we don't; a German ride-pooling service | Copy the commitment rule (onboard = fixed vehicle; unpicked = movable). It is evidence that player C can be exact, not heuristic, at L1–L6 |
| 13 | Ichoua, S., Gendreau, M. & Potvin, J.-Y. (2000). Diversion issues in real-time vehicle dispatching. *Transp. Sci.* 34(4), 426–438 | 10.1287/trsc.34.4.426.12325 | **Abs** | VERIFIED: allows diverting a vehicle away from its current destination for a new request; evaluated within tabu search; shows savings | Whether a van heading to stop X can be re-routed mid-edge | Courier setting | **A modelling choice to fix explicitly.** Recommend no mid-edge diversion: the van's next stop is committed, which matches TransLoc's "next stop" tablet. Diversion can be a sensitivity case |
| 14 | Mitrović-Minić, S. & Laporte, G. (2004). Waiting strategies for the dynamic PDPTW. *Transp. Res. B* 38(7), 635–655 | 10.1016/j.trb.2003.09.002 | **Abs** (RePEc paraphrase plus two short quotes) | Solution quality depends on how waiting time is distributed along routes; compares four waiting strategies | Whether idle vans should wait in place, drive on, or reposition | Courier; time windows | Our vans' idle policy (stay at last drop vs. return to a hotspot) is a hidden lever. Fix it identically for all players |
| 15 | Mitrović-Minić, S., Krishnamurti, R. & Laporte, G. (2004). Double-horizon based heuristics for the dynamic PDPTW. *Transp. Res. B* 38(8), 669–685 | 10.1016/j.trb.2003.09.001 | **Abs** (RePEc) | Evaluates insertions over short- and long-term horizons, managing slack in the far future; no forecasting of future requests | A cheap way to be "less myopic" without forecasts | Courier | Optional variant only; don't add it to the main ladder |
| 16 | Santi, P., Resta, G., Szell, M., Sobolevsky, S., Strogatz, S. & Ratti, C. (2014). Quantifying the benefits of vehicle pooling with shareability networks. *PNAS* 111(37), 13290–13294 | 10.1073/pnas.1403657111 | **Abs** | VERIFIED (significance statement): the shareability network turns trip-sharing into a graph problem; NYC taxi data | The origin of the pairwise shareability step inside RTV | Max 2–3 riders per trip; offline | The pairwise-compatibility pre-filter speeds up candidate generation |
| 17 | Simonetto, A., Monteil, J. & Gambella, C. (2019). Real-time city-scale ridesharing via linear assignment problems. *Transp. Res. C* 101, 208–232 | 10.1016/j.trc.2019.01.019; arXiv 1902.10676 | **Abs** (arXiv) | VERIFIED: casts ridesharing as a **linear assignment** between vehicles and requests in a federated architecture; up to 4× faster with similar service quality | A middle rung between greedy (A) and the full RTV MILP (C) | One new request per vehicle per batch | If C's candidate enumeration explodes at L7, a linear-assignment batch is a defensible fallback |
| 18 | Hyland, M. & Mahmassani, H. (2018). Dynamic autonomous vehicle fleet operations: optimization-based strategies to assign AVs to immediate traveler demand requests. *Transp. Res. C* 92, 278–297 | 10.1016/j.trc.2018.05.003 | **Sec** (ITS-UCI and TRID listings via search) | SECONDARY: optimization-based assignment vs. FCFS rules; **reassignment** of AVs already en route; at low fleet utilization, nearest-idle performs about as well as advanced strategies | Value of reassignment, and the low-load tie again | No pooling; secondary access only | Corroborates row 11. Don't cite specific numbers |
| 19 | Fielbaum, A. & Alonso-Mora, J. (2020). Unreliability in ridesharing systems: measuring changes in users' times due to new requests. *Transp. Res. C* 121, 102831 | 10.1016/j.trc.2020.102831 | **Sec** (search summary plus HEART 2020 abstract listing; DOI verified on Crossref) | SECONDARY: defines measures of how a user's times change *within a trip* when new requests are inserted ("one-time unreliability") and across days | **This is the nervousness metric we need**: TransLoc reassigns, and riders complain about ETAs | Not read in full | Add **ETA churn**: the number and size of changes to a rider's promised pickup time. Report it for every player that reassigns |
| 20 | Ropke, S. & Pisinger, D. (2006). An ALNS heuristic for the PDPTW. *Transp. Sci.* 40(4), 455–472 | 10.1287/trsc.1050.0135 | **Abs** | VERIFIED: competing destroy/repair sub-heuristics chosen adaptively by past performance | The standard modern metaheuristic for our class | Static; tuning effort | If we ever need a heuristic C at L7, ALNS is the reference. Not needed for L1–L6 |
| 21 | Cordeau, J.-F. & Laporte, G. (2003). A tabu search heuristic for the static multi-vehicle DARP. *Transp. Res. B* 37(6), 579–594 | 10.1016/S0191-2615(02)00045-0 | **Meta** (Crossref; Semantic Scholar auto-summary) | Tabu search with vehicle capacity, route duration and **maximum ride time** side constraints. RECALLED: penalized infeasible moves, and a schedule step that delays departures to shorten ride times | The classic DARP local search; closest academic analogue to TransLoc's annealing | Static | RECALLED detail worth checking: **ride-time feasibility needs a scheduling step, not just a sequence**. With "depart as early as possible" scheduling, our generator must state that vans never deliberately idle (§2.2) |
| 22 | Attanasio, A., Cordeau, J.-F., Ghiani, G. & Laporte, G. (2004). Parallel tabu search heuristics for the dynamic multi-vehicle DARP. *Parallel Computing* 30(3), 377–387 | 10.1016/j.parco.2003.12.001 | **Meta** | (Auto-summary) Parallel versions of the static tabu search applied to the dynamic DARP | Shows the standard "static solver inside a re-optimization loop" design | Not read | Supports the design pattern only |
| 23 | Madsen, O.B.G., Ravn, H.F. & Rygaard, J.M. (1995). A heuristic algorithm for a DARP with time windows, multiple capacities, and multiple objectives. *Ann. Oper. Res.* 60, 193–208 | 10.1007/BF02031946 | **Meta** | (Auto-summary) REBUS, insertion-based, for online scheduling with **user-weighted multiple goals** | An early real-world dynamic insertion system with weighted objectives | Not read | Precedent for "weighted multiple objectives" in operational DARP |
| 24 | Parragh, S., Doerner, K., Hartl, R. & Gandibleux, X. (2009). A heuristic two-phase solution approach for the multi-objective DARP. *Networks* 54(4), 227–242 | 10.1002/net.20335 | **Abs** | VERIFIED: cost vs. client-centred objective; weighted-sum solutions plus path relinking; ε-constraint for exact efficient sets on small instances | How to treat wait vs. ride as **two objectives**, and why one weighted sum is only one point on the frontier | Static | Supports §3: run 2–3 weight settings and show the trade-off curve, not one tuned weight |
| 25 | Paquette, J., Cordeau, J.-F., Laporte, G. & Pascoal, M. (2013). Combining multicriteria analysis and tabu search for DARPs. *Transp. Res. B* 52, 1–16 | 10.1016/j.trb.2013.02.007 | **Abs** (RePEc paraphrase) | Cost plus three quality-of-service criteria; reference-point method plus tabu search; Montreal data; finds diverse non-dominated solutions | Same as row 24, on real paratransit data | Static | Same as row 24 |
| 26 | Parragh, S., Doerner, K. & Hartl, R. (2010). Variable neighborhood search for the DARP. *Comput. Oper. Res.* 37(6), 1129–1138 | 10.1016/j.cor.2009.10.003 | **Meta** | (Auto-summary) VNS with ejection-chain neighbourhoods exploiting zero-load arcs | Local-search alternative | Not read | Not needed |
| 27 | Hunsaker, B. & Savelsbergh, M. (2002). Efficient feasibility testing for dial-a-ride problems. *Oper. Res. Lett.* 30(3), 169–173 | 10.1016/S0167-6377(02)00120-7 | **Meta** | RECALLED: a fast feasibility test for a route under time windows and ride-time limits | Candidate-route generation for C needs a fast feasibility check | Not read | For our sizes, brute-force forward simulation of each candidate route is enough. Cite this only if we need speed |
| 28 | Arslan, A., Agatz, N., Kroon, L. & Zuidwijk, R. (2019). Crowdsourced delivery: a dynamic PDP with ad hoc drivers. *Transp. Sci.* 53(1), 222–235 | 10.1287/trsc.2017.0803 | **Abs** | VERIFIED: a real-time platform matches tasks to ad hoc drivers, and a **dedicated backup fleet** serves the rest; rolling horizon with an exact matching each time new information arrives | **Structural analogue of van + Lyft**: two resource types chosen jointly in a rolling horizon | Here the backup is the *own* fleet and the flexible resource is external (the reverse of ours); parcels, not people | Supports **integrating** the Lyft choice inside the epoch MILP as a column with its own cost |
| 29 | Chu, C.-W. (2005). A heuristic algorithm for the truckload and less-than-truckload problem. *EJOR* 165(3), 657–667 | 10.1016/j.ejor.2003.08.067 | **Meta** (RePEc: no abstract) | SECONDARY (search summary): the origin of the **VRP with private fleet and common carrier** (VRPPC): each customer is served by the own fleet or outsourced at a per-customer price; savings-based heuristic | The static form of "van or Lyft" | Static freight; not read | The standard name for our overflow structure is VRPPC. Cite it through row 30, which I could at least read the abstract of |
| 30 | Côté, J.-F. & Potvin, J.-Y. (2009). A tabu search heuristic for the VRP with private fleet and common carrier. *EJOR* 198(2), 464–469 | 10.1016/j.ejor.2008.09.009 | **Abs** (RePEc paraphrase) | VERIFIED (abstract): each customer is served by the own fleet or the common carrier; minimize fleet fixed + variable cost + carrier charges; tabu search beats prior methods on 34 instances | Formal "serve or outsource" in one objective | Static; needs a $ price for outsourcing | Integration requires a **Lyft cost parameter**. We have no defensible $ value, so use a frontier or a shadow-price sweep (§5) |
| 31 | Bolduc, M.-C., Renaud, J. & Boctor, F. (2007). A heuristic for the routing and carrier selection problem. *EJOR* 183(2), 926–932 | 10.1016/j.ejor.2006.10.013 | **Meta** | SECONDARY: a simpler heuristic for VRPPC, reported to beat Chu (2005) | VRPPC lineage | Not read | Background only |
| 32 | Grahn, R., Qian, S. & Hendrickson, C. (2023). Optimizing first- and last-mile public transit services leveraging TNCs. *Transportation* 50(5), 2049–2076 (online 2022) | 10.1007/s11116-022-10301-z; accepted manuscript osti.gov/servlets/purl/1885410 | **Full** (abstract and method §3) | VERIFIED: each new request goes by insertion to the shuttle with the least **marginal cost** MC (weighted wait + in-vehicle time over all its riders). It is then sent to a **TNC if MC / TNC user cost > λ**; TNC wait drawn from historical Uber distributions. Hybrid (1 shuttle + TNC) vs. 2 shuttles: −6.0% cost, +7.7% service, up to −40% P95 travel time at peak | **The closest published analogue of our van + Lyft overflow** (on-demand shuttles + TNC, simulated with real demand) | Decides at **request time**, not after a wait. Pittsburgh FMLM; 2 shuttles; λ must be calibrated | Gives us a concrete **integrated policy** to test against Hopkins' threshold rule: "Lyft if the marginal cost of inserting into a van exceeds λ × the Lyft cost" (§5). Also: TNC wait as a draw from a distribution, which matches AS-08 |
| 33 | Gonzales, E.J., Sipetas, C. & Italiano, J. (2019). *Optimizing ADA paratransit operation with taxis and ride share programs.* MassDOT Report 19-004, UMass Amherst | umasstransportationcenter.org/Document.asp?DocID=714 | **Full** (abstract and §2.5) | VERIFIED: estimates each trip's **marginal cost** by removing it from greedy-built routes (three types: a trip needing its own vehicle is costliest; an end-of-route trip is moderate; a mid-route trip is cheapest). Shifts the trip with the largest saving vs. the TNC fare, re-optimizes, and repeats until no saving remains; modeled 40–48% cost reduction | **Integrated outsourcing by marginal cost**, in an agency (paratransit) setting | Daily offline planning, not real-time; estimates are modeled, not observed | Marginal cost is highest when a trip forces an extra vehicle out at peak. **Hypothesis for us:** the most valuable Lyft transfers are spatially isolated requests at peak, not simply the longest-waiting ones |
| 34 | Archetti, C., Speranza, M.G. & Weyland, D. (2018). A simulation study of an on-demand transportation system. *Int. Trans. Oper. Res.* 25(4), 1137–1161 | 10.1111/itor.12476 | **Abs** | VERIFIED: simulates dynamically routed minibuses without fixed stops; users accept if the ETA meets their threshold, otherwise choose another mode; scenarios, scalability, responsiveness | Methodological precedent for a simulation study of an on-demand service with synthetic demand | Mode choice we don't model | Supports our simulation-first design. No campus specifics |
| 35 | TransLoc TechLog (2016). *Ridesharing algorithms in TransLoc OnDemand* (archived 28 Apr 2018) | via `transloc_operations.md` §3.2 and §12 | **Sec** (I rely on the project's own reading) | VENDOR 2016: simulated annealing; reassign/reorder moves; weighted wait/ride/miles; convex wait; re-plan on events and every 2 min | Defines baseline T | Nine years old; one blog post | §2.4 extracts the one quantitative constraint it gives on the penalty shape |
| 36 | Bertsimas, D. & Tsitsiklis, J. (1997). *Introduction to Linear Optimization*, Athena Scientific, §1.3 (piecewise-linear convex objectives) | textbook | **RECALLED** | Minimizing a max of affine functions is an LP through an epigraph variable | Justifies the PWL epigraph in §2.3 | — | Standard result. Cite the textbook in the report |
| 37 | HiGHS solver README / documentation | github.com/ERGO-Code/HiGHS; highs.dev | **Sec** (search summary of the README and a wrapper's docs) | SECONDARY: HiGHS solves LP, convex QP and MIP, but **not MIQP**; a quadratic term with integers is rejected or ignored | Our solver is HiGHS (preregistration, player C) | Check the pinned version's release notes | **Do not use a quadratic wait penalty with HiGHS.** Use PWL |

**Campus / night-safety literature.** I found **no peer-reviewed optimization or simulation study of a university night safe-ride service** (searches on safe ride, campus night shuttle and campus dial-a-ride returned vendor pages from Via, TransLoc and Slidr, and general DARP work). The nearest evidence is (a) the TransLoc/SIMPO 2020 vendor simulation already in `transloc_operations.md` §3.6, and (b) general on-demand simulation (row 34). **INFERENCE:** this is a genuine gap and a modest contribution our report can claim, provided the claim is phrased as "a simulation study calibrated to aggregate dashboards", not as an evaluation of Hopkins operations.

---

## 2. Recommended formulation for one decision epoch

### 2.1 State at epoch time τ (what the engine hands the player)

| Symbol | Meaning |
|---|---|
| V | Vans in service at τ |
| n_v, a_v | Van v's **committed next node** and its arrival time there. A van mid-edge is not diverted: its next stop is fixed (choice per row 13) |
| E_v | Shift end of van v. After E_v it may finish onboard drop-offs but not accept new pickups that end later than E_v + g (g = grace, ASSUMED) |
| Q_v | Seat capacity (14 per AS-15; 10 and 7 as variants) |
| O_v | **Onboard parties** of v: each has a drop-off d_r, party size q_r, pickup time p_r (sunk) and request time t_r. They are fixed to v (pairing) |
| C_v | **Committed pickups** of v: requests whose pickup is v's next stop, or where v has arrived and is in the 3-min wait. Fixed to v (§4.3) |
| R | **Open requests**: requested, not picked up, not committed, not cancelled, not transferred. Each r has t_r, o_r, d_r, q_r ≤ 5 and a Lyft-eligibility flag e_r = 1[q_r ≤ 4]. Requests already assigned to a van but not committed **are in R**: they may be reassigned |
| T(i,j) | OSRM travel time × multiplier (AS-21), plus dwell s (AS-17) at each stop |

No future requests are in the state; the player sees only revealed requests (fairness rule, §4.5).

### 2.2 Decisions. Recommended: route selection over feasible candidate routes

For each van v, enumerate a set K_v of **candidate routes**. A route k is an ordered stop sequence starting at n_v that contains every drop-off in O_v, every pickup and drop-off in C_v, and the pickup and drop-off of a subset S_k ⊆ R. Always include the "committed work only" route k⁰_v (S = ∅), so every epoch has a feasible solution.

For each candidate, **forward-simulate** the schedule: depart each stop as soon as service ends (vans never idle on purpose; this is ASSUMED and stated). That gives each rider's pickup time P_r^k and drop time D_r^k. A candidate is kept only if it passes these **checks at generation time**:

- **Capacity:** the running load never exceeds Q_v.
- **Precedence and pairing:** each pickup comes before its own drop-off on the same van.
- **Onboard commitments:** O_v and C_v are served by v, in the committed first position for C_v.
- **Shift end:** the last new pickup's drop-off is by E_v + g.
- **Ride cap (hard, or elastic as below):** D_r − P_r ≤ L_r for every rider on the route, including those already onboard.

Variables:
- y_vk ∈ {0,1}: van v executes route k;
- u_r ∈ {0,1}: open request r is **deferred** (stays pending to the next epoch; no denial at Homewood);
- ℓ_r ∈ {0,1}: r is transferred to Lyft, only in the **integrated-Lyft** variant (§5); otherwise ℓ_r ≡ 0.

MILP:

```
min  Σ_v Σ_{k∈K_v} c_vk · y_vk  +  Σ_{r∈R} π_r · u_r  +  Σ_{r∈R} κ_r · ℓ_r
s.t. Σ_{k∈K_v} y_vk = 1                                   ∀ v ∈ V      (one route per van)
     Σ_v Σ_{k∈K_v : r∈S_k} y_vk + u_r + ℓ_r = 1            ∀ r ∈ R      (each open request: van, defer, or Lyft)
     ℓ_r ≤ e_r                                             ∀ r ∈ R      (party ≤ 4)
     y, u, ℓ binary
```

Route cost, with W_r = P_r − t_r (wait, **measured from the request time**, so sunk wait counts) and H_r = D_r − P_r (ride):

```
c_vk = Σ_{r ∈ S_k ∪ C_v} q_r·φ(W_r)  +  Σ_{r ∈ S_k ∪ C_v ∪ O_v} q_r·[ β·H_r + ψ(H_r − L̄_r)⁺ ]  +  γ·miles_k
```

- φ is the convex wait penalty, β the ride weight, and γ a small mileage weight. ψ(·)⁺ is an optional soft penalty above a ride *target* L̄_r that lies below the hard cap L_r (§3).
- Weighting by party size q_r means "per passenger". The dashboard counts riders, so this matches the reporting unit. Whether TransLoc weights per booking or per rider is UNKNOWN.

**Why this structure (INFERENCE):**
- Every hard rule lives in route generation, which is easy to unit-test by hand on L1. The MILP is a small set-partitioning problem that HiGHS solves in milliseconds at our sizes.
- The same model covers player C (joint) and, restricted to |S_k| ≤ 1 with sequential processing, player A (greedy insertion). The ladder gaps then isolate one ingredient each, as the architecture page intends.
- It is the Alonso-Mora RTV pattern (row 3), with "drop after Ω" replaced by "defer at price π_r".

**Size control.** Bound |S_k| (e.g. ≤ 3 new requests per van per epoch) and keep only the best few sequences per subset. Note this as a restriction in the report: **C is then "optimal over the enumerated candidates", not globally optimal for the epoch.**

**The deferral price π_r is a real modelling decision, not a detail.** If π_r is too small, the optimizer defers hard requests forever: this is the starvation risk Psaraftis (1980) guarded against with priority rules. Two defensible choices:
- (a) π_r = q_r·φ(W_r^lb) + M, where W_r^lb is a lower bound on r's wait if picked up next epoch, and M is large. Then any feasible assignment beats deferral, which is TransLoc-like: everything gets a plan and an ETA.
- (b) π_r = q_r·φ(W_r^lb) with no M, which allows strategic holding.

**Recommend (a) for baseline T and C.** Under (a), a request is deferred only when no candidate route can take it, i.e. it is genuinely unassignable now.

### 2.3 Node-arc alternative (for H and for hand-checks), and how a convex penalty enters a MILP

For the clairvoyant benchmark H, routes cannot be enumerated (the whole night or hour). Use a Cordeau (2006)-style formulation (row 4; its details are RECALLED):

- binary arc variables x_ij^v;
- continuous service-start times B_i;
- loads Λ_i;
- big-M time propagation B_j ≥ B_i + s_i + T(i,j) − M(1 − x_ij^v);
- precedence B_{d(r)} ≥ B_{p(r)} + s + T(p(r), d(r));
- ride cap B_{d(r)} − (B_{p(r)} + s) ≤ L_r;
- wait W_r = B_{p(r)} − t_r ≥ 0, with B_{p(r)} ≥ t_r (no pickup before the request in H, since H knows requests early but riders don't appear early).

Here W_r is a **continuous decision variable**, so the shape of φ matters:

| Option | How it enters | Model class | Exact? | Use |
|---|---|---|---|---|
| **PWL convex epigraph** | Breakpoints 0 < b₁ < … < b_m (e.g. 5, 10, 15, 20 min) with **increasing** slopes σ₀ < σ₁ < … < σ_m. Add θ_r ≥ φ(b_j) + σ_j(W_r − b_j) for every piece j, plus θ_r ≥ σ₀W_r, and minimize Σ q_r θ_r | **MILP** (the binaries are only the routing ones; **no extra binaries**) | Exact for the PWL function, because minimization drives θ_r down to the max of the affine pieces, which equals φ_PWL(W_r) when φ is convex | **Recommended** for H, and for any node-arc C |
| PWL with SOS2 / λ-formulation | Convex-combination weights on the breakpoints | MILP with SOS2 | Exact for PWL | Needed only if φ is **non-convex** (e.g. a step at 15 min to count "late" riders). Avoid |
| Quadratic φ(W) = W² | Quadratic objective term | **MIQP. Not a linear model.** Convex MIQP | Exact for the quadratic | Not with HiGHS (row 37, SECONDARY). Would need Gurobi/SCIP. Don't call it linear |
| Step / indicator ("wait > 15 min") | Binary z_r with W_r ≤ 15 + M·z_r | MILP with extra binaries and big-M | Exact for the step | Matches the "timely served" metric (§7, R-2), but gives weak LP bounds and no incentive once a rider is already late. Avoid as the objective; keep it as a reported metric |

In the route-selection model (§2.2), **none of this is needed**. φ is evaluated when each route's cost is computed, so even a non-convex φ keeps the MILP linear. That is a strong argument for using route selection for C, and keeping node-arc only for H.

### 2.4 Choosing φ: what the TransLoc example pins down (INFERENCE)

TransLoc's 2016 example prefers cutting 1 min from a 10-min wait over cutting 2 min from a 5-min wait. As a constraint on the penalty, that reads φ(10) − φ(9) > φ(5) − φ(3).
- **Linear** φ: 1 > 2 is false. So the vendor's penalty is **not linear**.
- **Power law** φ = w^p: the inequality needs **p > 1.80** (solved numerically: equality at p ≈ 1.799). **Quadratic (p = 2) passes narrowly** (19 > 16).
- **PWL:** the slope on [9, 10] must exceed **twice** the average slope on [3, 5].

**Proposed default (ASSUMED, to be agreed in 3B).** Per-minute slopes of 1 on [0, 5], 2.5 on [5, 10], 5 on [10, 15], 10 on [15, 20] and 20 above 20 min.
- This passes the TransLoc check: φ(10) − φ(9) = 2.5 > φ(5) − φ(3) = 2.
- Avoid a slope of exactly 2 on [5, 10]: it makes the two sides equal, and the check fails.
- Test a gentler and a steeper variant (AS-03).

The breakpoints at 15 and 20 min tie the penalty to the published Homewood targets. The TransLoc example constrains only the region from 3 to 10 min. **Everything above 10 min is our choice and must be labelled ASSUMED.**

Why convex matters beyond fidelity:
- With a **linear** wait cost, sunk wait is irrelevant to the marginal decision. The optimizer is then indifferent between making a 20-min-old request wait 2 more minutes and making a fresh request wait 2 more minutes. That invites starvation under reassignment.
- A convex φ evaluated on W_r = P_r − t_r (the total, including sunk time) automatically prioritizes old requests. This is the mathematical form of "safety first".

---

## 3. Weighted vs. lexicographic priorities

The goal: "waiting matters more than riding, but no unreasonable onboard delays".

| | Weighted sum (φ(W) + β·H + γ·miles) | Lexicographic (min wait; then min ride s.t. wait ≤ (1+ε)·opt; then miles) |
|---|---|---|
| Solves per epoch | One | Two or three (each stage is a MILP); ε must be chosen |
| Meaning | Explicit exchange rate between wait and ride; easy to explain at the board | "No amount of ride time is worth one second of wait" |
| Failure mode | The weights are arbitrary (TransLoc's are not public); results depend on them | **Unbounded onboard detours.** The wait-first stage happily sends onboard riders around the block to pick up another rider. That is exactly the long-ride tail behind April's P90 of 24 min against a 20-min target, and the student complaints of long, indirect rides |
| Interaction with rolling horizon | Smooth | Stage-1 ties are common at small scale, so stage 2 decides a lot. Small changes in stage 1 can flip stage 2: more nervousness |
| Literature | REBUS (row 23), Jaw (row 2), Grahn (row 32) all weight | Multi-objective DARP work (rows 24–25) shows a single weighting is one point on a Pareto frontier. The case for lexicographic order is weak when the frontier is smooth |

**Recommendation:**
1. **Weighted objective** with a convex φ (§2.4), **β < φ′ in the busy range**, and a small γ. This encodes "wait matters more" as a *marginal* statement: past about 5 min of waiting, one minute of wait costs more than one minute of ride.
2. **Hard ride cap as a constraint**, not an objective term, so "no unreasonable onboard delays" is guaranteed rather than traded away. Use a detour-based cap, L_r = max(L_abs, α·T(o_r, d_r) + δ). For example, L_abs = 20 min (the Homewood target), α = 2 and δ = 5 min; all ASSUMED.
   - The 20-min absolute target alone is infeasible for some long O-D pairs once dwell and pickups are added. Check against the 13.6-min longest direct drive (T6) and the Peabody pairs (§7, R-9).
   - The detour form is RECALLED from Jaw et al. (1986); verify before citing.
3. **Make the cap elastic in the dynamic setting.** Delays (no-shows, dwell variance) can make every candidate route violate the cap for an onboard rider. A strictly hard cap then leaves the epoch with no feasible route at all.
   - Add a violation term with a very large penalty Ψ·(H_r − L_r)⁺, and log every violation.
   - Report the violation count as a metric. It should be zero almost always; if it isn't, that is a finding.
4. **Report the frontier.** Run three weight settings: wait-heavy (closest to lexicographic), the default, and ride-heavy. Show mean/P90 wait against P90 ride. This answers the AS-03 question with a figure instead of a guessed weight.
5. **Keep lexicographic as one named variant** ("strict safety-first"). Its expected signature (HYPOTHESIS) is the lowest P90 wait and the worst P90 ride. If our default reproduces April's ride tail only when it is near lexicographic, that is weak evidence about how the real engine is weighted. It is only weak, because many other factors shape the tail.

---

## 4. Rolling horizon

### 4.1 Triggers and cadence
- **Event triggers** (TransLoc 2016): new request, cancellation, no-show. **Add stop completion (arrival or departure) as a state update, not a re-solve.** Re-solving at every stop multiplies solves without new information.
- **Periodic tick:** Δ = 120 s for baseline T (VENDOR 2016). W = 60 s is the current preregistration default for B/C. Those differ; decide whether the cadence is a *policy* lever (vary it for one fixed algorithm) or part of the player's definition. It should not differ silently between T and C.
- **Bertsimas et al. (row 11):** Δ = 30 s with a 15 s solve cap. Their rule: the solve must finish well within Δ. Enforce a **wall-clock budget per solve** (e.g. ≤ Δ/4). If the MILP times out, use the incumbent and log it. A MILP that doesn't finish inside Δ is not implementable, and must not get extra time in simulated "frozen" time.
- **Only the next stop of each van is implemented** between epochs. Everything after it is a plan that the next solve may revise.

### 4.2 Reassignment and nervousness
- **Value:** reassignment of unpicked requests is what makes TransLoc a coordinating dispatcher (transloc_operations §3.2). Gaul et al. (row 12) and Alonso-Mora et al. (row 3) both allow it. Hyland & Mahmassani (row 18, SECONDARY) report that it helps.
- **Cost:** riders' ETAs change ("nervousness"; Fielbaum & Alonso-Mora, row 19). Hopkins riders already complain that app ETAs don't match (PRESS 2025). Every flip also costs a driver re-route.
- **Controls, in increasing strength:**
  1. a **reassignment penalty** η per changed assignment, added to c_vk for routes that move a request from its previous van;
  2. a **commit window**: freeze r to its van once the van's ETA at o_r is ≤ h_c (e.g. 3–5 min) or r is the van's next stop;
  3. no reassignment (the "insert and never move" variant; AS-02).
- **Recommendation:** use (2) with h_c = "next stop" as the baseline, which matches the tablet's "next stop" model. Use h_c ∈ {next stop, 5 min} and "no reassignment" as AS-02 variants. **Report ETA churn** per rider for every player: the number of times the promised pickup time changed by more than 1 min, and the largest change.

### 4.3 Commitments near pickup (engine rules, identical for all players)
1. Onboard riders: fixed vehicle, never relocated (Gaul et al.).
2. A van that has arrived, or is on its final edge to o_r: r is committed. During the 3-min wait no re-plan can pull the van away; a no-show then frees it.
3. No mid-edge diversion (row 13), as a stated assumption.

### 4.4 End of night
- No new requests after 02:00, but all requests made before 02:00 are honoured (JHU). The **terminal condition is "all accepted requests served (by van or Lyft)"**, not a fixed horizon.
- Vans drop out at shift end (27.6 → 11.1 between 18:00 and midnight, All services). The route constraint "new pickups only if done by E_v + g" prevents assigning work a van can't finish. **Without it, the optimizer will plan rides on vans that are about to leave.**
- **Score the backlog explicitly:** the time the last rider is dropped, and the van-minutes after 02:00. A policy that looks good before 02:00 by deferring hard requests should pay for it here.

### 4.5 Unknown future arrivals vs. forecasts
- **Baseline T and players A, B, C are myopic.** They optimize only over revealed requests, as TransLoc 2016 and Psaraftis (1980) do. This is the honest status-quo model.
- **Anticipation options** (the literature has them; I'd keep them out of the main study):
  - rebalancing idle vans toward hotspots (Alonso-Mora rebalancing step);
  - waiting strategies (row 14);
  - double horizon (row 15);
  - sampled-scenario or forecast-aware objectives.
- **Information-leak risk (specific to us).** Our demand is synthetic, drawn from a model we wrote (gravity × IPF). A "forecast-aware" policy that uses the generator's own rates has a perfect forecast that no real dispatcher has. If anticipation is ever tested, the forecast must be estimated from a *different* sample or from April aggregates only, and the report must say so.
- **The clairvoyant H** is the only player that sees future requests. Its definition must state (§6):
  1. what it knows: request times, O/D and party sizes for the whole hour;
  2. whether it knows each rider's **patience draw**. If cancellations depend on wait, H's outcomes depend on its own decisions. Simplest: run H only where there are no cancellations (L1), or treat patience as known deadlines, which is a legitimate offline DARP with time windows;
  3. whether it can use Lyft. If it can, the comparison needs the same Lyft cost as C.

---

## 5. Lyft overflow: separate rule vs. integrated decision

| | **Separate rule** (Hopkins practice; AS-06) | **Integrated** (Lyft as a column in the epoch MILP) |
|---|---|---|
| Mechanism | After a solve, a dispatcher stand-in transfers pending rides with party ≤ 4 whose expected wait > θ (e.g. 15 min), after a lag λ_d, at peak | In §2.2, ℓ_r ∈ {0,1} with cost κ_r. The optimizer chooses van, defer or Lyft jointly. Variant: the Grahn et al. (row 32) **marginal-cost ratio rule**, Lyft if MC_r / Lyft-cost_r > λ |
| Literature | Matches what Hopkins describes (JHU, PRESS). There is no OR literature on wait-threshold transfers specifically. Closest: the TCRP digest on "overflow" to taxis/TNCs (SECONDARY) | VRPPC (rows 29–31), crowdsourced delivery with a backup fleet (row 28), MBTA paratransit marginal cost (row 33), shuttle + TNC (row 32) |
| Decides on | **Age / expected wait** of the request | The **marginal cost** of serving it by van, which includes the detour imposed on other riders |
| Pros | Simple, explainable, directly controllable by Hopkins; the honest baseline | Picks the trips that are *expensive for the fleet* (isolated, at peak), not just the late ones. Gonzales et al. find the costliest trips are those forcing an extra vehicle out at peak |
| Cons | Transfers late; the rider has already waited θ + λ_d plus the Lyft wait. That can exceed 25 min in total, matching the student reports of 25–30 min | Needs a cost κ_r per Lyft trip in the *same units* as wait minutes. We have **no defensible $ value or weight**. The result is sensitive to κ. Also less like what Hopkins does today |
| Timing | Late (after waiting) | Early: it can transfer at request time if a van is clearly far. Grahn decides at request time |

**Recommendation:**
1. Keep the **separate rule as part of baseline T**: it *is* the status quo.
2. Treat Lyft strategies as **operating policies**, compared on a **frontier**: Lyft trips per night (the resource cost) against P90 wait and the share waiting over 15 min (rider outcome).
   - Generate the frontier by sweeping θ for the rule-based family, and κ (a shadow price) or λ for the integrated family.
   - If one family's frontier dominates, that is a defensible finding **without ever assigning a dollar value to a Lyft trip**.
3. **Early-transfer variant.** "Transfer at request time if the best van ETA > θ_e" is a simple, explainable middle ground. It is the cheapest policy for Hopkins to adopt.
4. **Keep Lyft eligibility e_r = 1[q_r ≤ 4]** and the Lyft wait draw (AS-08) **identical across families**.
5. Lyft capacity is treated as unlimited (AS-08). State that this assumption **favours aggressive Lyft policies**.

**What this lets us claim (INFERENCE):** "Within our simulator, policy X reaches the same P90 wait as the Hopkins-like rule with N fewer Lyft trips per night (or a lower wait at the same N)." It does **not** let us claim dollar savings, or that Hopkins' actual dispatchers use θ = 15.

---

## 6. What greedy-vs-MILP comparisons can and cannot show

**Distinguish two kinds of improvement** (the research question depends on it):
- **Algorithm improvement:** the same objective, constraints, cadence, commit rule and Lyft rule; only the solver changes (A → C, or annealing-like T → exact C). That measures **optimization quality**.
- **Policy improvement:** the objective weights, ride cap, cadence, commit window, Lyft rule or fleet by hour changes, with the algorithm held fixed. That measures **operating choices Hopkins controls**.
- A comparison that changes both at once (e.g. "C with integrated Lyft" vs. "T with the threshold rule") cannot attribute the gain to either. Design it as a 2 × 2.

**Greedy vs. MILP can show:**
- the value of *joint* assignment within an epoch, **for our stated objective**, at the load tested;
- where on the load axis that value appears. Bertsimas et al.: about 0 at low load (within 2%), large at medium to high load with flexible windows. Expect the same shape; **pre-register "C − A ≈ 0 at L1–L4"**;
- whether a heuristic ties the MILP. Tying is a real finding (persona rule), and it means the vendor heuristic is probably adequate.

**It cannot show:**
1. **That the MILP beats TransLoc.** Our T is an approximation of a nine-year-old public description. The real engine's weights, candidate lists and current algorithm are unknown (AS-03, AS-04).
2. **That per-epoch optimality is optimal over the night.** A rolling horizon with exact epochs is still myopic. Exact epoch solves can do *worse* over the night than a heuristic on some instances (INFERENCE: an epoch-optimal plan can position vans badly for requests that haven't arrived yet). Report distributions over replicates, not single nights.
3. **Effects on metrics the objective does not target**, unless measured. Example: optimizing φ(W) + βH says nothing directly about the "timely served" step metric.
4. **Real Hopkins magnitudes.** Only aggregates are available, so calibration matches marginal distributions (wait/ride percentiles, status shares), not trip-level behaviour. Several mechanisms can fit the same aggregates (identifiability).
5. **Value of information (H − C)** unless H is solved to proven optimality under the same rules. Otherwise H − C mixes information, myopia and H's optimality gap. With the [incumbent, bound] bracket, the honest statement is "the value of information is at most bound − C".

**What a vendor-like baseline lets us claim:** "Relative to a dispatcher with the structure TransLoc published in 2016 (event plus 2-minute re-plan, reassignment, convex wait penalty), and calibrated so the simulated status shares and wait/ride percentiles fall within April's ranges, policy X changes outcome Y by Z, across N replicates and stated sensitivity ranges." Nothing stronger. In particular, no "Hopkins could save …".

---

## 7. Gaps and risks in the current framing

| ID | Risk / disagreement | Where | Recommendation |
|---|---|---|---|
| R-1 | **The primary metric uses East Baltimore limits.** Preregistration §3 defines "timely passengers served" with 20/25 min, which transloc_operations §4.2 shows are East Baltimore goals; Homewood is 15/20, and soft | `preregistration.md` §3, D-04 | Already flagged as paused. When re-registering, use Homewood 15/20 thresholds **as reported metrics**, and keep the full wait/ride distributions primary |
| R-2 | **The objective and the metric don't match.** Players minimize a convex penalty (or delays); the primary metric is a step count. A player can win on one and lose on the other, and a reviewer will ask why we didn't optimize the metric | preregistration; AS-05 | State the choice: we optimize a rider-cost proxy and report the step metric. Or make the step metric secondary. Don't tune φ after seeing the step results (persona: no post-hoc tuning) |
| R-3 | **AS-03 is left as "lexicographic or weighted".** These produce different ride-time tails, so leaving it open is not neutral | `transloc_operations.md` §9 | Decide: weighted plus an elastic hard ride cap, with lexicographic as a named variant (§3) |
| R-4 | **The deferral price is unspecified.** The architecture describes deferring and Lyft but not what a pending request costs the optimizer. With a weak π_r, C may starve requests and look good on mean wait | p2/p3 architecture; §2.2 | Fix π_r per §2.2(a) for every player; add a "max age of any pending request" metric |
| R-5 | **The H benchmark is not well defined** with cancellations and Lyft. "Knows the whole hour" must say whether it knows patience draws, and whether it may use Lyft | preregistration §2 | Define H per §4.5. Run it at L1–L2 without cancellations, and report the bracket |
| R-6 | **"T ≈ C" is overstated.** The doc says TransLoc is close to player C. It is close in *structure* (periodic joint re-plan). But T uses annealing on unknown weights with no hard caps, while C is an exact MILP over enumerated candidates with our caps. A C − T gap mixes algorithm, constraints and weights | `transloc_operations.md` §3.2, §10 | Build T as "C's model with a heuristic solver (insertion + local search / annealing) and the same objective". Then C − T is pure algorithm, and policy changes are tested on both |
| R-7 | **The low-load ladder levels may show nothing.** L1–L4 (2 vans, 16 rides) are probably low-utilization. Bertsimas et al. find greedy within 2% there | phase3 plan §3C | Pre-register "no difference expected at L1–L4; these levels test correctness, not value". Make sure L5–L6 reach utilization where vans are mostly busy |
| R-8 | **Nervousness is unmeasured.** Reassignment is assumed to be good; its rider-facing cost (ETA churn) is not in any metric list | `transloc_operations.md` §7 "What each run reports" | Add ETA churn (§4.2) |
| R-9 | **Peabody is undecided** (open boundary decision, not decided here). It matters mathematically. Long Homewood–Peabody pairs set the minimum feasible ride cap, and they dominate the marginal-cost logic for Lyft (isolated, long trips are the natural Lyft candidates; row 33) | AS-20 | The team must decide before ride caps and Lyft rules are calibrated. Results on Lyft policy will be sensitive to it |
| R-10 | **Lyft has no cost unit.** Any integrated (κ-based) Lyft policy needs one | AS-08 | Use frontiers / shadow-price sweeps (§5), never a single κ |
| R-11 | **A perfect-forecast leak** if any anticipatory policy uses the generator's own rates | §4.5 | Ban it, or estimate forecasts from an independent sample |
| R-12 | **Cadence differs:** T's 120 s vs. B/C's 60 s. That confounds algorithm with cadence | AS-02, preregistration W = 60 s | Hold cadence equal in algorithm comparisons; vary it only as a policy lever |
| R-13 | **Party size vs. capacity.** With 14 seats and mean party 1.39, capacity rarely binds (AS-15). So the binding constraints are **time** (ride cap, shift end). C's advantage, if any, will come from sequencing, not packing | AS-15 | Expect it; make the ride cap and shift-end logic the most carefully tested part of candidate generation |
| R-14 | **Literature access gaps.** I could not read the full text of Cordeau & Laporte (2007), Ho et al. (2018), Berbeglia et al. (2010), Cordeau (2006), Jaw et al. (1986), Hyland & Mahmassani (2018) or Fielbaum & Alonso-Mora (2020). RECALLED details (the 3-index formulation, the MRT = a + b·direct form, the tabu schedule step) are **UNVERIFIED** | this note | Before the oral exam, someone with JHU library access should read Ho et al. §§ on dynamic DARP/objectives and Cordeau (2006) §2, and update rows 1–2, 4, 8 |
| R-15 | **No campus-specific literature.** Our setting (night, safety-first, university, agency-run with vendor software) has no peer-reviewed precedent that I found | §1 | Frame the contribution modestly, and don't claim to evaluate Hopkins |

---

## Takeaway (one line a teammate can present)

**Each epoch, choose one feasible route per van, plus "wait" or "Lyft" for each open request; the hard rules are checked when routes are built; the cost is a convex wait penalty plus ride time; re-solve on events and every two minutes, never moving riders already on board or the van's next stop.** That is the TransLoc-like structure as a small, exact MILP, and it lets us vary *policies* (ride cap, Lyft rule, commit window) separately from the *algorithm*.
