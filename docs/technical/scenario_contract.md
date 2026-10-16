# Scenario contract (Phase 3, v1, 1 Oct 2026)

> **PAUSED (12 Oct 2026).** This scenario contract v1 belongs to the paused Phase 3 v1. It is kept unchanged for the record. Its replacement is drafted in `scenario_spec.md` v0.1 (to be agreed). Do not generate data from this file.


What the world-builder produces and what the simulator (Phase 4) may rely on. Code: `src/scenario/`. Decisions: D-16 to D-22 in `decision_log.md`.

## 1. Locations and travel times
**`data/processed/locations_v1.csv`**: one row per digitized map bubble. These bubbles are the only places a request or a van can be.

| Column | Meaning |
|---|---|
| `loc_id` | The bubble id, e.g. `p04_b012` |
| `lat`, `lon` | WGS84 coordinates |
| `zone_id` | `Z01`..`Z16` (zones v1 = zones v0) |
| `endpoint` | `O` (origin map) or `D` (destination map) |
| `weight` | April completed rides at this bubble (after the D-09 scaling) |

**`data/processed/tt_locations_v1.csv`**: the complete directed matrix over all locations, with columns `origin`, `dest`, `seconds`, `meters`.
- Values are OSRM free-flow car times.
- The diagonal is 0.
- Every value is finite and non-negative.

The simulator multiplies `seconds` by the scenario's `tt_multiplier`.

## 2. Demand model
`src/scenario/demand.py`, function `fit_od(beta_per_min: float, direction: str, min_trip_s: float = 60.0) -> (table, diag)`.
- `table` is a DataFrame with columns `o_loc`, `d_loc`, `prob`:
  - `o_loc` is always an `O` location and `d_loc` is always a `D` location;
  - `prob` sums to 1;
  - it is fitted by gravity × IPF to the point margins.
- `diag` is a dict holding at least:
  - `converged` (bool), `iterations` (int);
  - `max_rel_resid_o` and `max_rel_resid_d`: the largest relative error of the fitted point margins vs the targets;
  - `zone_rel_resid_o` and `zone_rel_resid_d`: the same at zone level, as dicts keyed by zone.
- Structural zeros: pairs with `seconds < min_trip_s` (including same-place pairs) have `prob == 0`, or are absent.
- `direction`:
  - `"month_average"`: targets are the April point margins;
  - `"campus_outbound_6pm"`: origin weights in zone `Z08` are multiplied by 1.5 and the origin total is renormalised to the April total; the destination targets are unchanged.
- `beta_per_min` ∈ {0, 0.1, 0.2}. The gravity seed is `w_o · w_d · exp(-beta · seconds/60)`.

## 3. A scenario
`src/scenario/generator.py`, function `build_scenario(params: dict, replicate: int, out_dir) -> dict`. It writes three files to `out_dir`, creating the folder if needed, and returns the parsed `scenario.json`. `default_params()` returns the base-cell params (scenario M).

**`requests.csv`**, sorted by `t_request_s`, then `request_id`:

| Column | Meaning |
|---|---|
| `request_id` | `R001`, `R002`, … |
| `t_request_s` | Seconds after window start (18:00); in `[0, window_s)` |
| `o_loc`, `d_loc` | Location ids |
| `o_zone`, `d_zone` | Zone ids |
| `o_lat`, `o_lon`, `d_lat`, `d_lon` | Coordinates |
| `party` | Integer 1..4 |
| `patience_s` | Positive; the rider abandons if not picked up by `t_request_s + patience_s` (Phase 4 rule) |
| `direct_s` | Free-flow o→d seconds from the matrix |

**`fleet.csv`**:

| Column | Meaning |
|---|---|
| `van_id` | `V01`, … |
| `start_loc`, `lat`, `lon` | Where the van starts |
| `capacity` | Seats |
| `shift_start_s` | 0 |
| `shift_end_s` | `window_s`. No new assignments after this; onboard riders are finished |

**`scenario.json`** holds:
- `params`: the full dict, as given;
- `replicate`;
- `seeds`: the `master_seed` and the per-component spawn keys;
- `inputs`: sha256 of `locations_v1.csv` and `tt_locations_v1.csv`;
- `content_hash`: sha256 over `requests.csv` bytes + `fleet.csv` bytes + canonical JSON of `params` and `replicate`;
- `code_version`: informational, not part of the hash;
- `labels`: an evidence label for each parameter.

