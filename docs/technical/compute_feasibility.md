# Computing requirements, portability and reproducibility (v0.1, 12 Oct 2026)

**Status:** an assessment for team review. **No benchmark has been run.** Every runtime or memory figure below is either a recorded measurement (marked *measured*) or a reasoned **estimate** with its assumptions stated. Details and sources: `research_notes/compute_feasibility.md`.

## 1. Four separate workloads
| Workload | When | CPU | RAM | Storage | Notes |
|---|---|---|---|---|---|
| **OSRM preprocessing** | Once per map version | Multi-threaded; *measured* 40 s extract + partition + customize on this Mac (10 cores) | Succeeded in an 8.2 GB Docker VM; peak not measured | 215 MB pbf + ~1 GB routing files | One person, once. Not during experiments |
| **OSRM server** | Only to compute **new** coordinates | Idle otherwise | *measured* ~0.7 GB resident (2 Oct) | Same files | **Not needed to run simulations**: the 188 × 188 matrix file is enough |
| **Simulation** | Every run | Single-threaded per run; parallel **across** runs | Estimate < 0.5 GB per worker (the matrix is 283 KB) | Estimate ~0.5 MB event log per night; do not store per-epoch plans by default | Python + numpy |
| **Optimization** | Inside every run | Heuristic: estimate 0.05–1 s per re-plan at ~200 stops. Exact (HiGHS): 1 thread per solve | Heuristic small; MILP estimate tens of MB to ~1–2 GB on the largest small instances | — | Exact solves only on small instances |

**Provisional guidance for this Mac (10 cores, 16 GB):**
- run **up to 8 simulation workers**, leaving 2 cores for the OS and an optional OSRM container;
- 1 thread per worker (`OMP_NUM_THREADS=1`).

**Disk:** the experiment outputs should stay well under 10 GB, provided per-epoch plan snapshots are off (estimate).

## 2. Problem sizes and what exact methods can do (estimates)
| Case | Open requests per epoch | Exact? |
|---|---|---|
| 2 vans / 16 requests (L1–L4) | 2–6 | **Yes**: enumeration up to ~4 open; MILP up to ~8 |
| 5 vans / 30–60 per hour | 8–15 | Borderline; heuristic plus an exact *check* on sampled epochs |
| ~20–27 vans / 170–300 per hour (whole night) | 50–75 | **No** in a 2-min cadence (a node-arc MILP would have ~10⁶ arc variables); heuristic only, against a long-run heuristic reference |

**Whole-night load (estimate).** 2,400 requests means ~3,000–5,000 solves. At 0.1–0.5 s each, a large night is 5–40 CPU-minutes. 180 large nights (30 seeds × 6 rules) is then 15–120 CPU-hours, or **2–15 hours on 8 workers**.
- The upper end is too slow to iterate on, so the benchmark (§6) must measure before the experiment plan is fixed.
- Smaller Homewood windows (e.g. 18:00–21:00) cut the cost roughly in proportion.

**Exact sizes from the literature are not verified.** Cordeau (2006) reports "small to medium" instances; the exact sizes in the full text have not been checked.

## 3. Solvers and licensing
| Tool | Licence | Use |
|---|---|---|
| **HiGHS** (`highspy` or `scipy.optimize.milp`) | MIT | **Core exact solver** for C and H. Deterministic settings: `threads=1`, a fixed `random_seed`, **node limit** as the primary stop and wall time only as a safety cap. The default `mip_rel_gap` = 1e-4, so "optimal" means within 0.01% |
| OR-Tools routing (pickup and delivery) | Apache-2.0 | Optional independent heuristic cross-check |
| PyVRP | MIT | Supports pickup-before-delivery shipments; combination with time windows unverified; optional |
| Gurobi / CPLEX | Academic, per person; Gurobi named-user licences cannot run in containers | **Not recommended**: teammates couldn't reproduce runs |
| NVIDIA cuOpt | Apache-2.0, **needs an NVIDIA GPU** | Not usable on this Mac |

**GPU:** no useful role.
- The problems are small and branchy, which suits sequential local search.
- The exact references need a CPU MILP.
- A GPU path would also hurt reproducibility.

**Not installed yet:** no solver is in the venv. Adding `highspy` is part of Phase 4 setup, after approval.

## 4. OSRM portability (Windows / Linux x86-64)
**What we know:**
- The pinned image `osrm-backend:v6.0.0` **is published for linux/amd64 as well as linux/arm64**. The registry was inspected read-only.
- `PROVENANCE.json` records the *index* digest, which both architectures share. It should also record the platform and the per-platform digest.

