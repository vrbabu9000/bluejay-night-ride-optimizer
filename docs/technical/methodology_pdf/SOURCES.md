# Sources used for the methodology companion PDF

Files read for `BlueJay_Scenario_Methodology.pdf` (companion v1.0, 22 Oct 2026). Hashes taken on 22 Oct 2026 after the D-53 decision experiment and D-54 (methodology v1.2, spec v0.6, model_design v0.4). Earlier builds used earlier versions (methodology v1.1 `86a373fe…`, spec v0.5 `d1eb562d…`, model_design v0.3 `189f859b…`, decision log `465b4118…`, epochs `7b962cc5…` (now kept as `outputs/sim/L4_R0_M1_reference/`); before that methodology v1.1 `e04f4e8f…`, spec v0.5 `cd8964e2…`, model_design v0.3 `fa7b9bfc…`, decision log `a3176f5a…`, prereg `68e89a95…`, epochs `e30a0c29…`; before that methodology v1.0 `3255df49…`, spec v0.4 `8f08dfc4…`, model_design v0.2 `39d07bf6…`, decision log `cd4b6e7f…` then `5447b0ee…`, prereg `405ffe20…`).

| File | Version / date | SHA-256 |
|---|---|---|
| `docs/technical/scenario_methodology.md` | v1.2, 22 Oct 2026 | `17025bb880d0bc7a32802cb312186a425177b5ed64d687ea233cfb0fae2c1e86` |
| `docs/technical/scenario_spec.md` | v0.6, 22 Oct 2026 | `1fd80b709dde99361e515e12aff1966deebc803cc6b05f4871df10c8c2eeb279` |
| `docs/technical/model_design.md` | v0.4 draft, 22 Oct 2026 | `0599d4ed77c9dd58f18f7270df8f1bd1b7f7bc1b37f4509fe7e172b93b3a1d` |
| `docs/technical/decision_log.md` | through D-54 (D-53 update 2, D-52 amendment 4), 22 Oct 2026 | `b22e512c1a5e2e35274d08c206ed0bc428239eba158b993673818950ccd94e2b` |
| `docs/technical/preregistration_v2.md` | draft, revised 22 Oct 2026 | `6b05cf0ffed51b7373e46c60dd765520cef618846f9404945f08e9cb9ed28140` |
| `outputs/sim/L4_R0/epochs.jsonl` | original-price arm of the D-53 run (read only; Table 13 re-derived from it) | `30904f546fc98f2893bcab8f090cddf507bfa4373c383b194e6989d11c5571c7` |
| `outputs/sim/d53_comparison.md` | D-53 comparison (read only; Table 14 re-derived from the three arms' outcome and epoch files; assignment changes quoted) | `38f11a09deafbc912445443ed91c2b0d6386b51340a736e7702af1fd6cc7e127` |

**Other inputs**
- Coordinator messages, 22 Oct 2026: approval-status reminders, and the list of where each conflict was reconciled. No rule or number was taken from the messages themselves; each was checked in the files above.
- Bibliographic details only: `research_notes/math_literature.md` (literature rows 2, 3, 7, 8, 32, 37) and `transloc_operations.md` §12.

**Not used as authority:** `scenario_contract.md` (paused v1), `archive/*`, `docs/evidence/` and the restricted April PDF. April numbers in the PDF are the aggregates already quoted in the files above.

If any source changes, re-hash it (`shasum -a 256 <file>`), compare with this table, and update the PDF before relying on it.
