# Compute constraints: why exact dispatching limits what this project can test (18 Nov 2026)

**Status:** a record of a systemic limitation, for the team, the report and the talk. It contains no new experiment.
**Asked by:** the user, 18 Nov ("note the systemic hindrance and write a detailed documentation about this").
**Sources:**
- `m5a_compute_2026-11-10.md`, `m5b_run_record_2026-11.md`, `m5c_results_2026-11-17.md`;
- `m5c_diagnostic_results_2026-11-18.md`;
- the run manifests in `outputs/sim/m5/` (wall time and peak memory per night);
- decisions D-46, D-51, D-60 to D-64.

## 1. In plain words
- **The dispatcher is too slow at high load.** C re-plans every open request exactly, every two minutes. On a normal (base) first hour that takes a few minutes of computing per night. On a busy (high-load) first hour it takes about an hour per night, and one night took 23 hours.
- **This is not a bug.** It is the price of the exactness guarantee: C proves that each plan is the best one in its candidate set. That proof becomes very expensive when a van is nearly full and many requests are waiting.
- **The laptop can't simply throw more cores at it.**
  - **Nights run one at a time:** each night is a chain of re-plans, and each re-plan depends on the one before it, so one night cannot be split across cores.
  - **Each solve uses one thread,** so results don't depend on timing.
  - **Memory caps the parallel runs:** a busy night can need up to 6 GB, so at most two of them fit on this 16 GB machine.
- **What it costs us:**
  - Every experiment involving C at high load takes days of machine time.
  - Whole-evening runs at high load are probably out of reach before 1 Dec.
  - Each new test competes with the next milestone for the same laptop.

## 2. The evidence (all measured)
| Runs | What | Machine time (sum over nights) | Median per night | Slowest night | Peak memory |
|---|---|---|---|---|---|
| M5b, C, base, first hour, 30 nights | C as tested | 5.8 h | 8.0 min | 45 min | 2.5 GB |
| M5b, C, high load, first hour, 30 nights | C as tested | 58.1 h | 61 min | 23.3 h (r03) | 6.0 GB |
| M5b, greedy G, either load | Baseline | under 1 min in total | under 1 s | under 1 s | 0.1 GB |
| M5c, C-F, high load, 30 nights | Drop order fixed | 8.0 h | 15.2 min | 48 min | 1.5 GB |
| M5c, C-F, base, 30 nights | Drop order fixed | 1.0 h | 1.8 min | 6.3 min | 0.5 GB |

- **Elapsed time:**
  - M5b group B (high load, 60 runs) ran from 11 to 15 Nov on two workers, including a three-day pause for the r26 check (D-62).
  - M5c ran 60 runs in about 1.5 hours on six workers.
- **The tail dominates.** In the diagnostic's exact rebuild of C's 8,208 re-plans, the re-plans in which some van carried 6 or more parties were 11% of re-plans but took 65% of C's time (38 of 58 h).
- **What r03 looked like:** around minute 40, 15–17 requests were open while one van carried 6 riders. Each re-plan then took 9–12 min (M5b run record).

## 3. Why it happens (the mechanism)
1. **Candidate routes grow quickly.** For every van, C builds the best route for every set of up to K = 3 new pickups from the open requests. With 15 open requests that is 576 sets per van. Each route must also place the drop-offs of every rider already aboard.
2. **Exact reordering multiplies the work.** C may drop riders already aboard in any order (D-52 amendment). The label search that finds the best order is exact. Its work grows roughly with the number of ways to interleave the drops, and that grows very fast with the number of parties aboard.
3. **The two effects meet at the same moments.** Many open requests and full vans happen together, at the peak of a busy evening. That is why the median night is manageable but some nights explode.
4. **Determinism rules out the easy fix.** C uses a node budget (100,000 nodes) and one thread so that a plan never depends on how fast the computer is (D-46). A wall-clock time limit per re-plan would cap the tail but break reproducibility. The same night could give different plans on a busy and an idle machine.