**What we don't know:**
- **Same pbf + same image + same profile on x86-64 is not guaranteed to give identical travel times.** An upstream pull request describes platform-dependent 0.1 s rounding in extraction. It was closed without being shown merged.
- **Whether arm64-built routing files can be served by the amd64 image is undocumented.**

So **copying `data/osrm/` across architectures is not proven compatible**, and `osrm_local.md` should say "same architecture only, untested elsewhere".

**Proposed policy (for approval):**
1. **The canonical artifact is the travel-time matrix, not the server.**
   - Teammates run simulations from `tt_locations_v2.csv` (sha256 `b24c0bc6…`) plus a `MANIFEST.json` that records the hashes of every routing artifact, the pbf md5, image digests, profile and platform.
   - The simulator verifies the manifest at start-up and writes it into every output.
2. **Only one machine builds matrices.** A second machine that needs new coordinates first passes a **full-matrix cross-check** (all 35,344 pairs: max |Δ| ≤ 1 s, median 0). A failure is reported, never silently accepted.
3. Different servers keep separate caches (already enforced; add the platform to the cache key).

**Proposed tests (later approval; not run):**
- T1: rebuild on this Mac and compare the full matrix;
- T2: an emulated amd64 build on this Mac;
- T3: a native x86 machine, if a teammate has one.

## 5. Reproducibility checklist (proposed)
- **Lock file** with exact versions. `requirements.txt` today lists only folium and pillow; the venv has Python 3.10.6, numpy 2.2.6, pandas 2.3.3, scipy 1.15.3, and no solver. Python 3.10 reaches end of life around now; don't upgrade mid-project, but record the version.
- **Fingerprints:** pbf md5, image digests, matrix and snap-file sha256, scenario content hashes. The generator already hashes its content.
- **Seeds:**
  - `SeedSequence(experiment_seed, spawn_key=(scenario_id, replicate, component_id))` with **named** components;
  - every policy-independent random quantity is drawn **per request in advance** (common random numbers);
  - solver seeds are derived from the same tree.
- **Determinism hygiene:**
  - integer-second clock;
  - event ties broken by (time, priority, sequence id);
  - sorted iteration;
  - `PYTHONHASHSEED` fixed;
  - 1 thread per worker.
- **Run manifest:**
  - git commit and dirty flag, the hash of the frozen environment, Python, OS and architecture;
  - solver versions and options, all seeds;
  - wall and CPU time, solve status and gap.
- **Tests:**
  - the same run twice gives identical output hashes;
  - 1 worker vs 4 workers gives identical results;
  - **across machines:** compare within a tolerance, never bitwise (floating-point and SIMD differences).

## 6. Bounded benchmark (proposal for approval; ≤ 8 h on this Mac; not run)
| ID | Measures | Cap |
|---|---|---|
| B0 | Environment capture | 10 min |
| B1 | Heuristic re-plan time and memory vs open requests (4–100) and vans (2–25), on synthetic states | 1 h |
| B2 | HiGHS time-to-proof, nodes and gap for 2-van instances, k = 4–16 requests; a determinism repeat; 1 vs 4 threads | 3 h; stop growing k when 2 of 5 instances miss the gap in 600 s |
| B3 | Whole-night speed and peak memory for T at 2/16, 5/60·h, 25/300·h | 2 h |
| B4 | Throughput with 1/2/4/8 workers | 45 min |
| B5 | Heuristic vs exact gap on the B2 instances, with matched node/iteration budgets | within B2 |
| B6 | Portability tests T1/T2 (needs a rebuild and an image pull, so **separate approval**) | 1 h |

**Decision rules:**
- the largest k with 5/5 instances proved becomes the "exact reference range";
- if B3 at 25/300 projects over ~4 h per night, redesign the inner loop or reduce the re-plan rate before launching seeds.

## 7. Matched budgets and the meaning of "optimal"
- A **time-limited MILP is not automatically optimal**. Report its status, incumbent, bound and gap.
- **Match computation budgets by nodes or iterations**, which are reproducible, and report wall time as well.
- **Per-epoch optimal is not whole-night optimal.** Decisions are irreversible (transfers, cancellations caused by long ETAs), and future requests are unknown. A stable heuristic can beat repeated exact re-optimization over a night. That is testable.
- **Exact references exist only on small instances** (L1–L4). At Homewood scale we compare policies under the same heuristic T, and report T against greedy and a long-run heuristic.

## 8. Uncertainties in this assessment
- Every runtime is an estimate until B1–B4 run.
- Cross-architecture travel-time identity is untested.
- The OSRM peak memory during extraction is unmeasured.
- The MILP range for 2-van instances depends on the ride guardrail and the candidate limits.