### Parameters (`default_params()`, scenario M)

| Key | Default | Notes |
|---|---|---|
| `cell` | `"base"` | |
| `master_seed` | `20261001` | |
| `window_s` | `3600` | 18:00–19:00 |
| `n_vans` | `5` | |
| `capacity` | `4` | |
| `start_rule` | `"hotspot"` | or `"depot"` |
| `n_requests` | `30` | |
| `count_rule` | `"fixed"` | or `"poisson"` (count ~ Poisson(`n_requests`)) |
| `arrivals` | `"poisson"` | Uniform order statistics on the window, or `"burst"` |
| `burst_share` | `0.4` | Under `"burst"`: `round(burst_share · n)` requests uniform in `[0, burst_window_s)`, the rest uniform on the whole window |
| `burst_window_s` | `600` | |
| `beta_per_min` | `0.1` | |
| `direction` | `"month_average"` | |
| `min_trip_s` | `60` | |
| `party_probs` | `{"1": .72, "2": .19, "3": .06, "4": .03}` | |
| `patience` | `{"dist": "exponential", "median_s": 720}` | |
| `tt_multiplier` | `1.0` | |
| `pickup_dwell_s` | `30` | |
| `dropoff_dwell_s` | `30` | |
| `wait_limit_s` | `1200` | |
| `ride_limit_s` | `1500` | |

### Random streams
One stream per component: `count`, `times`, `od`, `party`, `patience`, `fleet`.
- Each is `np.random.default_rng(SeedSequence(master_seed, spawn_key=(replicate, k)))`, with a fixed `k` per component.
- Consequences:
  - changing `patience` leaves `t_request_s`, `o_loc`, `d_loc` and `party` unchanged;
  - changing `capacity`, `n_vans` or `start_rule` leaves `requests.csv` byte-identical;
  - the same params and replicate give byte-identical files.

### Fleet start rules
- `hotspot`: vans go to the `O` locations ranked by `weight`, cycling through them if there are more vans than locations.
- `depot`: every van starts at the depot location named in `locations_v1` metadata. That is the highest-weight `O` location in `Z08` (D-17, ASSUMED).

## 4. Ladder and grid
- **Ladder:** `src/scenario/build_ladder.py` writes `data/scenarios/ladder/{S0,S1,S2,M,M60,L170,L300}/`.
  - S0 is hand-written: 1 van, 2 requests.
  - S1: 1 van, 6 requests.
  - S2: 3 vans, 15 requests.
  - M: 5 vans, 30 requests.
  - M60: 5 vans, 60 requests.
  - L170 and L300: 27 vans, with 170 and 300 requests.
- **Frozen hashes:** `data/scenarios/FROZEN.json` maps each ladder id to its `content_hash`.
- **Grid:** `src/scenario/build_grid.py` writes the pre-registered cells (see `preregistration.md`) to `data/scenarios/grid/<cell>/r00..r29/`, plus `data/scenarios/grid/manifest.csv` with `cell, replicate, content_hash`.

## 5. Clarifications (1 Oct 2026, from the independent test review)
1. **Campus tilt.** Z08 origin weights are multiplied by 1.5, then *all* origin weights are scaled uniformly back to the April origin total.
2. **Unattainable targets.** A bubble whose every partner pair is a structural zero is listed in `diag["unattainable_o"]` or `diag["unattainable_d"]`. Its mass is not redistributed. None occur in v1.
3. **Labels.** `labels` covers every modelling parameter. `cell` and `master_seed` are bookkeeping and carry no evidence label.
4. **`direct_s`** is the raw matrix value, not multiplied by `tt_multiplier`. The engine applies the multiplier.
5. **Depot.** The depot is named in `data/processed/locations_v1_meta.json`, key `depot_loc`.
6. **Hotspot ties.** Ranked by weight, descending, then by `loc_id`, ascending.
7. **`content_hash`.** sha256 of `requests.csv` bytes + `fleet.csv` bytes + `json.dumps({"params": params, "replicate": r}, sort_keys=True, separators=(",", ":"))`. The `cell` label is inside `params`, so grid `base/r00` and ladder `M` have identical requests but different hashes.
8. **S0.** S0 is hand-written. Its hash uses the same function, over its stored files.
9. **Imports.** `src/scenario` works both as the package `scenario.*` (tests) and as scripts run from that folder.
