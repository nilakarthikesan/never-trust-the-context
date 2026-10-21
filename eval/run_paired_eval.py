"""Score complete clean/perturbed prediction pairs; no model calls or credentials.

python3 eval/run_paired_eval.py --predictions /path/to/run.jsonl
python3 eval/run_paired_eval.py --export-prompts /tmp/paired-prompts.jsonl
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from zt_pep.paired_metrics import Prediction, evaluate, validate_cases
from zt_pep.inline import InlinePEP
from zt_pep.model import Entry, RequestContext
from zt_pep.policy import Policy


def export_prompts(cases, path: Path, mode="raw", labels="oracle", policy=None):
    records = []
    for case in cases:
        entries = {e["id"]: e for e in case["entries"]}
        for variant in ("clean", "perturbed"):
            visible = [entries[e] for e in case["variants"][variant]]
            if mode == "raw":
                context = [{"id": e["id"], "source": e["source"], "content": e["content"]}
                           for e in visible]
            else:
                operating_policy = copy.deepcopy(policy or Policy())
                operating_policy.clearance["External"] = case["write_clearance"]
                operating_policy.required_integrity["External"] = case["required_integrity"]
                operating_policy.quarantine_mode = "attribute" if mode == "attribute" else "drop"
                admitted_entries = [Entry(id=e["id"], content=e["content"], source=e["source"],
                                          C=e["C"], I=e["I"] if labels == "oracle" else None)
                                    for e in visible]
                _, admitted = InlinePEP(operating_policy).build_context(
                    admitted_entries, RequestContext(direction="External", capability="comment"))
                context = [{"id": e.id, "source": e.source, "content": e.content,
                            "context_role": "evidence"} for e in admitted.verbatim]
                context += [{"id": e.id, "source": e.source, "content": e.content,
                             "context_role": "unverified_hint_not_evidence"} for e in admitted.attributed]
            # Withhold expected verdict, label oracle and support edges from the model.
            # Source metadata is assumed trusted in this experiment, not in deployment.
            records.append({"pair_id": case["id"], "variant": variant,
                            "mode": mode, "label_source": labels if mode != "raw" else "not_used",
                            "task": case["task"], "context": context,
                            "claim_vocabulary": case["claim_vocabulary"],
                            "response_schema": {"verdict": "approve|request_changes|abstain",
                                                "claims": [{"id": "claim identifier", "evidence_ids": ["entry identifier"]}]}})
    with path.open("w") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=ROOT / "eval/fixtures/paired_review_cases.json")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--predictions", type=Path)
    modes.add_argument("--export-prompts", type=Path)
    parser.add_argument("--mode", choices=("raw", "inline", "attribute"), default="raw")
    parser.add_argument("--labels", choices=("oracle", "heuristic"), default="oracle",
                        help="Only I labels vary; fixture C labels remain fixed in this pilot.")
    parser.add_argument("--policy", type=Path, help="Optional YAML; requires pyyaml. For heuristic PR sources use config/policy.pr-review.yaml.")
    args = parser.parse_args()
    cases = json.loads(args.suite.read_text())["cases"]
    validate_cases(cases)
    if args.export_prompts:
        policy = Policy.from_yaml(str(args.policy)) if args.policy else Policy()
        export_prompts(cases, args.export_prompts, args.mode, args.labels, policy)
        print(f"Exported {2 * len(cases)} prompts from {len(cases)} authored pairs; no model was run.")
        return
    predictions = []
    for number, line in enumerate(args.predictions.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            predictions.append(Prediction.from_dict(json.loads(line)))
        except (ValueError, TypeError) as error:
            raise SystemExit(f"Invalid prediction on line {number}: {error}") from error
    result = evaluate(cases, predictions)
    result["provenance"] = {"suite_sha256": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
                            "predictions_sha256": hashlib.sha256(args.predictions.read_bytes()).hexdigest(),
                            "note": "User-supplied observations; scorer does not run or verify model identity."}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
