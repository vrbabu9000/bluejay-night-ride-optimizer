"""Lyft transfer rules (scenario_spec §6), evaluated once per epoch after the van solve.

M0 scope: the rules are exercised only where the L4 answer key is hand-checkable, i.e. before the vans come on duty
(the engine's `rule_active_before_s`). The general post-18:15 integration is deferred to M2.

Each rule reads only the board: request time, how long the request has been without an assigned van, and the
predicted van pickup (the plan's ETA, or the tentative ETA of a pending request; None = no feasible van = infinite).
"""
import math

TYPICAL_LYFT_DELAY_S = 480        # the rule's assumption (spec §6 R3), not the hidden per-request delay

RULES = {"R0": None, "R1(10)": ("elapsed", 600), "R1(15)": ("elapsed", 900), "R1u(10)": ("unassigned", 600),
         "R2(15)": ("predicted", 900), "R3(2)": ("van_vs_lyft", 120)}


def fires(rule, tau, t_request, unassigned_since, predicted_pickup, lag_s):
    spec = RULES[rule]
    if spec is None:
        return False
    kind, theta = spec
    pred = math.inf if predicted_pickup is None else predicted_pickup
    if kind == "elapsed":
        return tau - t_request >= theta
    if kind == "unassigned":
        return unassigned_since is not None and tau - unassigned_since >= theta
    if kind == "predicted":
        return pred - t_request > theta
    if kind == "van_vs_lyft":
        return pred > tau + lag_s + TYPICAL_LYFT_DELAY_S + theta
    raise ValueError(kind)
