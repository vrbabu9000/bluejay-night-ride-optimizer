"""Phase 4 event simulator (milestones M0-M1).

Build contract: docs/technical/scenario_spec.md v0.5 section 17; mathematics: docs/technical/model_design.md v0.3;
settings for this milestone: decision log D-52 and its amendments.

    inputs.py    read the frozen scenario files (read-only, hash-checked) and the travel table
    engine.py    the event engine (referee): clock, same-second order, states, hidden traits
    dispatch.py  dispatcher C: candidate routes per van + route-selection MILP (HiGHS)
    lyft.py      Lyft transfer rules (M0 scope: before the vans come on duty in L4)
    run.py       command line: run a level, write logs and a readable narrative
"""
