# BlueJay Night Ride Optimizer

A simulation study of Johns Hopkins University's **Homewood Blue Jay Night Ride**, an on-demand, shared, curb-to-curb van service dispatched with TransLoc OnDemand, with Lyft as overflow. The study asks which **Lyft transfer rules** serve riders best, and at what cost, under a realistic re-planning dispatcher.

> **Project status (Oct 2026): Phase 3, building the world.**
> - The evidence (April 2026 dashboards) is digitized and analysed.
> - A local routing server is built.
> - The operations research is done and critically reviewed.
> - The **scenario specification is drafted and awaiting team agreement.**
> - No scenario data has been generated from it yet.
> - The simulator (Phase 4) needs separate approval.
>
> See [docs/plans/](docs/plans/README.md).

## Research question
> **Which dispatcher-initiated Lyft transfer rules improve Homewood rider outcomes, under which demand and fleet conditions, and at what resource cost, with the van dispatcher held fixed at a TransLoc-like re-planning baseline?**

**Supporting questions:**
- Does the ranking of rules hold under other dispatchers: no reassignment, greedy, small-instance exact?
- How do demand bursts and vehicle availability over the night change it?
- How do waiting-vs-riding priorities interact with the rule?
- Is it robust to dispatcher lag, Lyft pickup time and rider patience?

This is a question about an **operating policy** Hopkins controls. It is not a claim to beat TransLoc's algorithm. Why the question changed from the original "rolling-horizon MILP vs heuristics" is explained in [research_review.md](docs/technical/research_review.md).

## Approach
1. **Evidence.** JHU shared only **aggregate** April 2026 TransLoc dashboards: daily and hourly counts, wait and ride percentiles, origin/destination heat maps. No trip records. We digitized every chart with error intervals and reconciled the charts against each other: completed rides agree within 0.4% across charts.
2. **Insights.** Ten analysis tasks showed:
   - the service is supply-limited;
   - ~47% of requests are cancelled;
   - the long ride-time tail comes from routing;
   - Lyft carries ~25% of riders and tracks cancellations day by day.
3. **Operations research.** How TransLoc OnDemand, the Hopkins dispatchers and the Lyft overflow work, with every claim graded by source ([transloc_operations.md](docs/technical/transloc_operations.md)).
4. **Synthetic world.** Demand is fitted to the April origin/destination totals (gravity × IPF). Road times come from a pinned local OSRM. Latent rider traits (patience, no-show) are drawn per request, so every policy sees identical riders.
5. **Simulation (planned).** An event-driven referee simulates the night:
   - a TransLoc-like dispatcher re-plans van routes on every event and every 2 minutes, with a convex waiting penalty and a ride-time guardrail;
   - a separate Lyft-rule module transfers waiting riders;
   - results are compared on paired nights as frontiers of rider outcome against Lyft use ([model_design.md](docs/technical/model_design.md)).

**Every value is labelled** OBSERVED / DERIVED / ASSUMED / SIMULATED, and assumptions are varied rather than hidden ([decision_log.md](docs/technical/decision_log.md)).

## Repository layout
```text
.
├── README.md
├── docs/
│   ├── README.md              documentation index (start here)
│   ├── technical/             research, model design, scenario spec, decisions, OSRM how-to, team guide builder
│   ├── plans/                 every phase's plan, with versions and change logs
│   ├── proposal/              written proposal (.docx, .tex)
│   ├── presentations/         proposal deck and speaker notes
│   ├── ai_use_log.md          AI-use disclosure log (course policy)
│   └── evidence/              digitized-chart briefs (gitignored: restricted)
├── src/
│   ├── evidence/              chart and map digitizers, georeferencing
│   ├── insights/              analysis tasks T1–T10
│   ├── scenario/              locations, demand model, scenario generator v1 (paused), travel-time client
│   └── demo/                  early folium routing demo
├── infra/osrm/                local OSRM build script, docker-compose, validation
├── tests/                     scenario-generator tests
└── data/, outputs/            local data and results (gitignored)
```

## Getting started
Requirements: Python 3.10+, plus Docker Desktop if you need the local router.

Create a virtual environment and install the dependencies:
```bash
python3 -m venv .venv
```
```bash
.venv/bin/pip install -r requirements.txt
```
Run the tests:
```bash
.venv/bin/python -m pytest tests -q
```

**Data is not in the repository.** `data/` and `docs/evidence/` are gitignored, because they derive from a restricted JHU PDF. Ask the team for the data folder.
- The tests and the scenario code need `data/processed/`.
- **Simulations will need only the travel-time matrix file**, not the routing server.

**Local routing server (optional):** only for computing new travel times. Build and run instructions, portability limits and validation are in [osrm_local.md](docs/technical/osrm_local.md). It is tested on Apple Silicon only; copy map data only between machines of the same architecture.

