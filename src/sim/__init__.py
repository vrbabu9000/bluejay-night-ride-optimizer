"""Phase 4 event simulator (milestones M0-M1).

Build contract: docs/technical/scenario_spec.md v0.5 section 17; mathematics: docs/technical/model_design.md v0.3;
settings for this milestone: decision log D-52 and its amendments.

    inputs.py    read the frozen scenario files (read-only, hash-checked) and the travel table
    engine.py    the event engine (referee): clock, same-second order, states, hidden traits
    dispatch.py  dispatcher C: candidate routes per van + route-selection MILP (HiGHS)
    lyft.py      Lyft transfer rules (all evening since M2; the M0 window stays selectable)
    compare.py   D-53 comparison of pending-price formulations
    m2_report.py M2 report: the Lyft rules with C over the whole L4 evening
    run.py       command line: run a level, write logs and a readable narrative
"""
