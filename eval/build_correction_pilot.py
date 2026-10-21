"""Build/validate the provisional authored pilot; exercise a bounded sandbox.

Offline software/data work only. No model API, agent action run, or human
validation is performed by these commands.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from correction_scope_demo import audit_packet
from zt_pep.correction_pilot import SandboxSession, build_pilot, run_reference_policies, validate_pilot

DEFAULT_SUITE = ROOT / "eval/fixtures/correction_pilot.json"
DEFAULT_MANIFEST = ROOT / "eval/fixtures/correction_pilot_manifest.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build", help="write the deterministic authored fixtures; refuse existing files")
    commands.add_parser("validate", help="validate fixture/oracle constraints and execute 72 bounded checks")
    policies = commands.add_parser("reference-policies", help="execute four NONLLM diagnostic policies through the bounded tools")
    policies.add_argument("--output", type=Path, required=True)
    sandbox = commands.add_parser("sandbox", help="exercise one local tool session, not an agent result")
    sandbox.add_argument("--base-id", required=True, help="private manifest base_id")
    sandbox.add_argument("--variant", choices=("unchanged", "update"), default="update")
    sandbox.add_argument("--verify", action="store_true")
    sandbox.add_argument("--action", choices=("approve", "decline"), default="decline")
    args = parser.parse_args()
    try:
        if args.command == "build":
            suite, manifest = build_pilot()
            result = validate_pilot(suite, manifest, audit_packet)
            if args.suite.exists() or args.manifest.exists():
                raise FileExistsError("refusing to overwrite an authored suite or manifest")
            for path, value in ((args.suite, suite), (args.manifest, manifest)):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        suite, manifest = (json.loads(path.read_text()) for path in (args.suite, args.manifest))
        result = validate_pilot(suite, manifest, audit_packet)
        if args.command == "reference-policies":
            policy_results = run_reference_policies(suite, manifest, audit_packet)
            policy_results["input_sha256"] = {"suite": hashlib.sha256(args.suite.read_bytes()).hexdigest(),
                                               "private_manifest": hashlib.sha256(args.manifest.read_bytes()).hexdigest()}
            policy_results["code_sha256"] = {str(Path(path).relative_to(ROOT)): hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                               for path in (inspect.getfile(run_reference_policies), inspect.getfile(audit_packet), __file__)}
            with args.output.open("x") as stream:
                stream.write(json.dumps(policy_results, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"artifact_kind": policy_results["artifact_kind"], "model_calls": 0,
                              "summary": policy_results["summary"]}, indent=2, sort_keys=True))
            return
        if args.command == "validate":
            # A reproducible build check detects accidental edits to the frozen
            # initial design. A future deliberately revised suite needs a version.
            generated_suite, generated_manifest = build_pilot()
            if suite != generated_suite or manifest != generated_manifest:
                raise ValueError("saved pilot differs from the deterministic authored v1 design")
            print(json.dumps(result, indent=2, sort_keys=True))
            return
        selected = [b for b in manifest["bases"] if b["base_id"] == args.base_id]
        if len(selected) != 1:
            raise ValueError("unknown or duplicate base id")
        base = selected[0]
        packet_id = base["packets"][args.variant]["internal_packet_id"]
        packet = next(p for p in suite["packets"] if p["packet_id"] == packet_id)
        session = SandboxSession(base, packet, audit_packet)
        trace = [{"tool": "verify", "result": session.verify()}] if args.verify else []
        trace.append({"tool": args.action, "result": getattr(session, args.action)()})
        print(json.dumps({"artifact_kind": "scripted sandbox software demonstration; no model/agent evaluation",
                          "trace": trace, "private_grade": session.private_grade()}, indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f"Pilot input error: {error}\n")


if __name__ == "__main__":
    main()
