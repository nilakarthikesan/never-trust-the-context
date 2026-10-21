"""Join private pilot pairing metadata to an existing external-prediction score.

This reads observations; it does not execute models or infer action performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from zt_pep.correction_pilot import paired_analysis


def analyze_run(metrics_path, manifest_path, output_path, bootstrap_samples=2000, seed=1729):
    """Save private analysis beside scored results, never inside a public export."""
    metrics_path, manifest_path, output_path = map(Path, (metrics_path, manifest_path, output_path))
    for ancestor in output_path.resolve().parents:
        if (ancestor / "export_manifest.json").is_file():
            raise ValueError("paired analysis output must stay outside the public prompt export directory")
    metrics_bytes, manifest_bytes = metrics_path.read_bytes(), manifest_path.read_bytes()
    result = paired_analysis(json.loads(metrics_bytes), json.loads(manifest_bytes), bootstrap_samples, seed)
    result["input_sha256"] = {"metrics": hashlib.sha256(metrics_bytes).hexdigest(),
                              "private_manifest": hashlib.sha256(manifest_bytes).hexdigest()}
    with output_path.open("x") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", required=True, type=Path, help="metrics.json produced by run_correction_eval.py score")
    parser.add_argument("--manifest", type=Path, default=ROOT / "eval/fixtures/correction_pilot_manifest.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()
    try:
        result = analyze_run(args.metrics, args.manifest, args.output, args.bootstrap_samples, args.seed)
        print(json.dumps({"artifact_kind": result["artifact_kind"], "n_bases": result["n_bases"],
                          "n_packets": result["n_packets"], "n_claims": result["n_claims"],
                          "output": str(args.output)}, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Paired analysis input error: {error}\n")


if __name__ == "__main__":
    main()
