"""Run the CI-Work evaluation comparing baselines against the zero-trust PEP.

Offline demo (no API key needed):
    python eval/run_eval.py --source fixture --judge keyword

Real CI-Work data (needs the LLM judge + API access):
    python eval/run_eval.py --source formatted \
        --path data/ACV/misc/CI-Work/data/trajectory/<model>/naive/ess4_sen4/formatted_trajectory.json \
        --judge llm

Defenses compared:
    - undefended : the agent's raw final action (CI-Work baseline)
    - zt_pep      : our Biba+BLP zero-trust PEP (redact mode)
    - zt_pep_deny : PEP in deny+explain mode (privacy upper bound)
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zt_pep.policy import DEFAULT_POLICY, Policy
from zt_pep.pep import PolicyEnforcementPoint, KeywordJudge
from zt_pep.metrics import score_case, aggregate
from zt_pep.labels import label_entry

from ciwork_adapter import load_fixture, load_formatted_trajectory, Case


def build_judge(kind: str):
    if kind == "keyword":
        return KeywordJudge()
    if kind == "llm":  # pragma: no cover
        from openai import OpenAI
        from zt_pep.pep import LLMJudge
        client = OpenAI()
        model = os.environ.get("CIWORK_JUDGE_MODEL", "gpt-5.2")
        return LLMJudge(client, model)
    raise ValueError(kind)


def eval_defense(cases, judge, policy: Policy, mode: str, apply_pep: bool):
    scores = []
    for c in cases:
        # ensure labels populated for metrics (integrity axis needs I(e))
        for e in c.all_entries():
            label_entry(e, c.ctx, policy)
        if apply_pep:
            pep = PolicyEnforcementPoint(policy=policy, mode=mode)
            res = pep.enforce(c.undefended_action, c.all_entries(), c.ctx)
            action = res.sanitized_action
        else:
            action = c.undefended_action
        scores.append(score_case(action, c.sensitive, c.essential, c.ctx, judge, policy,
                                 c.outline, corrupting=c.corrupting))
    return aggregate(scores)


def fmt_row(name, agg):
    p = agg.as_percent()
    return f"{name:<14} LR={p['LR%']:>6}  VR={p['VR%']:>6}  CR={p['CR%']:>6}  IL={p['IL%']:>6}  IVR={p['IVR%']:>6}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["fixture", "formatted"], default="fixture")
    ap.add_argument("--path", default=os.path.join(os.path.dirname(__file__), "fixtures", "cases.json"))
    ap.add_argument("--judge", choices=["keyword", "llm"], default="keyword")
    ap.add_argument("--policy", default=None,
                    help="path to a policy YAML; omit to use the built-in defaults")
    ap.add_argument("--per-case", action="store_true", help="also print a row per case")
    args = ap.parse_args()

    cases = load_fixture(args.path) if args.source == "fixture" else load_formatted_trajectory(args.path)
    judge = build_judge(args.judge)
    policy = Policy.from_yaml(args.policy) if args.policy else DEFAULT_POLICY

    label = os.path.basename(args.policy) if args.policy else "defaults"
    print(f"\nCI-Work eval  |  source={args.source}  judge={args.judge}  "
          f"cases={len(cases)}  policy={label}")
    print("metrics: LR/VR/CR = CI-Work confidentiality;  IL/IVR = new Biba integrity axis  (LR/VR/IL/IVR lower better, CR higher better)\n")

    rows = [
        ("undefended", eval_defense(cases, judge, policy, mode="allow", apply_pep=False)),
        ("zt_pep", eval_defense(cases, judge, policy, mode="redact", apply_pep=True)),
        ("zt_pep_deny", eval_defense(cases, judge, policy, mode="deny_explain", apply_pep=True)),
    ]
    for name, agg in rows:
        print("  " + fmt_row(name, agg))
    print()

    if args.per_case:
        for c in cases:
            print(f"  --- {c.name}  ({c.ctx.direction}"
                  f"{'/' + c.ctx.capability if c.ctx.capability else ''})"
                  f"  ess={len(c.essential)} sens={len(c.sensitive)} corr={len(c.corrupting)}")
            for label_, mode, apply_pep in (("undefended", "allow", False),
                                            ("zt_pep", "redact", True)):
                agg = eval_defense([c], judge, policy, mode=mode, apply_pep=apply_pep)
                print("      " + fmt_row(label_, agg))
        print()


if __name__ == "__main__":
    main()
