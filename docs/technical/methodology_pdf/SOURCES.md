# Sources used for the methodology companion PDF

Files read for `BlueJay_Scenario_Methodology.pdf` (companion for methodology v1.6, 23 Oct 2026). The methodology hash was retaken on 23 Oct 2026 for v1.6; the other hashes date from 22 Oct 2026 after the L5 pilot and batch (spec v0.8, model_design v0.5, decision log through D-57) and were re-checked on 23 Oct. Earlier builds used methodology v1.0–v1.2, spec v0.4–v0.6, model_design v0.2–v0.4 and earlier decision-log versions; their hashes are in the git history of this file.

| File | Version / date | SHA-256 |
|---|---|---|
| `docs/technical/scenario_methodology.md` | v1.6, 23 Oct 2026 | `bd93a4548c987d1239cf0d686f4d5c01b84ca790029831ed6e4a31ccfed2f73d` |
| `docs/technical/scenario_spec.md` | v0.8, 22 Oct 2026 | `0cdb285245508c1aa01624b0ebe756b76db13bd2bc4a487bc7248cfad2f85e1f` |
| `docs/technical/model_design.md` | v0.5 draft, 22 Oct 2026 | `407d2d5bcfb7f1c55218b5f8caa31a5fd3a8e25019c0729aa9031ec6b8d087ea` |
| `docs/technical/decision_log.md` | through D-57 (D-52 amendment 5, D-56, D-57), 22 Oct 2026 | `653f09658cf345012fd34dd1d60627e3746277b4399c64da5fbf8228de6afa45` |
| `docs/technical/preregistration_v2.md` | draft, revised 22 Oct 2026 | `6b05cf0ffed51b7373e46c60dd765520cef618846f9404945f08e9cb9ed28140` |

**Simulation artifacts read (never written)**

| File | Used for | SHA-256 |
|---|---|---|
| `outputs/sim/L4_R0_M1_reference/epochs.jsonl` | M1 18:15 plan table, re-derived | `7b962cc5a96ee9e0a049e51124c7d6b3cc8f2b71247315d64c079220b4991f88` |
| `outputs/sim/d53_experiment/d53_comparison.md` | D-53 comparison table; values re-derived from `d53_experiment/L4_R0_pp-{original,A,B}/` outcome and epoch files, assignment changes quoted | `38f11a09deafbc912445443ed91c2b0d6386b51340a736e7702af1fd6cc7e127` |
| `outputs/sim/m2_L4_report.md` | M2 tables; the summary table re-derived from `outputs/sim/L4_<rule>/outcomes.csv` and `events.csv` (van-km from `data/processed/tt_locations_v2.csv` metres) | `dbc1e1dc841d5cf2cbe69735d4e79a05d777c0a9a1209dc6b8882720a4bf697e` |
| `outputs/sim/L4_R2-15/epochs.jsonl` | The step-5 table and the worked transfer (plan the rule read vs re-solved plan at 18:20), checked | `8aa01b9cda54997a1787f9027c87afed9997afa28884f1647abd789a4a170233` |
| `outputs/sim/batch_L5_v1/per_night_metrics.csv` | L5 transfer-fate and descriptive tables, verification counts (13,663 solves, 41 incomplete tie searches, 36 attributed guardrail excess events on 10 nights), re-derived; the 16 distinct requests were counted from the runs' `manifest.json` | `1e26c95e1c92defde4438d1d725f67bbfac9a952c5b19fdff0c299b575694f94` |
| `outputs/sim/batch_L5_v1/tradeoff_rule_summary.csv` | L5 trade-off figure (f9) and the dominance statements | `e94a8c0f7588c7987e8f7a7d11205cc9b4028136a091c83974552c255beb65e2` |
| `outputs/sim/batch_L5_v1/reproducibility.json` | Reproducibility wording (6 re-runs + 2 pilot comparisons) | `fdac3de70339e5b445ecf707550d3cd6b3f159100b02c029abc3a2d8b4ba5e5a` |
| `outputs/sim/batch_L5_v1/r*/R1u-10/outcomes.csv` | R1u(10) transfer times (8 on 6 nights; requests 18:21–18:28, transfers 18:35–18:38), checked | per night |

**Other inputs**
- Coordinator messages, 22 Oct 2026: they said what to update. No rule or number was taken from a message without checking it in the files above.
- Bibliographic details only: `research_notes/math_literature.md` (literature rows 2, 3, 7, 8, 32, 37) and `transloc_operations.md` §12.

**Not used as authority:** `scenario_contract.md` (paused v1), `archive/*`, `docs/evidence/` and the restricted April PDF. April numbers in the PDF are the aggregates already quoted in the files above.

If any source changes, re-hash it (`shasum -a 256 <file>`), compare with this table, and update the PDF before relying on it.
