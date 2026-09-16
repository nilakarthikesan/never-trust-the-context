"""PDP: apply BLP (no-write-down) and Biba (no-write-up) plus the weighted zero-trust score."""

from __future__ import annotations

from typing import List

from .model import Entry, RequestContext, Decision, EntryDecision
from .policy import Policy, DEFAULT_POLICY
from .labels import label_entry, required_outbound_integrity


def decide_entry(entry: Entry, ctx: RequestContext, policy: Policy = DEFAULT_POLICY,
                 use_ground_truth_C: bool = True) -> EntryDecision:
    """Decide ALLOW / DENY / QUARANTINE for a single candidate entry."""
    label_entry(entry, ctx, policy, use_ground_truth_C=use_ground_truth_C)

    clr = policy.clr_C(ctx.direction)
    lvl = required_outbound_integrity(ctx, policy)

    # BLP no-write-down: C(e) must not exceed recipient clearance.
    conf_ok = entry.C <= clr + policy.eps_C
    # Biba no-write-up: I(e) must meet the artifact's required integrity.
    integ_ok = entry.I >= lvl - policy.eps_I

    # Weighted zero-trust risk (Tian-Song, made explicit).
    wC = policy.w_C.get(ctx.direction, 1.0)
    wI = policy.w_I.get(ctx.direction, 1.0)
    risk = wC * max(0.0, entry.C - clr) + wI * max(0.0, lvl - entry.I)

    if conf_ok and integ_ok:
        decision = Decision.ALLOW
        reason = "passes BLP (no-write-down) and Biba (no-write-up)"
    elif not conf_ok:
        # Confidentiality breach dominates: dropping protects against leakage regardless of integrity.
        decision = Decision.DENY
        reason = f"BLP violation: C={entry.C:.2f} > clr_C({ctx.direction})={clr:.2f}"
    else:
        # conf ok but integrity too low for this artifact
        decision = Decision.QUARANTINE
        reason = f"Biba violation: I={entry.I:.2f} < lvl_I({ctx.direction})={lvl:.2f}"

    # Threshold override: if weighted risk is under theta, allow (tunable leniency).
    if decision is not Decision.ALLOW and risk <= policy.theta.get(ctx.direction, 0.15):
        decision = Decision.ALLOW
        reason += f" | but risk={risk:.3f} <= theta -> ALLOW"

    return EntryDecision(
        entry=entry,
        decision=decision,
        conf_ok=conf_ok,
        integ_ok=integ_ok,
        risk=round(risk, 3),
        reason=reason,
    )


def decide_all(entries: List[Entry], ctx: RequestContext, policy: Policy = DEFAULT_POLICY,
               use_ground_truth_C: bool = True) -> List[EntryDecision]:
    return [decide_entry(e, ctx, policy, use_ground_truth_C=use_ground_truth_C) for e in entries]
