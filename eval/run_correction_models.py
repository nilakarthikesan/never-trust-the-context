#!/usr/bin/env python3
"""Budgeted public-input model runs, offline replay, and explicitly non-LLM controls."""
import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from zt_pep.correction_runner import (  # noqa: E402
    CONDITIONS, HEURISTICS, HTTPAdapter, ModelConfig, ReplayAdapter, canonical,
    digest, heuristic_predictions, now, plan_experiment, run_experiment, validate_public,
)


def read_inputs(path):
    data = Path(path).read_bytes()
    packets = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
    validate_public(packets)
    return packets, data


def model_options(parser):
    parser.add_argument("--model", default=os.environ.get("CORRECTION_MODEL"))
    parser.add_argument("--base-url", default=os.environ.get("CORRECTION_API_BASE_URL")
                        or os.environ.get("OPENAI_BASE_URL"))
    parser.add_argument("--input-price-per-million", type=float, required=True)
    parser.add_argument("--output-price-per-million", type=float, required=True)
    parser.add_argument("--max-output-tokens", type=int, default=1000)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=2)


def config_from(args):
    if not args.model or not args.base_url:
        raise ValueError("provide an explicit model and base URL using flags or CORRECTION_MODEL/CORRECTION_API_BASE_URL")
    return ModelConfig(args.model, args.base_url, args.input_price_per_million,
                       args.output_price_per_million, args.max_output_tokens,
                       args.temperature, args.timeout_seconds, args.max_retries)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="dry run: no provider requests")
    plan.add_argument("--prompts", required=True)
    plan.add_argument("--condition", choices=CONDITIONS + ("all",), default="all")
    model_options(plan)
    run = commands.add_parser("run", help="explicitly authorized HTTP run or hash-checked resume")
    run.add_argument("--prompts", required=True)
    run.add_argument("--output-dir", required=True)
    run.add_argument("--condition", choices=CONDITIONS, required=True)
    run.add_argument("--max-requests", type=int, required=True)
    run.add_argument("--max-cost-usd", type=float, required=True)
    run.add_argument("--allow-network", action="store_true")
    run.add_argument("--api-key-env", default="CORRECTION_API_KEY",
                     help="environment variable name; OPENAI_API_KEY is the default fallback")
    model_options(run)
    replay = commands.add_parser("replay", help="replay exact saved requests/responses, without network")
    replay.add_argument("--source-dir", required=True)
    replay.add_argument("--output-dir", required=True)
    control = commands.add_parser("heuristic", help="transparent deterministic non-LLM control")
    control.add_argument("--prompts", required=True)
    control.add_argument("--output-dir", required=True)
    control.add_argument("--method", choices=HEURISTICS, required=True)
    args = parser.parse_args(argv)
    if args.command == "replay":
        source = Path(args.source_dir)
        manifest = json.loads((source / "run_manifest.json").read_text(encoding="utf-8"))
        packets, data = read_inputs(source / "public_inputs.jsonl")
        summary = run_experiment(packets, args.output_dir, ModelConfig(**manifest["config"]),
                                 condition=manifest["condition"], adapter=ReplayAdapter(source),
                                 input_bytes=data, network=False, **manifest["budget_limits"])
        print(json.dumps(summary, indent=2))
        return 0 if summary["complete"] else 2
    packets, data = read_inputs(args.prompts)
    if args.command == "heuristic":
        directory = Path(args.output_dir)
        directory.mkdir(parents=True, exist_ok=False)
        predictions = heuristic_predictions(packets, args.method)
        encoded = b"".join(canonical(p) for p in predictions)
        (directory / "predictions.jsonl").write_bytes(encoded)
        manifest = {"origin": "deterministic_heuristic_NOT_LLM", "method": args.method,
                    "created_at_utc": now(), "inputs_sha256": digest(data),
                    "predictions_sha256": digest(encoded), "n_packets": len(packets),
                    "limitations": "lexical scope/negation and first-proposition control; initial-records ignores all updates; latest-notice ignores update authority"}
        (directory / "run_manifest.json").write_bytes(canonical(manifest))
        print(json.dumps(manifest, indent=2))
        return 0
    config = config_from(args)
    conditions = CONDITIONS if args.condition == "all" else (args.condition,)
    plans = [plan_experiment(packets, config, condition=c) for c in conditions]
    if args.command == "plan":
        print(json.dumps({"network_requests_made": 0, "config": asdict(config), "plans": plans,
                          "total_requests_without_retries": sum(p["requests_without_retries"] for p in plans),
                          "total_declared_reservation_usd_with_retries": sum(p["declared_cost_reservation_with_retries_usd"] for p in plans)}, indent=2))
        return 0
    if not args.allow_network:
        raise ValueError("run requires --allow-network after reviewing plan and budgets")
    key = os.environ.get(args.api_key_env)
    if key is None and args.api_key_env == "CORRECTION_API_KEY":
        key = os.environ.get("OPENAI_API_KEY", "")
    summary = run_experiment(packets, args.output_dir, config, condition=args.condition,
                             max_requests=args.max_requests, max_cost_usd=args.max_cost_usd,
                             adapter=HTTPAdapter(config, key or ""), network=True, input_bytes=data)
    print(json.dumps(summary, indent=2))
    return 0 if summary["complete"] else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as error:
        # Provider exceptions are converted to safe per-packet outcomes by the runner.
        print("correction runner: " + str(error), file=sys.stderr)
        sys.exit(2)
