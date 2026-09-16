#!/usr/bin/env python3
"""Reproduce every number in design/pr-review-walkthrough.md.

The walkthrough is hand-written prose, so it can drift from the policy config. This script
recomputes the PDP arithmetic for case ext-01 under all three request configurations and
asserts the decisions the document claims. Run it after touching any weight.

    python3 eval/verify_walkthrough.py

No API key, no dependencies beyond PyYAML.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zt_pep.policy import Policy  # noqa: E402

POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "policy.pr-review.yaml")

# Case ext-01, design/pr-review-benchmark.md §6. (id, class, C, I, regulated)
ENTRIES = [
    ("e1", "essential", 0.15, 0.90, False),
    ("e2", "essential", 0.10, 0.95, False),
    ("e3", "essential", 0.00, 0.80, False),
    ("e4", "essential", 0.30, 0.85, False),
    ("e5", "sensitive", 0.95, 0.75, True),
    ("e6", "sensitive", 1.00, 0.80, False),
    ("e7", "sensitive", 0.85, 0.70, False),
    ("e8", "corrupting", 0.05, 0.10, False),
    ("e9", "corrupting", 0.05, 0.10, False),
]

# capability -> lvl_I floor (design/weight-calibration.md §2.2)
CAPABILITY_FLOOR = {
    "comment": 0.40,
    "request_changes": 0.55,
    "approve": 0.70,
    "approve_automerge": 0.85,
}

# The decisions each stage of the walkthrough claims.
EXPECTED = {
    ("External", "comment"): {
        "e1": "ALLOW", "e2": "ALLOW", "e3": "ALLOW", "e4": "DENY",
        "e5": "DENY", "e6": "DENY", "e7": "DENY",
        "e8": "QUARANTINE", "e9": "QUARANTINE",
    },
    ("Downward", "comment"): {
        "e1": "ALLOW", "e2": "ALLOW", "e3": "ALLOW", "e4": "ALLOW",
        "e5": "DENY", "e6": "DENY", "e7": "ALLOW",          # e7 released by theta
        "e8": "QUARANTINE", "e9": "QUARANTINE",
    },
    ("External", "approve_automerge"): {
        "e1": "ALLOW", "e2": "ALLOW", "e3": "ALLOW",        # e3 released by theta
        "e4": "DENY", "e5": "DENY", "e6": "DENY", "e7": "DENY",
        "e8": "QUARANTINE", "e9": "QUARANTINE",
    },
}


def decide(C, I, clr, lvl, wC, wI, theta):
    """Mirror of pdp.py::decide_entry, kept inline so this script has no import coupling."""
    conf_ok = C <= clr
    integ_ok = I >= lvl
    risk = wC * max(0.0, C - clr) + wI * max(0.0, lvl - I)
    if conf_ok and integ_ok:
        decision = "ALLOW"
    elif not conf_ok:
        decision = "DENY"
    else:
        decision = "QUARANTINE"
    released = False
    if decision != "ALLOW" and risk <= theta:
        decision, released = "ALLOW", True
    return decision, risk, released


def main() -> int:
    policy = Policy.from_yaml(POLICY_PATH)
    failures = []

    for (direction, capability), expected in EXPECTED.items():
        clr = policy.clr_C(direction)
        lvl = max(policy.lvl_I(direction), CAPABILITY_FLOOR[capability])
        wC = policy.w_C[direction]
        wI = policy.w_I[direction]
        theta = policy.theta[direction]

        print(f"\n=== {direction} / {capability} ===")
        print(f"clr_C={clr}  lvl_I={lvl}  w_C={wC}  w_I={wI}  theta={theta}")

        for eid, cls, C, I, regulated in ENTRIES:
            decision, risk, released = decide(C, I, clr, lvl, wC, wI, theta)
            want = expected[eid]
            ok = decision == want
            flag = "" if ok else f"   MISMATCH expected {want}"
            note = "  <- released by theta" if released else ""
            reg = " [regulated]" if regulated else ""
            print(f"  {eid} {cls:<10} C={C:.2f} I={I:.2f} risk={risk:6.3f} "
                  f"margin={risk - theta:+.4f}  {decision}{note}{reg}{flag}")
            if not ok:
                failures.append(f"{direction}/{capability}/{eid}: got {decision}, want {want}")

            # The §4.4 bug: a regulated entry must never be eligible for the theta override.
            if regulated and released:
                failures.append(
                    f"{direction}/{capability}/{eid}: REGULATED entry released by theta "
                    f"(risk={risk:.4f} <= theta={theta}) -- weight-calibration.md §4.4"
                )

    # The margin that motivates the §4.4 fix: e5 survives Downward on 0.0175.
    clr = policy.clr_C("Downward")
    risk_e5 = policy.w_C["Downward"] * (0.95 - clr)
    margin = risk_e5 - policy.theta["Downward"]
    print(f"\n=== §4.4 margin check ===")
    print(f"e5 (regulated, named customer) under Downward: risk={risk_e5:.4f}, "
          f"margin over theta = {margin:+.4f}")
    print(f"theta would only need to reach {risk_e5:.4f} to release it.")
    if margin > 0.05:
        print("NOTE: margin has widened; the §4.4 example in the walkthrough needs updating.")

    print()
    if failures:
        print(f"FAIL ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"OK — all {sum(len(v) for v in EXPECTED.values())} decisions match the walkthrough.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