## Documentation
The full index is [docs/README.md](docs/README.md). Key documents:

| Document | What it is |
|---|---|
| [research_review.md](docs/technical/research_review.md) | Critical review: framing, research questions, scope, assumption audit, calibration limits |
| [transloc_operations.md](docs/technical/transloc_operations.md) | How TransLoc and the Hopkins Night Ride operate (graded evidence) |
| [model_design.md](docs/technical/model_design.md) | Mathematical formulation, algorithms, Lyft rules, architecture |
| [scenario_spec.md](docs/technical/scenario_spec.md) | **Draft** scenario specification (awaiting agreement) |
| [compute_feasibility.md](docs/technical/compute_feasibility.md) | PC requirements, solvers, reproducibility, benchmark proposal |
| [decision_log.md](docs/technical/decision_log.md) | Accepted decisions, status changes, open proposals |

## Data, privacy and boundaries
This repository must not contain:
- rider names or university identifiers;
- phone numbers or email addresses from trip records;
- driver identities;
- exact residential addresses;
- raw restricted operational data;
- credentials, API keys, or private TransLoc endpoints.

**What may appear publicly:** aggregate statistics and de-identified maps only.

**What the project is not:** this is a retrospective decision-support study. It does not control live vehicles, does not modify TransLoc, and makes no deployment claims.

## Roadmap
- [x] Select the Homewood Blue Jay Night Ride use case; submit the proposal
- [x] Digitize and reconcile the April 2026 dashboards (gate G1 passed)
- [x] Insight tasks T1–T10
- [x] Research TransLoc and Hopkins operations; critical review of the research direction
- [x] Local OSRM travel-time matrix and road routes
- [ ] **Agree the scenario specification** (Homewood boundary, Lyft rules, objective, fleet range)
- [ ] Re-write the pre-registration; generate the validation scenarios L1–L5
- [ ] Build the event simulator, dispatchers and Lyft module (Phase 4); pass hand-checked validation
- [ ] Benchmark computation; calibrate to April (keeping every parameter set that fits)
- [ ] Run the Lyft-policy experiments and robustness checks
- [ ] Mid-semester update; final report and presentation

## Team
**Team FourSight:** Irfan Setiadi, Miles Zhou, Youzhi Zhang, Vignesh Rajesh Babu.

EN.553.602 Research and Design in Mathematics: Data Mining, Johns Hopkins University, Fall 2026. Instructor: Prof. Anthony J. Kearsley.

## Relationship to prior work
[VehiPathOptimizer](https://github.com/vrbabu9000/VehiPathOptimizer) is an earlier static capacitated vehicle-routing project by Vignesh Rajesh Babu (OR-Tools, OSRM, Folium). This project adds:
- paired pickups and drop-offs;
- dynamic requests;
- vehicles with riders on board;
- a re-planning dispatcher;
- outsourced overflow.

## Selected references
- Cordeau, J.-F. (2006). [A branch-and-cut algorithm for the dial-a-ride problem](https://doi.org/10.1287/opre.1060.0283). *Operations Research* 54(3), 573–586.
- Cordeau, J.-F., & Laporte, G. (2007). [The dial-a-ride problem: models and algorithms](https://doi.org/10.1007/s10479-007-0170-8). *Annals of Operations Research* 153, 29–46.
- Alonso-Mora, J., Samaranayake, S., Wallar, A., Frazzoli, E., & Rus, D. (2017). [On-demand high-capacity ride-sharing via dynamic trip-vehicle assignment](https://doi.org/10.1073/pnas.1611675114). *PNAS* 114(3), 462–467.
- Gaul, D., Klamroth, K., & Stiglmayr, M. (2021). [Solving the dynamic dial-a-ride problem using a rolling-horizon event-based graph](https://doi.org/10.4230/OASIcs.ATMOS.2021.8). *ATMOS 2021*.
- Johns Hopkins Facilities & Real Estate, [Shuttle Services](https://jhfre.jhu.edu/ts/transportation/shuttle-services/).

The full source lists, with access levels, are in [docs/technical/research_notes/](docs/technical/research_notes/).

## AI-use disclosure
AI tools (OpenAI Codex early on; Anthropic Claude Code since September 2026) have been used to:
- organise materials;
- digitize charts;
- research sources;
- draft code and documentation.

Every use is logged with its purpose, how the output was used, and how it was verified, in [docs/ai_use_log.md](docs/ai_use_log.md), as the course syllabus requires. The team is responsible for verifying all citations, equations, assumptions, code and conclusions.

## License
**Code:** MIT, see [LICENSE](LICENSE).

**Data and derived data:** not covered by the license. The JHU operational data and anything derived from it may not be redistributed; they stay outside the repository. Map data is © OpenStreetMap contributors (ODbL).
