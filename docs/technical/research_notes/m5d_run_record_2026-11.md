# M5d run record (started 18 Nov 2026)

**Status:** a running log of compute, crashes and check failures for M5d. It contains **no rider outcomes**. The test itself is defined in `m5d_preregistration_2026-11.md` (frozen 18 Nov, sha `cda1b43885d2`), and nothing here changes it.

## Queues
- **Launched:** about 17:35 ET on 18 Nov, code fingerprint `1f318cef8ad4`, under `caffeinate -i`.
  - `m5d_C`: 2 workers, log `outputs/sim/m5/m5d_C.log`.
  - `m5d_rest`: 1 worker, log `outputs/sim/m5/m5d_rest.log`.
- **Cutoff:** 24 Nov 2026 12:00 ET.

## Development probe, r03 (finished after the freeze)
The prereg's §8 left the second probe night open. It is recorded here, as §8 said it would be.

| Night (old, high_5) | C-S6 wall time | C (M5b) | C-F (M5c) | Peak memory | Checks |
|---|---|---|---|---|---|
| r00 | 28.5 min | 76 min | 6 min | 1.0 GB | all pass, every epoch optimal |
| r03 | **3.6 h** (12,923 s) | 23.3 h | (see M5c) | **4.0 GB** | all pass, every epoch optimal |

- **What it shows:** the switch cut C's worst night by about 6.5×, but not to the diagnostic's estimate of about 1.6 h. The estimate held C's trajectory fixed, so it ignored how the plans change. Expect C-S6's high-load tail on fresh nights to sit above the diagnostic's estimate too.
- **Memory:** 4.0 GB is well above r00's 1.0 GB. Two C workers (up to 6 GB each) plus one C-S6 worker still fit in 16 GB, but with little room to spare. Avoid running other heavy work on the laptop until the cutoff.
- **No rider outcome of either probe run was read.**

## Progress checks (`python -m sim.m5 m5d status`: wall time and check status only)
| When (ET) | C high | C-S6 high | G high | Base arms | Notes |
|---|---|---|---|---|---|
| 18 Nov 20:37 | 4/30 done | 3/30 done | 3/30 done | 0/30 | No crashes, no failed checks so far |

## Crashes and failed checks
- None so far.
