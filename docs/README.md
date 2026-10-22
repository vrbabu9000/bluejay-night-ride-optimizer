# Documentation index

Start with the project [README](../README.md). This index lists every document, grouped by purpose. **Status** says whether a document is current, a draft awaiting agreement, or kept for the record.

## Where we are
| Document | Status | What it is |
|---|---|---|
| [plans/README.md](plans/README.md) | Current | Every phase's plan, with archived versions and change logs. **Phase 3 is v4** (L1–L5 generated; design consolidated 21 Oct); **Phase 4 v1**: simulator M0–M1 done 22 Oct |
| [plans/phase3/plan.md](plans/phase3/plan.md) | Current | What happens from spec approval to experiments |

## Research and design
| Document | Status | What it is |
|---|---|---|
| [technical/research_review.md](technical/research_review.md) | Current (v1.0, 12 Oct) | Critical review of the research direction: what the evidence supports, research questions, Homewood scope, the audit of the 25 assumptions, missing angles, calibration limits |
| [technical/transloc_operations.md](technical/transloc_operations.md) | Current (v1.1) | How TransLoc OnDemand, the Hopkins dispatchers and the Lyft overflow operate; peer campuses; assumptions register. v1.0 is in [technical/archive/](technical/archive/) |
| [technical/scenario_methodology.md](technical/scenario_methodology.md) | **Current (v1.2, 22 Oct)** | **Start here for the design:** how the scenarios were built from April aggregates, the system diagram, the objective with a worked example, readiness, the next milestone, and which document governs what |
| [technical/methodology_pdf/](technical/methodology_pdf/README.md) | Draft (22 Oct) | Explanatory companion PDF of the methodology and simulator contract, for teammates and the professor; not authoritative |
| [technical/model_design.md](technical/model_design.md) | Draft (v0.4, 22 Oct) | The mathematics: dynamic dial-a-ride with rolling-horizon re-planning, the convex waiting penalty, the ride guardrail, players, the Lyft module, metrics, architecture diagrams |
| [technical/scenario_spec.md](technical/scenario_spec.md) | **Scope approved 20 Oct; v0.6 (22 Oct) is the build contract**, whose §17 holds proposed and provisional conventions (see the decision log statuses) | Scenario inputs vs policies vs outcomes, Lyft rules, the L1–L7 ladder, experiment matrix, schemas, seeds, validation; **§17 simulator build rules** |
| [technical/preregistration_v2.md](technical/preregistration_v2.md) | Draft (revised 21 Oct) | Metrics, non-inferiority decision rules and hypotheses; frozen when the first L6 comparison starts |
| [technical/compute_feasibility.md](technical/compute_feasibility.md) | Draft (v0.1; environment section stale, estimates unverified) | Computing needs, solvers, OSRM portability, reproducibility, a benchmark proposal (not run) |
| [technical/research_notes/](technical/research_notes/) | Working notes | The research notes behind the 12 Oct review (literature, operations and validity, computing) and the three 21 Oct design-review notes |

## Decisions and configuration
| Document | Status | What it is |
|---|---|---|
| [technical/decision_log.md](technical/decision_log.md) | Current | Every decision that sets a number or rule (D-01 to D-51), status changes, **open proposals P-01 to P-12** (not yet decisions), and the report-ready scenario design trail |
| [technical/team_config.v2.json](technical/team_config.v2.json) | Current (v2.1) | Parameter values with evidence labels. Its `simultaneous_event_order` is superseded by `scenario_spec.md` §17.3 |
| [ai_use_log.md](ai_use_log.md) | Current | AI-use disclosure (tool, purpose, how used, how verified), as the syllabus requires |

## Infrastructure
| Document | Status | What it is |
|---|---|---|
| [technical/osrm_local.md](technical/osrm_local.md) | Current | How to build, run, validate and update the local OSRM routing server; portability limits |
| [plans/osrm/](plans/osrm/) | Complete | The OSRM workstream's plan, agent prompts and log |

## Team guide and diagrams
| Document | Status | What it is |
|---|---|---|
| Team Technical Guide (`technical/build_team_guide.py`, PDF in `output/pdf/`) | v2.2 (1 Oct) | The team's plan-of-record guide. It **predates the 12 Oct review**; an update follows spec approval (versioning rule in [technical/guide_changelog.md](technical/guide_changelog.md)) |
| [technical/architecture/](technical/architecture/README.md) | Partly outdated | The draw.io simulator diagrams and project map. The player pages predate the TransLoc-like baseline; the current architecture is in model_design.md §8 |

## Kept for the record (paused, not current)
| Document | Why it is kept |
|---|---|
| [technical/scenario_contract.md](technical/scenario_contract.md) | The Phase 3 v1 scenario contract (5 vans, 30 requests, no Lyft). Superseded in draft by scenario_spec.md |
| [technical/preregistration.md](technical/preregistration.md) | The v1 pre-registration. Replaced by `preregistration_v2.md` |
| [plans/master/plan_v2_2026-09-29.md](plans/master/plan_v2_2026-09-29.md) | The master plan Phases 0–2 were executed from |

## Proposal stage (Sep 2026)
- [proposal/](proposal/): written proposal (.docx, .tex).
- [presentations/](presentations/): proposal deck, speaker notes and slide overlay. These describe the original plan (trip-level replay, a greedy-vs-MILP question), which was revised after the data arrived as aggregates only.

## Restricted (not in git)
`evidence/` holds the chart briefs, insight briefs, the reconciliation ledger, the data-quality scorecard and source snapshots. It derives from the restricted JHU PDF, so it is gitignored. Ask the team.