## 4. Why more parallel computing helps only partly
- **Across nights:** yes. Nights are independent, so 30 nights can run on as many workers as memory allows.
- **Within a night:** no. Re-plans are sequential: the state at 18:42 depends on every plan before it. A 23-hour night stays a 23-hour night.
- **Within a re-plan:** in principle, but not as used here. HiGHS could use several threads, but then results may vary between runs. Candidate generation could be split across vans, but that is a code change under the frozen fingerprint.
- **This machine:**
  - 10 cores, of which only 4 are performance cores, and 16 GB of memory.
  - High-load C nights need up to 6 GB each, so at most two run at once (D-61).
  - Runs on the efficiency cores are slower, and timings measured under parallel load are slower than on an idle machine. Every compute figure here was measured that way, as was the 15-min gate.
- **Other machines:**
  - Teammates' laptops or a cloud machine could take some of the nights.
  - That would first need a check that one night gives an identical event log on both machines. This has not been tested across machines (`compute_feasibility.md`, 12 Oct).

## 5. What it has already cost the project, and the decisions it forced
| Decision | Effect of the compute limit |
|---|---|
| D-60 (M5a gate) | Median night ≤ 15 min, or the night count is reset from compute alone |
| D-61 | High load run last, at 2 workers, with a fixed order and a cutoff rule, so a slow night can't hold the analysis hostage |
| D-62 | Fixing the r26 check during M5b would have meant re-running 300 runs (~75 CPU-h). The fix was deferred and made 18 Nov |
| D-51 (proposed) | Scope: C for the base pattern; high-load full evenings reported as a compute limitation, not run |
| D-63 (M5c) | Tested the cheapest speed-up (fixed drop order). It cost about 2 pp of riders and still missed the gate (15.2 min) |
| D-64 (M5d, proposed) | Tests a partial speed-up (fix the order only in vans with 6+ parties) on fresh nights |

## 6. The M5d gamble and the queue for the laptop (decided by the user, 18 Nov)
- **Decision:** the user chose to build and run M5d (C-S6 vs C on fresh nights r30–r59), knowing it competes with M6 for the same machine. The machine is reserved for M5d until **Tuesday 24 Nov 2026, 12:00 ET**. The analysis uses whatever has finished by then (preregistered prefix rule).
- **Why the test needs this much machine time:** a fair test needs C itself re-run on the 30 fresh high-load nights. At the M5b rate that is about 58 h of machine time on two workers, plus the risk of a 23-hour night. C-S6 adds an estimated 20–25 h, and the base and greedy runs about 8 h.
- **Risks, and how they are handled:**
  - **A runaway C night can delay later nights.** The prefix rule then simply uses fewer nights; the interval gets wider, but the result is not biased by when nights finished.
  - **M6 can't start until the M5d queues finish or are stopped at the cutoff.** The phase 4 plan already puts M6 after the 26 Nov preview, so the preview itself is unaffected: it uses M5b, M5c and whatever M5d gives by the cutoff.
  - **The time left for M6 and M7 shrinks to 26 Nov–1 Dec.** M6 needs one timed full base evening before M7 is frozen (D-51 (3)). If that window is too tight, M7 is cut, not M6.

## 7. Ways out (ideas, none adopted)
| Idea | What it would buy | What it costs |
|---|---|---|
| Time budget per re-plan (anytime C: start from C-F's plan, improve until a budget runs out) | Caps the tail where it matters (diagnostic) | Results depend on machine speed unless the budget is counted in work units, not seconds; a new frozen test |
| Switch by van fullness (C-S6) | Removes the runaway nights; keeps an estimated 91% of the value | Estimated 38 min median at high load: still over the gate. Being tested (M5d) |
| Fixed drop order everywhere (C-F) | 4× faster | About 2 pp more riders not reached (M5c); still missed the gate |
| Smaller K at high load (K = 2) | Fewer candidate routes | Untested; may lose riders the same way |
| Column generation or decomposition | Scales better in principle | A new solver; weeks of work and checking |
| More machines (team laptops, cloud) | More nights at once | Needs a cross-machine reproducibility check; doesn't shorten a single night |

## 8. How to say it in the report and the talk
- **One sentence:** *"The exact dispatcher beats a simple greedy baseline, but its computing cost explodes on busy evenings when vans are nearly full, so our high-load results cover the first hour only."*
- **Always state:**
  - Every compute figure was measured on one laptop (MacBook Air, Apple M4: 10 cores, 16 GB, no fan) with parallel runs.
  - Base-load first hours took a median 8 min per night; high-load first hours a median 1 h, with one night at 23 h.
- **Never claim:**
  - that C is fast enough for live use;
  - that the high-load full evening was tested.
