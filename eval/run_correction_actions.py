#!/usr/bin/env python3
"""Plan or explicitly run bounded action agents; never send private grader inputs."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from correction_scope_demo import audit_packet, load_packets
from run_correction_models import config_from, model_options, read_inputs
from zt_pep.correction_actions import CONDITIONS, align_cases, build_action_messages, run_action_experiment
from zt_pep.correction_pilot import SandboxSession
from zt_pep.correction_runner import HTTPAdapter, canonical


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "run"):
        sub = subcommands.add_parser(name)
        sub.add_argument("--prompts", required=True)
        sub.add_argument("--suite", required=True)
        sub.add_argument("--private-manifest", required=True)
        sub.add_argument("--condition", choices=CONDITIONS, required=True)
        sub.add_argument("--packet-limit", type=int)
        model_options(sub)
        if name == "run":
            sub.add_argument("--output-dir", required=True)
            sub.add_argument("--max-requests", type=int, required=True)
            sub.add_argument("--max-cost-usd", type=float, required=True)
            sub.add_argument("--allow-network", action="store_true")
            sub.add_argument("--api-key-env", default="CORRECTION_API_KEY")
    args = parser.parse_args(argv)
    prompts, data = read_inputs(args.prompts)
    if args.packet_limit is not None:
        if args.packet_limit < 1:
            raise ValueError("packet limit must be positive")
        prompts = prompts[:args.packet_limit]
        data = b"".join(canonical(p) for p in prompts)
    suite = load_packets(args.suite)
    manifest = json.loads(Path(args.private_manifest).read_text(encoding="utf-8"))
    config = config_from(args)
    if args.command == "plan":
        cases = align_cases(prompts, suite, manifest)
        input_estimate = 0
        for prompt, base, _, packet in cases:
            task = SandboxSession(base, packet, audit_packet).public_task()
            messages = build_action_messages(prompt, task, args.condition)
            body = canonical({"model": config.model, "messages": messages,
                              "temperature": config.temperature, "max_tokens": config.max_output_tokens})
            # Later requests can contain one real check transcript plus earlier
            # choices. This is a planning allowance, not a guaranteed token bound.
            input_estimate += 3 * (len(body) + 1024) + 20000
        maximum = len(cases) * 3  # Includes retries: the packet cap is enforced at transport-attempt level.
        print(json.dumps({"network_requests_made": 0, "condition": args.condition,
                          "n_packets": len(cases), "maximum_provider_attempts": maximum,
                          "declared_reservation_estimate_usd": (
                              input_estimate * config.input_price_per_million
                              + maximum * config.max_output_tokens * config.output_price_per_million) / 1_000_000,
                          "estimate_policy": "byte-based three-call planning allowance; actual acquired-check transcript varies; each live request is budget-reserved before sending",
                          "private_checks_or_truth_in_model_input": False}, indent=2))
        return 0
    if not args.allow_network:
        raise ValueError("run requires --allow-network; use plan for zero-network preparation")
    key = os.environ.get(args.api_key_env)
    if key is None and args.api_key_env == "CORRECTION_API_KEY":
        key = os.environ.get("OPENAI_API_KEY", "")
    summary = run_action_experiment(prompts, suite, manifest, audit_packet, args.output_dir, config,
                                    condition=args.condition, max_requests=args.max_requests,
                                    max_cost_usd=args.max_cost_usd,
                                    adapter=HTTPAdapter(config, key or ""), network=True, input_bytes=data)
    print(json.dumps(summary, indent=2))
    return 0 if summary["complete"] else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        print("bounded action runner: " + str(error), file=sys.stderr)
        sys.exit(2)
