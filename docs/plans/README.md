# Plans: every phase's plan, every version, and why it changed

| Folder | What's inside | Current version | Status |
|---|---|---|---|
| `master/` | The master plan v2 (29 Sep 2026): research design, phases 0-8, gates, agent plan | v2 | Phases 0-2 done from it; phases 3-8 being re-planned phase by phase |
| `phase1/` | Phase 1, Evidence: digitize all 12 April charts | v1 (as executed) | **Done**; G1 passed 30 Sep |
| `phase2/` | Phase 2, Insights: T1-T10, zones v0, OSRM table | v1 (as executed) | **Done** 30 Sep |
| `phase3/` | Phase 3, Build the world | **v3** (12 Oct) | **In progress**: research reviewed; `scenario_spec.md` v0.2 **approved 20 Oct**; generation awaiting go-ahead; v1 paused |
| `osrm/` | Local OSRM (standalone): plan, agent prompts, log | v1 | **Complete** 2 Oct (one team-policy decision pending: how teammates get the map data) |

## Rules (same spirit as the guide's versioning rule)
1. `plan.md` in each folder is the **current** plan. Its header carries the version, the date and the status.
2. When a plan changes:
   - copy the old `plan.md` to `versions/vN_YYYY-MM-DD.md` first. Archived versions are never edited;
   - then edit `plan.md` and bump the version;
   - then add a row to that folder's `log.md`.
3. `log.md` is append-only: date, version, what changed, **why**, who decided, and the evidence or outcome.
4. Execution results (gates passed, numbers) go in `log.md` too, so each log reads as the phase's history.
5. The working plan file used during planning sessions (`~/.claude/plans/…`) is a scratch copy. The files here are the record.
