"""Offline runner checks. Oracle-assisted fake responses test plumbing, not model ability."""
import copy
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))
from correction_scope_demo import load_packets
from run_correction_eval import build_materials
from run_correction_models import main
from zt_pep.correction_eval import evaluate, parse_predictions
from zt_pep.correction_runner import (
    CONDITIONS, HTTPAdapter, IntegrityFailure, ModelConfig, ProviderFailure, ReplayAdapter,
    apply_public_updates, build_messages, canonical, condition_packet, heuristic_predictions,
    parse_auxiliary, plan_experiment, reconstruction_candidates, run_experiment, validate_public,
)


def provider_body(content):
    return canonical({"choices": [{"message": {"content": json.dumps(content)}}],
                      "usage": {"prompt_tokens": 23, "completion_tokens": 17, "total_tokens": 40}})


class CorrectionRunnerTests(unittest.TestCase):
    def setUp(self):
        self.prompts, self.reference, self.allowed = build_materials(load_packets())
        self.predictions = {}
        for packet in self.prompts:
            self.predictions[packet["packet_id"]] = {
                "packet_id": packet["packet_id"], "claims": [
                    {"claim_id": claim["claim_id"], **copy.deepcopy(self.reference[
                        packet["packet_id"], claim["claim_id"]])} for claim in packet["claims"]]}
        self.config = ModelConfig("explicit-test-model", "https://provider.invalid/v1", 0.4, 1.6,
                                  max_output_tokens=800, max_retries=0)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "run"
        self.calls = []

    def transport(self, url, body, headers, timeout):
        self.calls.append((url, body, dict(headers), timeout))
        request = json.loads(body)
        content = json.loads(request["messages"][-1]["content"])
        packet = content["packet"]
        prediction = self.predictions[packet["packet_id"]]
        if content["instruction"].startswith("CONSTRAINED"):
            response = {"packet_id": packet["packet_id"], "emitted_candidates": [
                {k: c[k] for k in ("candidate_id", "text")}
                for c in content["reconstruction_candidates"][:1]]}
        elif content["instruction"].startswith("SOURCE-SUPPORT"):
            response = {"packet_id": packet["packet_id"], "ledger": [
                {k: v for k, v in row.items() if k != "status"} for row in prediction["claims"]]}
        else:
            response = prediction
        return 200, provider_body(response)

    def run_fake(self, *, condition="raw_history", prompts=None, config=None,
                 max_requests=100, max_cost_usd=10, transport=None, directory=None):
        config = config or self.config
        return run_experiment(prompts or self.prompts[:2], directory or self.directory, config,
                              condition=condition, max_requests=max_requests, max_cost_usd=max_cost_usd,
                              adapter=HTTPAdapter(config, "test-secret", transport=transport or self.transport),
                              network=True, sleep=lambda _: None)

    def test_exact_requests_raw_responses_usage_and_evaluator_schema(self):
        summary = self.run_fake()
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["provider_requests"], 2)
        self.assertEqual(summary["reported_usage"]["total_tokens"], 80)
        self.assertAlmostEqual(summary["reported_cost_usd_at_declared_rates"],
                               2 * (23 * .4 + 17 * 1.6) / 1_000_000)
        predictions = parse_predictions((self.directory / "predictions.jsonl").read_text())
        reference = {key: value for key, value in self.reference.items()
                     if key[0] in {p["packet_id"] for p in self.prompts[:2]}}
        self.assertEqual(evaluate(reference, predictions, self.allowed)["summary"]["all_fields_correct_rate"], 1)
        request_file = next(self.directory.glob("traces/*/final.request.json"))
        self.assertIn(request_file.read_bytes(), [call[1] for call in self.calls])
        self.assertEqual(self.calls[0][0], "https://provider.invalid/v1/chat/completions")
        self.assertEqual(self.calls[0][2]["Authorization"], "Bearer test-secret")
        self.assertEqual(self.calls[0][3], 60)
        saved = b"".join(p.read_bytes() for p in self.directory.rglob("*") if p.is_file())
        self.assertNotIn(b"test-secret", saved)

    def test_all_conditions_withhold_gold_and_emit_observation_separately(self):
        for condition in CONDITIONS:
            with self.subTest(condition=condition):
                directory = Path(self.temporary.name) / condition
                self.calls.clear()
                summary = self.run_fake(condition=condition, prompts=self.prompts[:1], directory=directory)
                self.assertTrue(summary["complete"])
                self.assertEqual(len(self.calls), 2 if condition.endswith("audit") else 1)
                for _, body, _, _ in self.calls:
                    content = json.loads(json.loads(body)["messages"][-1]["content"])
                    packet = content["packet"]
                    self.assertNotIn("private_world_truth", packet)
                    self.assertNotIn("description", packet)
                    for claim in packet["claims"]:
                        self.assertEqual(set(claim), {"claim_id", "text"})
                if condition == "regeneration_audit":
                    observation = json.loads(next(directory.glob("traces/*/auxiliary.json")).read_text())
                    self.assertEqual(observation["emitted_candidates"], [
                        {k: c[k] for k in ("candidate_id", "text")}
                        for c in reconstruction_candidates(self.prompts[0])[:1]])
                    self.assertNotIn("regenerate", observation)
                    self.assertTrue(set(c["candidate_id"] for c in observation["emitted_candidates"]).isdisjoint(
                        c["claim_id"] for c in self.prompts[0]["claims"]))

    def test_filtered_reread_preserves_archive_and_does_not_mutate_input(self):
        packet = next(p for p in self.prompts if any(e["op"] == "retract" for e in p["events"]))
        before = copy.deepcopy(packet)
        filtered = condition_packet(packet, "source_filtered_reread")
        self.assertEqual(packet, before)
        self.assertEqual(filtered["events"], [])
        self.assertEqual(len(filtered["records"]), len(packet["records"]))
        self.assertTrue(any(r["status"] == "archive" for r in filtered["records"]))

    def test_regeneration_parser_requires_observed_exact_candidate_subset(self):
        packet = self.prompts[0]
        candidate = {k: reconstruction_candidates(packet)[0][k] for k in ("candidate_id", "text")}
        good = {"packet_id": packet["packet_id"], "emitted_candidates": []}
        self.assertEqual(parse_auxiliary(json.dumps(good), packet, "regeneration_audit"), good)
        invalid = [
            {"packet_id": packet["packet_id"], "judgments": []},
            {"packet_id": packet["packet_id"], "emitted_candidates": [{**candidate, "text": "changed"}]},
            {"packet_id": packet["packet_id"], "emitted_candidates": [candidate, candidate]},
            {"packet_id": packet["packet_id"], "emitted_candidates": packet["claims"][:1]},
        ]
        for value in invalid:
            with self.assertRaises(ValueError):
                parse_auxiliary(json.dumps(value), packet, "regeneration_audit")
        with self.assertRaises(ValueError):
            parse_auxiliary('{"packet_id":"a","packet_id":"b","emitted_candidates":[]}', packet, "regeneration_audit")

    def test_resume_reuses_saved_results_without_new_provider_calls(self):
        first = self.run_fake(condition="regeneration_audit")
        calls = len(self.calls)
        resumed = self.run_fake(condition="regeneration_audit")
        self.assertEqual(len(self.calls), calls)
        self.assertEqual(resumed["provider_requests"], first["provider_requests"])
        self.assertEqual(resumed["reserved_cost_usd"], first["reserved_cost_usd"])

    def test_resume_rejects_input_config_budget_or_saved_response_change(self):
        self.run_fake()
        changed = copy.deepcopy(self.prompts[:2])
        changed[0]["claims"][0]["text"] += " modified"
        for kwargs in ({"prompts": changed}, {"config": replace(self.config, model="another")},
                       {"max_requests": 101}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.run_fake(**kwargs)
        response = next(self.directory.glob("traces/*/final.response.json"))
        response.write_bytes(response.read_bytes() + b" ")
        with self.assertRaises(IntegrityFailure):
            self.run_fake()

    def test_replay_matches_complete_request_and_performs_no_network(self):
        self.run_fake(condition="source_support_audit")
        replay = ReplayAdapter(self.directory)
        output = Path(self.temporary.name) / "replayed"
        summary = run_experiment(self.prompts[:2], output, self.config,
                                 condition="source_support_audit", max_requests=100,
                                 max_cost_usd=0, adapter=replay)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["provider_requests"], 0)
        self.assertEqual(summary["reserved_cost_usd"], 0)
        self.assertEqual((output / "predictions.jsonl").read_bytes(),
                         (self.directory / "predictions.jsonl").read_bytes())
        with self.assertRaises(ProviderFailure):
            replay.request(b"different request")

    def test_retry_budget_counts_failures_and_omits_error_body_secrets(self):
        calls = []
        def failing(url, body, headers, timeout):
            calls.append(1)
            return 503, b"test-secret private provider details"
        summary = self.run_fake(config=replace(self.config, max_retries=2),
                                max_requests=2, transport=failing)
        self.assertFalse(summary["complete"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(summary["provider_requests"], 2)
        self.assertGreater(summary["reserved_cost_usd"], 0)
        self.assertEqual(summary["outcomes"][0]["state"], "budget_exhausted")
        saved = b"".join(p.read_bytes() for p in self.directory.rglob("*") if p.is_file())
        self.assertNotIn(b"test-secret", saved)
        self.assertNotIn(b"private provider details", saved)

    def test_auth_and_quota_failures_open_circuit_without_retrying_remaining_packets(self):
        for status in (401, 403, 429):
            with self.subTest(status=status):
                count = []
                def denied(*_):
                    count.append(1)
                    return status, b"secret error body is not persisted"
                summary = self.run_fake(config=replace(self.config, max_retries=2), transport=denied,
                                        directory=Path(self.temporary.name) / str(status))
                self.assertEqual(count, [1])
                self.assertEqual(summary["n_valid"], 0)
                self.assertEqual(summary["n_unattempted_packets"], 1)
                self.assertFalse(summary["usage_complete"])
                self.assertEqual(summary["stop_reason"], "provider_circuit_breaker_http_" + str(status))
                self.run_fake(config=replace(self.config, max_retries=2), transport=denied,
                              directory=Path(self.temporary.name) / str(status))
                self.assertEqual(count, [1])

    def test_timeout_exception_is_safe_and_retryable(self):
        def timeout(*_):
            raise TimeoutError("test-secret and headers")
        summary = self.run_fake(config=replace(self.config, max_retries=1), transport=timeout,
                                prompts=self.prompts[:1])
        self.assertEqual(summary["provider_requests"], 2)
        self.assertEqual(summary["outcomes"][0]["error_code"], "transport_error")
        self.assertNotIn("test-secret", (self.directory / "run_summary.json").read_text())

    def test_cost_budget_stops_before_http_and_survives_resume(self):
        first = self.run_fake(max_cost_usd=0)
        self.assertEqual(first["provider_requests"], 0)
        self.assertFalse(first["complete"])
        self.assertEqual(self.calls, [])
        resumed = self.run_fake(max_cost_usd=0)
        self.assertEqual(resumed["provider_requests"], 0)

    def reservation(self, packet):
        body = canonical({"model": self.config.model,
                          "messages": build_messages(packet, "raw_history"),
                          "temperature": self.config.temperature,
                          "max_tokens": self.config.max_output_tokens})
        return ((len(body) + 1024) * self.config.input_price_per_million
                + self.config.max_output_tokens * self.config.output_price_per_million) / 1_000_000

    def test_successful_complete_usage_releases_reservation_before_next_request(self):
        reported_charge = (23 * .4 + 17 * 1.6) / 1_000_000
        budget = max(self.reservation(p) for p in self.prompts[:2]) + reported_charge + .000001
        summary = self.run_fake(max_cost_usd=budget)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["provider_requests"], 2)
        self.assertGreater(summary["reserved_cost_usd"], budget)
        self.assertAlmostEqual(summary["budgeted_cost_usd"], reported_charge * 2)
        count = len(self.calls)
        resumed = self.run_fake(max_cost_usd=budget)
        self.assertEqual(len(self.calls), count)
        self.assertEqual(resumed["budgeted_cost_usd"], summary["budgeted_cost_usd"])

    def test_missing_usage_retains_full_reservation_and_blocks_next_request(self):
        def no_usage(url, body, headers, timeout):
            status, raw = self.transport(url, body, headers, timeout)
            response = json.loads(raw)
            response.pop("usage")
            return status, canonical(response)
        summary = self.run_fake(max_cost_usd=self.reservation(self.prompts[0]) + 1e-9,
                                transport=no_usage)
        self.assertEqual(summary["n_valid"], 1)
        self.assertFalse(summary["complete"])
        self.assertFalse(summary["usage_complete"])
        self.assertEqual(summary["budgeted_cost_usd"], summary["reserved_cost_usd"])
        self.assertEqual(summary["provider_requests"], 1)

    def test_invalid_final_json_is_not_repaired_or_counted_valid(self):
        def invalid(*_):
            return 200, provider_body("```json\n{}\n```")
        summary = self.run_fake(transport=invalid, prompts=self.prompts[:1])
        self.assertEqual(summary["n_valid"], 0)
        self.assertEqual(summary["outcomes"][0]["state"], "invalid_model_output")
        self.assertTrue(next(self.directory.glob("traces/*/final.response.json")).exists())
        self.assertEqual((self.directory / "predictions.jsonl").read_bytes(), b"")

    def test_invalid_provider_body_is_preserved_but_not_a_model_result(self):
        summary = self.run_fake(transport=lambda *_: (200, b"not JSON"), prompts=self.prompts[:1])
        self.assertEqual(summary["outcomes"][0]["error_code"], "invalid_provider_response")
        self.assertEqual(next(self.directory.glob("traces/*/final.response.json")).read_bytes(), b"not JSON")
        self.assertFalse(list(self.directory.glob("traces/*/final.result.json")))

    def test_known_secret_echo_is_redacted_and_explicitly_flagged(self):
        def echo(*_):
            raw = json.loads(provider_body(self.predictions[self.prompts[0]["packet_id"]]))
            raw["provider_debug"] = "test-secret"
            return 200, canonical(raw)
        summary = self.run_fake(transport=echo, prompts=self.prompts[:1])
        self.assertTrue(summary["complete"])
        result = json.loads(next(self.directory.glob("traces/*/final.result.json")).read_text())
        self.assertTrue(result["known_secret_redacted"])

    def test_http_requires_explicit_authorization_and_config_has_no_model_default(self):
        with self.assertRaises(ValueError):
            run_experiment(self.prompts[:1], self.directory, self.config, condition="raw_history",
                           max_requests=1, max_cost_usd=1, adapter=HTTPAdapter(self.config, ""))
        for config in ({"model": ""}, {"base_url": "https://secret:password@example.com/v1"},
                       {"base_url": "https://example.com/v1?key=secret"}, {"max_retries": 6}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                replace(self.config, **config)

    def test_private_annotations_are_rejected(self):
        packets = copy.deepcopy(self.prompts[:1])
        packets[0]["private_world_truth"] = {}
        with self.assertRaises(ValueError):
            validate_public(packets)
        packets = copy.deepcopy(self.prompts[:1])
        packets[0]["claims"][0]["kind"] = "current_support"
        with self.assertRaises(ValueError):
            validate_public(packets)

    def test_dry_run_counts_two_stage_calls_and_retry_reservations(self):
        for condition in CONDITIONS:
            plan = plan_experiment(self.prompts[:2], replace(self.config, max_retries=2), condition=condition)
            n = 4 if condition.endswith("audit") else 2
            self.assertEqual(plan["requests_without_retries"], n)
            self.assertEqual(plan["maximum_attempts_with_retries"], n * 3)
            self.assertAlmostEqual(plan["declared_cost_reservation_with_retries_usd"],
                                   plan["declared_cost_reservation_without_retries_usd"] * 3)
        self.assertFalse(self.directory.exists())

    def test_heuristic_controls_are_public_only_and_schema_valid(self):
        for method in ("initial_records_heuristic", "latest_notice_heuristic"):
            rows = heuristic_predictions(self.prompts, method)
            self.assertEqual(len(parse_predictions("\n".join(json.dumps(r) for r in rows))), len(self.prompts))
        forged = next(p for p in self.prompts if any(e["issuer"] != next(
            r["source_owner"] for r in p["records"] if r["record_id"] == e["target_record_id"])
            for e in p["events"]))
        self.assertNotEqual(apply_public_updates(forged)[0],
                            apply_public_updates(forged, check_authority=False)[0])

    def test_pilot_heuristics_recognize_historical_record_and_public_source_labels(self):
        prompts, reference, _ = build_materials(load_packets(ROOT / "eval/fixtures/correction_pilot.json"))
        for method in ("initial_records_heuristic", "latest_notice_heuristic"):
            for prediction in heuristic_predictions(prompts, method):
                history = prediction["claims"][0]
                gold = reference[prediction["packet_id"], history["claim_id"]]
                self.assertEqual(history["scope"], "historical_assertion")
                self.assertEqual(history["supporting_records"], gold["supporting_records"])
                # On unchanged controls, source label matching must recover the
                # named primary owner instead of choosing the first opaque ID.
                prompt = next(p for p in prompts if p["packet_id"] == prediction["packet_id"])
                if not prompt["events"]:
                    endorsement = prediction["claims"][1]
                    expected = reference[prediction["packet_id"], endorsement["claim_id"]]
                    self.assertEqual(endorsement["scope"], "current_endorsement")
                    self.assertEqual(endorsement["supporting_records"], expected["supporting_records"])


if __name__ == "__main__":
    unittest.main()
