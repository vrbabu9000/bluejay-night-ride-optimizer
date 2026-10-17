# Documentation index

Start with the project [README](../README.md). This index lists every document, grouped by purpose. **Status** says whether a document is current, a draft awaiting agreement, or kept for the record.

## Where we are
| Document | Status | What it is |
|---|---|---|
| [plans/README.md](plans/README.md) | Current | Every phase's plan, with archived versions and change logs. **Phase 3 is v3**: scenario spec drafted, awaiting agreement |
| [plans/phase3/plan.md](plans/phase3/plan.md) | Current | What happens from spec approval to experiments |

## Research and design
| Document | Status | What it is |
|---|---|---|
| [technical/research_review.md](technical/research_review.md) | Current (v1.0, 12 Oct) | Critical review of the research direction: what the evidence supports, research questions, Homewood scope, the audit of the 25 assumptions, missing angles, calibration limits |
| [technical/transloc_operations.md](technical/transloc_operations.md) | Current (v1.1) | How TransLoc OnDemand, the Hopkins dispatchers and the Lyft overflow operate; peer campuses; assumptions register. v1.0 is in [technical/archive/](technical/archive/) |
| [technical/model_design.md](technical/model_design.md) | Draft (v0.1) | The mathematics: dynamic dial-a-ride with rolling-horizon re-planning, the convex waiting penalty, the ride guardrail, players, the Lyft module, metrics, architecture diagrams |
| [technical/scenario_spec.md](technical/scenario_spec.md) | **Draft (v0.1), awaiting agreement** | Scenario inputs vs policies vs outcomes, Lyft rules, the L1–L7 ladder, experiment matrix, schemas, seeds, validation; decisions D-A to D-G |
| [technical/compute_feasibility.md](technical/compute_feasibility.md) | Draft (v0.1) | Computing needs, solvers, OSRM portability, reproducibility, a benchmark proposal (not run) |
| [technical/research_notes/](technical/research_notes/) | Working notes | The three detailed research notes behind the review (literature, operations and validity, computing), with source tables |

## Decisions and configuration
| Document | Status | What it is |
|---|---|---|
| [technical/decision_log.md](technical/decision_log.md) | Current | Every decision that sets a number or rule (D-01 to D-26), status changes, and **open proposals P-01 to P-12** (not yet decisions) |
| [technical/team_config.v2.json](technical/team_config.v2.json) | Current (v2.1) | Parameter values with evidence labels |
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
| [technical/preregistration.md](technical/preregistration.md) | The v1 pre-registration. It is to be re-written from the approved spec |
| [plans/master/plan_v2_2026-09-29.md](plans/master/plan_v2_2026-09-29.md) | The master plan Phases 0–2 were executed from |

## Proposal stage (Sep 2026)
- [proposal/](proposal/): written proposal (.docx, .tex).
- [presentations/](presentations/): proposal deck, speaker notes and slide overlay. These describe the original plan (trip-level replay, a greedy-vs-MILP question), which was revised after the data arrived as aggregates only.

## Restricted (not in git)
`evidence/` holds the chart briefs, insight briefs, the reconciliation ledger, the data-quality scorecard and source snapshots. It derives from the restricted JHU PDF, so it is gitignored. Ask the team.
