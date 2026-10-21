"""Summarize observed runs without turning missing predictions into model results.

The private evidence oracle is joined only here, after provider outputs are saved.
Constrained candidate emission is a diagnostic, not free-form regeneration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))
from run_correction_eval import build_materials
from correction_scope_demo import load_packets
from zt_pep.correction_eval import evaluate, parse_predictions
from zt_pep.correction_runner import _completion, build_messages, parse_auxiliary, reconstruction_candidates


def sha(data):
    return hashlib.sha256(data).hexdigest()


def positive_support_gold(private_packet, public_packet, reference):
    candidates = reconstruction_candidates(public_packet)
    queries = [c for c in private_packet["claims"] if c["kind"] == "current_support"]
    if (len(candidates) != 1 or len(queries) != 1 or queries[0]["value"] is not True
            or queries[0]["proposition_id"] != candidates[0]["proposition_id"]):
        raise ValueError("reconstruction diagnostic requires one positive query for the same proposition")
    public_query = next(c for a, c in zip(private_packet["claims"], public_packet["claims"])
                        if a["claim_id"] == queries[0]["claim_id"])
    return candidates[0], reference[public_packet["packet_id"], public_query["claim_id"]]


def summarize(run_dir, suite):
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "run_manifest.json").read_bytes())
    run = json.loads((run_dir / "run_summary.json").read_bytes())
    inputs = (run_dir / "public_inputs.jsonl").read_bytes()
    predictions = (run_dir / "predictions.jsonl").read_bytes()
    private_packets = load_packets(Path(suite))
    prompts, reference, allowed = build_materials(private_packets)
    if (sha(inputs) != manifest["inputs_sha256"]
            or [json.loads(s) for s in inputs.decode().splitlines() if s.strip()] != prompts
            or sha(predictions) != run["predictions_sha256"]):
        raise ValueError("saved inputs/predictions do not match manifest and suite")
    parsed = parse_predictions(predictions.decode())
    if len(parsed) != run["n_valid"] or len(prompts) != run["n_packets"]:
        raise ValueError("saved output coverage does not match run summary")
    complete = len(parsed) == len(prompts)
    if complete != run["complete"]:
        raise ValueError("inconsistent complete flag")
    report = {
        "artifact_kind": "saved-run coverage and oracle diagnostics; missing outputs never imputed",
        "origin": manifest["origin"],
        "condition": manifest["condition"], "requested_model": manifest["config"]["model"],
        "n_expected_packets": len(prompts), "n_valid_packets": len(parsed),
        "prediction_coverage": len(parsed) / len(prompts), "complete": complete,
        "outcome_counts": dict(Counter(row["state"] for row in run["outcomes"])),
        "provider_requests": run["provider_requests"],
        "reported_cost_usd_at_declared_rates": run["reported_cost_usd_at_declared_rates"],
        "unknown_failure_reservations_are_not_confirmed_charges": True,
        "model_metrics": evaluate(reference, parsed, allowed) if complete else None,
        "input_sha256": {"run_manifest": sha((run_dir / "run_manifest.json").read_bytes()),
                         "run_summary": sha((run_dir / "run_summary.json").read_bytes()),
                         "suite": sha(Path(suite).read_bytes())},
    }
    if manifest["condition"] == "regeneration_audit":
        rows = []
        for private_packet, packet in zip(private_packets, prompts):
            directory = run_dir / "traces" / sha(packet["packet_id"].encode())[:24]
            path = directory / "auxiliary.json"
            if not path.exists():
                continue
            observed = parse_auxiliary(path.read_text(), packet, "regeneration_audit")
            result_path = directory / "probe.result.json"
            if not result_path.exists():
                raise ValueError("auxiliary observation lacks a saved probe result")
            result = json.loads(result_path.read_bytes())
            if result["request_file"] != "probe.request.json" or result["response_file"] != "probe.response.json":
                raise ValueError("unexpected probe trace filename")
            request = (directory / result["request_file"]).read_bytes()
            raw = (directory / result["response_file"]).read_bytes()
            if sha(request) != result["request_sha256"] or sha(raw) != result["response_sha256"]:
                raise ValueError("probe request/response hash mismatch")
            if json.loads(request)["messages"] != build_messages(packet, "regeneration_audit"):
                raise ValueError("probe request does not match public packet")
            if parse_auxiliary(_completion(raw)[0], packet, "regeneration_audit") != observed:
                raise ValueError("saved auxiliary differs from provider response")
            emitted = {row["candidate_id"] for row in observed["emitted_candidates"]}
            # This pilot has exactly one proposition and one positive current-support query.
            # Reject generalizations that would silently join a candidate to another claim.
            candidate, gold = positive_support_gold(private_packet, packet, reference)
            rows.append({"packet_id": packet["packet_id"],
                         "candidate_id": candidate["candidate_id"],
                         "emitted": candidate["candidate_id"] in emitted,
                         "current_support_status": gold["status"]})
        report["reconstruction_diagnostic"] = {
            "measurement": "observed constrained bare-proposition selection; not paper reproduction",
            "n_expected": len(prompts), "n_observed": len(rows),
            "by_support_status": {
                status: {"n": sum(row["current_support_status"] == status for row in rows),
                         "emitted": sum(row["current_support_status"] == status and row["emitted"] for row in rows)}
                for status in ("supported", "unsupported", "opposed", "conflicted")},
            "rows": rows,
            "limitations": "Public candidate anchors the claim. Historical attribution is not a bare-proposition candidate. No action consequence is inferred.",
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--suite", type=Path, default=ROOT / "eval/fixtures/correction_pilot.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        for parent in (args.output.resolve().parent, *args.output.resolve().parents):
            if (parent / "export_manifest.json").exists():
                raise ValueError("reference-bearing analysis cannot be written into public prompt exports")
        result = summarize(args.run_dir, args.suite)
        with args.output.open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
        print(json.dumps({key: result[key] for key in ("complete", "n_expected_packets", "n_valid_packets", "outcome_counts")}))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
