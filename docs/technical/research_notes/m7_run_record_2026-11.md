# M7 run record (started 24 Nov 2026)

**Status:** CLOSED 24 Nov 21:16 ET (360 / 360 runs). The log of compute, crashes and check failures for M7; outcomes are in `m7_results_2026-11-24.md`. The design is in `m7_plan_2026-11.md` (FROZEN 24 Nov, sha `52237b996987…`) and `preregistration_v2.md` (FROZEN 24 Nov, sha `34cf70eaab70…`). Nothing here changes either.

## Power pilot (plan §3a)
- **Runs:** R0 and R3(2), 5 vans, L6 base_5 r30–r39, full evenings, code fingerprint `1f318cef8ad4`. Started 24 Nov about 12:10 ET with 8 workers; finished 13:04 ET.
- **Checks:** all 20 runs passed every check.
- **Compute under 8-way load:** R0 median 23.8 min, max 42.9, peak 1.15 GB; R3(2) median 3.5 min, max 5.9. R0 alone took 8.5 min in M6, so running 8 workers at once makes each run about 3× slower. Total throughput is still higher.
- **Power** (`outputs/sim/m7/power.json`; the measure is R3(2) − R0 per night):

| Measure | SD over 10 nights | Expected 95% half-width at 30 nights | Target (0.7 δ) |
|---|---|---|---|
| **Not reached within 20 min (sets the count)** | 3.25 pp | **1.16 pp** | 1.4 pp |
| Not reached within 15 min (sensitivity) | 4.89 pp | 1.75 pp | 1.4 pp |
| P90 passenger wait | 1.51 min | 0.54 min | 0.7 min |
| Lyft bookings per 100 | 2.17 | 0.78 | 1.4 |

- **Decision (mechanical, plan §3a):** 1.16 ≤ 1.4, so the main grid uses **30 nights (r00–r29)**. The 60-night branch is not used and no new nights are built.
- **Note:** the 15-min sensitivity would miss the target at 30 nights. It does not set the count (the plan says so), and its readings are labelled accordingly.
- **Use of pilot outcomes:** they are used for nothing else.

## Main grid (plan §3b)
- **Launched:** 24 Nov about 13:10 ET. 360 runs (6 rules × 5/6 vans × r00–r29), night by night, 8 workers, log `outputs/sim/m7/main.log`.
- **Cutoff:** 30 Nov 12:00 ET.
- **Expected:** about 10 h at the pilot's loaded speeds.

| When (ET) | Runs finished | Notes |
|---|---|---|
| 24 Nov 13:10 | 0 / 360 | Launched |
| 24 Nov 16:36 | 141 / 360 (136 ok, 5 failed a check) | About 40 runs an hour; nights r00–r11 under way |
| 24 Nov 21:16 | **360 / 360** (355 ok, 5 failed a check) | Complete; grid 8 h 06 min; no crash |

## Crashes and failed checks (plan §3c)
- **Crashes:** none.
- **Failed checks:** 5 runs in all (no more after 16:36), all the same check ("no unexplained van ride over the guardrail"). Each was run through `python -m sim.m7_explain`; all 5 match the §3c pattern (unavoidable excess shared among riders aboard after a van no-show), so their nights are kept:

| Run | Rider | Excess (s) | Least total excess over all drop orders (pax-s) | Explained |
|---|---|---|---|---|
| R1(10), 5 vans, r00 | R060 | 218 | 266 | yes |
| R0, 5 vans, r02 | R046 | 196 | 196 | yes (the M6 case) |
| R1(15), 5 vans, r02 | R046 | 196 | 196 | yes |
| R1u(10), 5 vans, r02 | R046 | 196 | 196 | yes |
| R2(15), 5 vans, r04 | R019 | 233 | 233 | yes |

- The strict sensitivity (§3c) will drop nights r00, r02 and r04 for every rule.

## Compute (main grid, 8-way load)
| C wall time per full evening | Median | Max |
|---|---|---|
| 5 vans, R0 / R1u(10) | 18.3 / 18.5 min | 61.1 / 60.8 |
| 5 vans, R1(15) / R1(10) / R2(15) / R3(2) | 17.4 / 9.7 / 6.5 / 3.8 | 51.7 / 39.5 / 26.0 / 19.1 |
| 6 vans, R0 / R1u(10) | 4.8 / 4.8 | 25.7 / 25.1 |
| 6 vans, R1(15) / R1(10) / R2(15) / R3(2) | 4.3 / 3.0 / 2.7 / 1.8 | 21.3 / 16.5 / 14.2 / 10.5 |

## Analysis run
- 24 Nov 21:17 ET, from `src`:
  `python -m sim.m7 compare --explained '[["r00",5,"R1(10)"],["r02",5,"R0"],["r02",5,"R1(15)"],["r02",5,"R1u(10)"],["r04",5,"R2(15)"]]'`
- Nights: 30 finished before the cutoff; 30 used; 27 in the strict sensitivity.
