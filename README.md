# BlueJay Night Ride Optimizer

A rolling-horizon mixed-integer optimization framework for evaluating dispatch and routing decisions in Johns Hopkins University's Homewood Blue Jay Night Ride service.

> **Project status:** Proposal and data-acquisition stage. JHU Transportation has offered operational reports and sample data; the team has not yet completed a field-level data audit.

## Research question

Can a rolling-horizon Mixed-Integer Linear Program improve passenger service and shuttle utilization relative to transparent dispatch heuristics, while respecting vehicle capacity, pickup-before-drop-off precedence, wait-time limits, ride-time limits, and vehicle movements already underway?

## Why this problem matters

Blue Jay Night Ride is an on-demand, shared, curb-to-curb transportation service operating around the Homewood campus. Dispatchers must assign requests to vehicles while earlier trips are still in progress. Every routing decision can affect:

- Passenger waiting time
- Passenger ride time and detours
- Vehicle capacity and availability
- Shuttle travel and empty mileage
- The need for overflow transportation

Johns Hopkins describes the service as safety-first, with published pickup and ride-time parameters. This project treats those passenger-service requirements as central constraints rather than optimizing distance alone.

## Mathematical framing

The project is a **dynamic Dial-a-Ride Problem with time windows**, a vehicle-routing problem in which each request has a paired pickup and drop-off.

The proposed node-arc MILP includes:

- Binary route variables indicating whether a vehicle travels between two service events
- Binary assignment variables matching requests to vehicles or an overflow option
- Continuous variables for event times, passenger waiting, ride duration, and vehicle load
- Constraints for route continuity, same-vehicle pickup and drop-off, pickup precedence, vehicle capacity, service time windows, maximum ride time, and committed actions

A service-first objective will prioritize feasible passenger service before minimizing waiting, excess ride time, overflow, and vehicle travel:

~~~text
minimize
    overflow penalty
  + passenger waiting penalty
  + excess ride-time penalty
  + vehicle travel cost
~~~

Because requests arrive during service, the MILP will run inside a rolling-horizon controller:

1. Observe current vehicle states and all known requests.
2. Fix actions that have already started or cannot safely change.
3. Solve the remaining assignment and routing problem under a time limit.
4. Commit the next operational action.
5. Add newly arrived requests and repeat.

## Evaluation

Every dispatch policy will receive the same chronological request stream, fleet availability, starting state, and travel-time assumptions.

Planned comparisons:

1. Reconstructed historical performance, if supported by the data
2. Nearest-feasible vehicle assignment
3. Greedy pickup-and-drop-off insertion
4. Rolling-horizon MILP

Primary outcomes:

- Mean, median, and high-percentile passenger wait time
- Percentage of pickups and rides meeting published service parameters
- Passenger ride time and excess ride time
- Requests served by a shuttle
- Overflow or unserved requests, when identifiable
- Total and estimated empty vehicle distance
- Vehicle utilization and route balance
- Solver time, feasible-solution rate, and optimality gap

The project will use paired historical replay and sensitivity analysis rather than promising an improvement in advance. A result showing that a simple heuristic matches or outperforms the MILP would remain a valid and useful finding.

## Data

The requested de-identified operational fields include:

- Request, assignment, arrival, pickup, and drop-off timestamps
- Pickup and destination zones or suitably protected coordinates
- Party size
- Trip outcome, including cancellation or overflow when available
- Pseudonymous vehicle identifiers, capacities, and in-service periods
- Observed trip time, distance, or vehicle events when shareable

The team will maintain a data dictionary that separates:

- Fields directly supplied by JHU Transportation
- Values derived from supplied data
- Travel-time estimates from a road-network service
- Assumptions or simulated values

If only aggregate reports are available, the team will generate synthetic request streams calibrated to hourly demand and any available origin-destination summaries. Conclusions will clearly identify the role of simulated data.

## Privacy and project boundaries

This repository must not contain:

