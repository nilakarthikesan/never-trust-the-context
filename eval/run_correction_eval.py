"""Export correction-scope prompts and score externally supplied JSONL responses.

Offline only: no model API, semantic parser, executable review task, or action
evaluation. Export withholds private world labels and the authored claim AST.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from correction_scope_demo import DEFAULT_SUITE, audit_packet, load_packets, public_packet
from zt_pep.correction_eval import evaluate, parse_predictions, response_schema

FORMAT = "correction-scope-external-v1"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def code_hashes():
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()) for path in (
        Path(__file__).resolve(), ROOT / "eval/correction_scope_demo.py",
        ROOT / "src/zt_pep/correction_eval.py")}


def build_materials(packets):
    prompts, reference, allowed_records = [], {}, {}
    for packet in packets:
        result = audit_packet(packet)
        prompt = public_packet(packet)
        prompt["response_schema"] = response_schema()
        prompt["evidence_policy"] = {
            "identity": "Source-owner and event-issuer metadata are trusted; notice wording cannot override them.",
            "update_authority": "Only the source owner may update its own exact target_record_id, and the target must be active.",
            "retraction": "An authorized retract archives the exact target; it does not erase history or change any other record.",
            "supersession": "An authorized supersede archives the target and adds an active replacement with a new record_id, the same source_owner, and the same proposition_id. Reject the whole update if these conditions fail.",
            "failed_update": "A rejected update changes no canonical record; it supplies no replacement endorsement.",
            "support_admission": "Only active records from owners whose may_support includes the proposition count as current admissible support. This restriction does not erase their historical assertions or their own current endorsements.",
            "world_truth": "Source assertions and admissible support are not world-truth guarantees; withdrawal alone is not refutation.",
        }
        prompt["scope_definitions"] = {
            "historical_assertion": "Whether the source made the specified assertion in the historical record referred to by the claim. Both active and archived records can establish this; a replacement does not rewrite the old assertion.",
            "current_endorsement": "The source owner's current attestation of the proposition/value, using any active record by that owner. It is not limited to the original record, and may_support does not govern this source-level question.",
            "current_support": "Current admissible support for the proposition/value, using active records admitted by may_support. A separately surviving record can support the claim after another record is withdrawn.",
        }
        prompt["response_instructions"] = (
            "Return one JSON object matching response_schema, with every listed claim exactly once. "
            "Extract each claim's scope from its text; no gold claim scopes are provided. "
            "List all eligible supporting and opposing records under that scope. "
            "Use empty lists when no records qualify. World truth is not the target."
        )
        prompt["status_definitions"] = {
            "supported": "At least one eligible supporting record and no opposing record.",
            "opposed": "At least one eligible opposing record and no supporting record.",
            "conflicted": "Both supporting and opposing eligible records exist.",
            "unsupported": "Neither supporting nor opposing eligible records exist.",
        }
        prompts.append(prompt)
        packet_id = prompt["packet_id"]
        allowed_records[packet_id] = {r["record_id"] for r in packet["records"]}
        allowed_records[packet_id].update(
            e["replacement"]["record_id"] for e in packet["events"] if "replacement" in e)
        gold = {c["claim_id"]: c for c in result["claims"]}
        for original, visible in zip(packet["claims"], prompt["claims"]):
            row = gold[original["claim_id"]]
            reference[packet_id, visible["claim_id"]] = {
                field: row[field] for field in
                ("scope", "status", "supporting_records", "opposing_records")}
    return prompts, reference, allowed_records


def prompt_bytes(prompts):
    return ("".join(json.dumps(p, sort_keys=True) + "\n" for p in prompts)).encode()


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def export_run(suite, output_dir):
    suite = Path(suite)
    prompts, reference, _ = build_materials(load_packets(suite))
    encoded = prompt_bytes(prompts)
    manifest = {
        "format": FORMAT,
        "artifact_kind": "synthetic prompt export; no model execution",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "suite_sha256": sha256(suite.read_bytes()), "prompts_sha256": sha256(encoded),
        "n_packets": len(prompts), "n_claims": len(reference),
        "scope_condition": "extract from text; gold claim AST withheld",
        "code_sha256": code_hashes(),
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "prompts.jsonl").write_bytes(encoded)
    _write_json(output_dir / "export_manifest.json", manifest)
    return manifest


def score_run(suite, export_dir, predictions_path, output_dir,
              origin="unspecified", source_label="unspecified"):
    suite, export_dir = Path(suite), Path(export_dir)
    predictions_path, output_dir = Path(predictions_path), Path(output_dir)
    if output_dir.resolve() == export_dir.resolve() or export_dir.resolve() in output_dir.resolve().parents:
        raise ValueError("score output must be outside the public prompt export directory")
    manifest = json.loads((export_dir / "export_manifest.json").read_text())
    if manifest.get("format") != FORMAT:
        raise ValueError("unsupported export manifest format")
    if sha256(suite.read_bytes()) != manifest["suite_sha256"]:
        raise ValueError("suite changed since prompt export; re-export before scoring")
    if code_hashes() != manifest["code_sha256"]:
        raise ValueError("oracle/export/scoring code changed since export; re-export before scoring")
    prompts, reference, allowed = build_materials(load_packets(suite))
    saved_prompts = (export_dir / "prompts.jsonl").read_bytes()
    if sha256(saved_prompts) != manifest["prompts_sha256"] or saved_prompts != prompt_bytes(prompts):
        raise ValueError("public prompts do not match their manifest and current suite")
    predictions_bytes = predictions_path.read_bytes()
    predictions = parse_predictions(predictions_bytes.decode("utf-8"))
    metrics = evaluate(reference, predictions, allowed)
    provenance = {
        "format": FORMAT,
        "artifact_kind": "offline replay/scoring of supplied observations; no model/action execution",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "suite_sha256": manifest["suite_sha256"], "prompts_sha256": manifest["prompts_sha256"],
        "predictions_sha256": sha256(predictions_bytes),
        "export_manifest_sha256": sha256((export_dir / "export_manifest.json").read_bytes()),
        "code_sha256": code_hashes(),
        "declared_prediction_origin": origin, "declared_source_label": source_label,
        "origin_verification": "not independently verified",
        "scope_condition": "externally extracted scopes; gold used only in private scoring",
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "predictions.jsonl").write_bytes(predictions_bytes)
    _write_json(output_dir / "metrics.json", metrics)
    _write_json(output_dir / "run_manifest.json", provenance)
    return metrics, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="write public prompts and a frozen-input manifest")
    export.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    export.add_argument("--output-dir", type=Path, required=True)
    score = commands.add_parser("score", help="validate and score complete external JSONL responses")
    score.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    score.add_argument("--export-dir", type=Path, required=True)
    score.add_argument("--predictions", type=Path, required=True)
    score.add_argument("--output-dir", type=Path, required=True)
    score.add_argument("--prediction-origin", choices=("unspecified", "external_model", "human", "oracle_diagnostic"),
                       default="unspecified")
    score.add_argument("--source-label", default="unspecified")
    args = parser.parse_args()
    try:
        if args.command == "export":
            manifest = export_run(args.suite, args.output_dir)
            print(f"Synthetic export: {manifest['n_packets']} packets / {manifest['n_claims']} claims. "
                  "No model was run.")
        else:
            metrics, _ = score_run(args.suite, args.export_dir, args.predictions, args.output_dir,
                                   args.prediction_origin, args.source_label)
            print(json.dumps({"artifact_kind": metrics["artifact_kind"],
                              "declared_prediction_origin": args.prediction_origin,
                              "summary": metrics["summary"]}, indent=2, sort_keys=True))
    except (ValueError, OSError, UnicodeError, KeyError) as error:
        parser.exit(2, f"Correction evaluation input error: {error}\n")


if __name__ == "__main__":
    main()
