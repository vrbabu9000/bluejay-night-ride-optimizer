# M8 run record (started 25 Nov 2026)

**Status:** CLOSED 26 Nov 2026. A log of compute, crashes and check failures for M8. It contains no outcomes. The design is in `m8_plan_2026-11.md` (FROZEN 25 Nov, sha `d9f3a4bb5ad4…`); nothing here changes it.

## Grid (plan §3)
- **Launched:** 25 Nov 09:59 ET.
- **Runs:** 780 (6 settings; R0 + 4 transfer rules in the patience settings, 4 transfer rules in the others; 5 vans; r00–r29), night by night, 8 workers, code fingerprint `1f318cef8ad4`.
- **Log:** `outputs/sim/m8/m8.log`.
- **Cutoff:** 28 Nov 12:00 ET.
- **Expected:** about 20 h at M7's loaded speeds; longer patience may slow C.

| When (ET) | Runs finished | Notes |
|---|---|---|
| 25 Nov 09:59 | 0 / 780 | Launched |
| 25 Nov 21:00 – 26 Nov 02:36 | ~280 / 780 | Laptop asleep (lid closed); `caffeinate -i` does not prevent clamshell sleep. Runs resumed in place on wake |
| 26 Nov 14:23 – 15:48 | 703 / 780 | Hibernated on low battery; resumed in place. Two runs spanning it reported 50 and 17 min of run time, so the solver's time cap did not count the sleep |
| 26 Nov 18:18 | 780 / 780 | **Complete**, before the 28 Nov 12:00 cutoff. 754 ok, 26 checks_failed, 0 crashes |

## Crashes and failed checks
- **Crashes:** none.
- **Failed checks:** 26, all the guardrail-attribution check ("no unexplained van ride over the guardrail"), each with one flagged ride. `sim.m7_explain` explains all 26 as the known pattern (an unavoidable excess shared among riders aboard after a van no-show; M7 plan §3c). So every night is kept (plan §3); the strict version drops the 11 nights with any failed check (r00, r02, r04, r08, r10, r14, r17, r19, r22, r28, r29), leaving 19.
- Full diagnoses: `outputs/sim/m8/explain_failures.txt`; the list passed to the analysis: `outputs/sim/m8/explained.json`.

| Setting | Rule | Night | Rider | Excess (s) | Riders aboard | Explained |
|---|---|---|---|---|---|---|
| lyft_fast | R1(10) | r00 | R060 | 218 | 2 | yes |
| lyft_slow | R1(10) | r00 | R060 | 218 | 2 | yes |
| consent_80 | R2(15) | r00 | R060 | 218 | 2 | yes |
| patience_long | R0 | r00 | R094 | 346 | 3 | yes |
| lyft_fast | R1(15) | r02 | R046 | 196 | 3 | yes |
| lyft_slow | R1(15) | r02 | R046 | 196 | 3 | yes |
| consent_80 | R1(15) | r02 | R046 | 196 | 3 | yes |
| consent_60 | R1(15) | r02 | R046 | 196 | 3 | yes |
| lyft_fast | R2(15) | r04 | R019 | 233 | 2 | yes |
| lyft_slow | R2(15) | r04 | R019 | 233 | 2 | yes |
| consent_80 | R2(15) | r04 | R019 | 233 | 2 | yes |
| patience_long | R1(15) | r08 | R144 | 242 | 4 | yes |
| patience_long | R1(15) | r10 | R059 | 221 | 2 | yes |
| patience_long | R1(10) | r14 | R046 | 213 | 5 | yes |
| patience_long | R0 | r14 | R125 | 273 | 5 | yes |
| patience_long | R3(2) | r17 | R134 | 241 | 2 | yes |
| patience_long | R1(10) | r17 | R040 | 252 | 5 | yes |
| patience_long | R2(15) | r17 | R040 | 252 | 5 | yes |
| patience_long | R0 | r17 | R040 | 252 | 5 | yes |
| patience_long | R1(15) | r17 | R040 | 252 | 5 | yes |
| patience_long | R1(10) | r19 | R100 | 494 | 3 | yes |
| patience_short | R2(15) | r22 | R041 | 238 | 2 | yes |
| patience_long | R3(2) | r28 | R102 | 237 | 5 | yes |
| patience_short | R1(15) | r29 | R052 | 220 | 5 | yes |
| patience_short | R0 | r29 | R052 | 220 | 5 | yes |
| patience_long | R1(10) | r29 | R081 | 200 | 2 | yes |

## Analysis
- From `src`: `../.venv/bin/python -m sim.m8 compare --explained "$(cat ../outputs/sim/m8/explained.json)"` (26 Nov 18:27 ET).
- **Post-freeze code change, formatting only:** pandas `to_markdown` needs the `tabulate` package, which the venv lacks; the first compare stopped there. Replaced with a local `_md` formatter in `sim/m8.py`. No computed value changes; `tests/test_m8.py` re-run after it.
- Results: `m8_results_2026-11-26.md`.
