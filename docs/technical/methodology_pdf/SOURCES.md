# Sources used for the methodology companion PDF

Files read for `BlueJay_Scenario_Methodology.pdf` (companion v1.0, 22 Oct 2026). Hashes were taken on 22 Oct 2026 after M2 and the provisional approval of pending price A (methodology v1.3, spec v0.7, model_design v0.5). Earlier builds used methodology v1.0–v1.2, spec v0.4–v0.6, model_design v0.2–v0.4 and earlier decision-log versions; their hashes are in the git history of this file.

| File | Version / date | SHA-256 |
|---|---|---|
| `docs/technical/scenario_methodology.md` | v1.3, 22 Oct 2026 | `20fa76a050d4c61096e3a7992d0c64381f7f7a1382a412c9814411b96e10c0fd` |
| `docs/technical/scenario_spec.md` | v0.7, 22 Oct 2026 | `f2d74e9806946dd769b85ec096000a52cfec81bd257bc088e58304ef39dbf806` |
| `docs/technical/model_design.md` | v0.5 draft, 22 Oct 2026 | `407d2d5bcfb7f1c55218b5f8caa31a5fd3a8e25019c0729aa9031ec6b8d087ea` |
| `docs/technical/decision_log.md` | through D-55, with the D-53 approval and design trail §11, 22 Oct 2026 | `2c68be1f052d55c73453917fb43517c29e2781898e1fb8b6aaf6ec078a7c26eb` |
| `docs/technical/preregistration_v2.md` | draft, revised 22 Oct 2026 | `6b05cf0ffed51b7373e46c60dd765520cef618846f9404945f08e9cb9ed28140` |

**Simulation artifacts read (never written)**

| File | Used for | SHA-256 |
|---|---|---|
| `outputs/sim/L4_R0_M1_reference/epochs.jsonl` | Table 13 (M1, original price, 18:15 plan), re-derived | `7b962cc5a96ee9e0a049e51124c7d6b3cc8f2b71247315d64c079220b4991f88` |
| `outputs/sim/d53_experiment/d53_comparison.md` | Table 14; values re-derived from `d53_experiment/L4_R0_pp-{original,A,B}/` outcome and epoch files, assignment changes quoted | `38f11a09deafbc912445443ed91c2b0d6386b51340a736e7702af1fd6cc7e127` |
| `outputs/sim/m2_L4_report.md` | Tables 15–16; Table 15 re-derived from `outputs/sim/L4_<rule>/outcomes.csv` and `events.csv` (van-km from `data/processed/tt_locations_v2.csv` metres) | `dbc1e1dc841d5cf2cbe69735d4e79a05d777c0a9a1209dc6b8882720a4bf697e` |
| `outputs/sim/L4_R2-15/epochs.jsonl` | Table 16 and the worked transfer (plan the rule read vs re-solved plan at 18:20), checked | `8aa01b9cda54997a1787f9027c87afed9997afa28884f1647abd789a4a170233` |

**Other inputs**
- Coordinator messages, 22 Oct 2026: they said what to update. No rule or number was taken from a message without checking it in the files above.
- Bibliographic details only: `research_notes/math_literature.md` (literature rows 2, 3, 7, 8, 32, 37) and `transloc_operations.md` §12.

**Not used as authority:** `scenario_contract.md` (paused v1), `archive/*`, `docs/evidence/` and the restricted April PDF. April numbers in the PDF are the aggregates already quoted in the files above.

If any source changes, re-hash it (`shasum -a 256 <file>`), compare with this table, and update the PDF before relying on it.
