# Sources used for the methodology companion PDF

Files read for `BlueJay_Scenario_Methodology.pdf` (companion v1.0, 22 Oct 2026). Hashes taken on 22 Oct 2026 at the final refresh (after the residue fixes and D-52 amendment 3). Earlier builds used earlier versions (methodology v1.1 `e04f4e8f…`, spec v0.5 `cd8964e2…`, model_design v0.3 `fa7b9bfc…`, decision log `a3176f5a…`, prereg `68e89a95…`, epochs `e30a0c29…`; before that methodology v1.0 `3255df49…`, spec v0.4 `8f08dfc4…`, model_design v0.2 `39d07bf6…`, decision log `cd4b6e7f…` then `5447b0ee…`, prereg `405ffe20…`).

| File | Version / date | SHA-256 |
|---|---|---|
| `docs/technical/scenario_methodology.md` | v1.1, 22 Oct 2026 (final wording: §7 test count and integrated review, §8 solve statuses) | `86a373fe8e07ffe56eb8101e6d30ec9ef351fcff469cd83bb608652eede3da3f` |
| `docs/technical/scenario_spec.md` | v0.5, 22 Oct 2026 | `d1eb562d28e499c3fd8d19f547bfda0149223d2a5a9449b4a08cfbfd4a9047e0` |
| `docs/technical/model_design.md` | v0.3 draft, 22 Oct 2026 | `189f859b120da08d10df2c6b6f957925d3852786abf208af139cfc1946735e41` |
| `docs/technical/decision_log.md` | through D-52 amendment 3 (D-51 update dated 21 Oct), 22 Oct 2026 | `465b41183e8bd394a541a26e76168a1ae70c5758cc07620f03ae77c09a794f82` |
| `docs/technical/preregistration_v2.md` | draft, revised 22 Oct 2026 | `6b05cf0ffed51b7373e46c60dd765520cef618846f9404945f08e9cb9ed28140` |
| `outputs/sim/L4_R0/epochs.jsonl` | M1 run, regenerated 22 Oct 2026 with `cd src && ../.venv/bin/python -m sim.run --level L4 --rule R0` | `7b962cc5a96ee9e0a049e51124c7d6b3cc8f2b71247315d64c079220b4991f88` |
| `outputs/sim/L4_R0/narrative.md` | same run (cross-check only) | `798a076ad4b7f4811894d6c5685fa09c3a10754fa44271d8986bfa04b4da30c8` |

**Other inputs**
- Coordinator messages, 22 Oct 2026: approval-status reminders, and the list of where each conflict was reconciled. No rule or number was taken from the messages themselves; each was checked in the files above.
- Bibliographic details only: `research_notes/math_literature.md` (literature rows 2, 3, 7, 8, 32, 37) and `transloc_operations.md` §12.

**Not used as authority:** `scenario_contract.md` (paused v1), `archive/*`, `docs/evidence/` and the restricted April PDF. April numbers in the PDF are the aggregates already quoted in the files above.

If any source changes, re-hash it (`shasum -a 256 <file>`), compare with this table, and update the PDF before relying on it.