- Rider names or university identifiers
- Phone numbers or email addresses from trip records
- Driver identities
- Exact residential addresses
- Raw restricted operational data
- Credentials, API keys, or private TransLoc endpoints

Only aggregate statistics and de-identified maps will appear in public outputs. The project is a retrospective decision-support study. It will not control live vehicles, modify TransLoc, or make deployment claims.

## Relationship to prior work

[VehiPathOptimizer](https://github.com/vrbabu9000/VehiPathOptimizer) is an earlier static Capacitated Vehicle Routing Problem project developed by Vignesh Rajesh Babu. It used Python, Google OR-Tools, OSRM distance matrices, and Folium route visualization.

This project extends that experience by adding:

- Paired passenger pickups and drop-offs
- Pickup-before-drop-off precedence
- Passenger wait and ride-time constraints
- Requests revealed dynamically
- Vehicles with existing passengers and committed movements
- An explicit mixed-integer formulation
- Historical replay and comparative evaluation

## Planned repository structure

~~~text
.
├── README.md
├── proposal_context_and_plan.md
├── docs/
│   ├── proposal/
│   ├── presentations/
│   └── references/
├── configs/
├── src/
│   ├── data/
│   ├── network/
│   ├── simulation/
│   ├── baselines/
│   ├── optimization/
│   └── evaluation/
├── tests/
├── notebooks/
└── outputs/
~~~

This layout is planned and will be created as implementation begins. Restricted data will remain outside the public repository.

## Project roadmap

- [x] Select the Homewood Blue Jay Night Ride use case
- [x] Contact JHU Transportation about reports and sample data
- [x] Define the initial DARP and rolling-horizon MILP strategy
- [ ] Audit the supplied data and create a data dictionary
- [ ] Confirm hard constraints and service goals with Transportation staff
- [ ] Build and validate the travel-time matrix
- [ ] Implement the replay simulator
- [ ] Implement nearest-vehicle and insertion baselines
- [ ] Implement and unit-test the static MILP
- [ ] Add rolling-horizon reoptimization
- [ ] Run historical replay and sensitivity experiments
- [ ] Prepare the progress report and final analysis

## Team

**Team FourSight**

- Irfan Setiadi
- Miles Zhou
- Youzhi Zhang
- Vignesh Rajesh Babu

Course: EN.553.602, Research and Design in Mathematics: Data Mining

Johns Hopkins University, Fall 2026

## Documentation

The detailed research context, formulation, execution plan, proposal-ready text, presentation map, risks, and references are available in [proposal_context_and_plan.md](proposal_context_and_plan.md).

## Selected references

- Cordeau, J.-F. (2006). [A Branch-and-Cut Algorithm for the Dial-a-Ride Problem](https://doi.org/10.1287/opre.1060.0283). *Operations Research*, 54(3), 573-586.
- Cordeau, J.-F., and Laporte, G. (2007). [The Dial-a-Ride Problem: Models and Algorithms](https://doi.org/10.1007/s10479-007-0170-8). *Annals of Operations Research*, 153, 29-46.
- Gaul, D., Klamroth, K., and Stiglmayr, M. (2021). [Solving the Dynamic Dial-a-Ride Problem Using a Rolling-Horizon Event-Based Graph](https://doi.org/10.4230/OASIcs.ATMOS.2021.8). *OASIcs ATMOS 2021*, 96, 8:1-8:16.
- Johns Hopkins University Facilities & Real Estate. [Shuttle Services](https://jhfre.jhu.edu/ts/transportation/shuttle-services/).

## AI-use disclosure

OpenAI Codex has been used to organize proposal materials, inspect prior public code, identify relevant literature, and draft initial documentation and mathematical structure. The team is responsible for verifying all citations, equations, assumptions, code, data descriptions, and submitted conclusions against original sources.

## License

A license has not yet been selected. Until the team and any data-owning stakeholders confirm the appropriate release terms, no license should be assumed for project materials or data.
