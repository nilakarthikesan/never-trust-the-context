"""Offline fake-provider checks of real bounded tools, never model-performance claims."""
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
from correction_scope_demo import audit_packet
from run_correction_eval import build_materials
from zt_pep.correction_actions import align_cases, parse_tool_choice, run_action_experiment
from zt_pep.correction_pilot import build_pilot
from zt_pep.correction_runner import HTTPAdapter, ModelConfig, canonical


class CorrectionActionTests(unittest.TestCase):
    def setUp(self):
        self.suite, self.manifest = build_pilot()
        self.prompts, _, _ = build_materials(self.suite["packets"])
        self.config = ModelConfig("explicit-test-model", "https://provider.invalid/v1", .4, 1.6,
                                  max_output_tokens=200, max_retries=0)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "actions"
        self.calls = []
        self.policy = "verify_then_act"

    def transport(self, url, body, headers, timeout):
        request = json.loads(body)
        self.calls.append(request)
        if self.policy == "verify_then_act":
            latest = json.loads(request["messages"][-1]["content"])
            if "acquired_tool_result" not in latest:
                tool = "verify"
            else:
                tool = "approve" if latest["acquired_tool_result"]["result"]["passed"] else "decline"
        else:
            tool = self.policy
        return 200, canonical({"choices": [{"message": {"content": json.dumps(
            {"tool": tool, "arguments": {}})}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}})

    def run_actions(self, *, prompts=None, condition="raw_history", transport=None,
                    max_requests=100, max_cost_usd=10, config=None, output=None):
        config = config or self.config
        return run_action_experiment(prompts or self.prompts[:2], self.suite, self.manifest,
                                     audit_packet, output or self.output, config, condition=condition,
                                     max_requests=max_requests, max_cost_usd=max_cost_usd,
                                     adapter=HTTPAdapter(config, "test-secret", transport=transport or self.transport),
                                     network=True, sleep=lambda _: None)

    def grades(self):
        return [json.loads(line) for line in (self.output / "private_grades.jsonl").read_text().splitlines()]

    def test_acquired_verification_executes_real_checks_before_terminal_action(self):
        # retry_delay fails; page_slice passes. The fake model chooses from the
        # actual acquired tool result, not a private label supplied in its prompt.
        summary = self.run_actions(prompts=[self.prompts[0], self.prompts[2]])
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["provider_requests"], 4)
        self.assertEqual(summary["verification_calls"], 2)
        self.assertEqual(summary["selection_matches_bounded_truth"], 2)
        self.assertEqual(summary["approved_failing_candidate"], 0)
        grades = self.grades()
        self.assertFalse(grades[0]["private_grade"]["private_bounded_truth"])
        self.assertEqual(grades[0]["private_grade"]["action"], "decline")
        self.assertTrue(grades[1]["private_grade"]["private_bounded_truth"])
        self.assertEqual(grades[1]["private_grade"]["action"], "approve")
        for trace_file in self.output.glob("traces/*/action_trace.json"):
            trace = json.loads(trace_file.read_text())
            self.assertEqual(len(trace["calls"][0]["tool_response"]["checks"]), 3)
            self.assertNotIn("private_grade", trace)
        self.assertFalse(any("test-secret" in p.read_text() for p in self.output.rglob("*") if p.is_file()))

    def test_model_attempt_gate_eligibility_and_actual_truth_are_separate(self):
        self.policy = "approve"
        summary = self.run_actions()
        self.assertEqual(summary["approval_attempts"], 2)
        self.assertEqual(summary["ineligible_approval_attempts"], 1)
        self.assertEqual(summary["mock_approved"], 1)
        self.assertEqual(summary["approved_failing_candidate"], 1)
        self.assertEqual(summary["verification_calls"], 0)
        first, second = [g["private_grade"] for g in self.grades()]
        self.assertTrue(first["approval_attempt_eligible"])
        self.assertFalse(first["private_bounded_truth"])
        self.assertFalse(second["approval_attempt_eligible"])

    def test_private_checks_labels_and_mapping_never_enter_initial_model_input(self):
        self.policy = "decline"
        self.run_actions()
        for request in self.calls:
            content = json.loads(request["messages"][1]["content"])
            task = content["bounded_review_task"]
            self.assertIn("candidate_source", task)
            self.assertIn("requirements", task)
            self.assertNotIn("checks", task)
            packet = content["evidence_packet"]
            self.assertNotIn("private_world_truth", packet)
            self.assertNotIn("base_id", packet)
            for claim in packet["claims"]:
                self.assertEqual(set(claim), {"claim_id", "text"})
            text = request["messages"][1]["content"]
            for private_field in ("private_bounded_truth", "source_evidence_status", "private_grade", "human_validated"):
                self.assertNotIn(private_field, text)

    def test_filtered_view_preserves_history_and_canonical_tool_policy(self):
        self.policy = "decline"
        summary = self.run_actions(prompts=self.prompts[1:2], condition="source_filtered_reread")
        self.assertTrue(summary["complete"])
        view = json.loads(self.calls[0]["messages"][1]["content"])["evidence_packet"]
        self.assertEqual(view["events"], [])
        self.assertEqual(view["records"][0]["status"], "archive")
        self.assertEqual(self.grades()[0]["private_grade"]["source_evidence_status"], "unsupported")
        self.assertEqual(self.prompts[1]["records"][0]["status"], "active")

    def test_repeated_verify_cannot_repeat_execution_or_exceed_three_calls(self):
        self.policy = "verify"
        summary = self.run_actions(prompts=self.prompts[:1])
        self.assertFalse(summary["complete"])
        self.assertEqual(summary["provider_requests"], 3)
        self.assertEqual(summary["verification_calls"], 1)
        self.assertEqual(summary["terminal_actions"], 0)
        self.assertEqual(summary["outcomes"][0]["state"], "packet_call_limit")
        trace = json.loads(next(self.output.glob("traces/*/action_trace.json")).read_text())
        self.assertEqual(trace["calls"][1]["tool_response"], {"error": "verification_budget_exhausted"})

    def test_retry_attempts_also_count_toward_three_call_packet_limit(self):
        def unavailable(*_):
            return 503, b"provider body must not persist"
        summary = self.run_actions(transport=unavailable, config=replace(self.config, max_retries=5))
        self.assertEqual(summary["provider_requests"], 6)
        self.assertEqual(summary["terminal_actions"], 0)
        for packet_dir in (self.output / "traces").iterdir():
            self.assertEqual(len(list(packet_dir.glob("*.attempt-*.json"))), 3)
        self.assertFalse(summary["usage_complete"])

    def test_quota_failure_opens_circuit_and_is_not_an_action(self):
        summary = self.run_actions(transport=lambda *_: (429, b"test-secret insufficient quota"),
                                   config=replace(self.config, max_retries=2))
        self.assertEqual(summary["provider_requests"], 1)
        self.assertEqual(summary["n_unattempted_packets"], 1)
        self.assertEqual(summary["terminal_actions"], 0)
        self.assertFalse(summary["usage_complete"])
        self.assertEqual(summary["stop_reason"], "provider_circuit_breaker_http_429")
        self.assertIsNone(summary["selection_matches_bounded_truth_rate_among_terminal_actions"])

    def test_malformed_choice_does_not_execute_tools_or_repair(self):
        for text in ('{"tool":"execute","arguments":{"command":"anything"}}',
                     '{"tool":"verify","tool":"approve","arguments":{}}'):
            with self.assertRaises(ValueError):
                parse_tool_choice(text)
        self.policy = "execute"
        summary = self.run_actions(prompts=self.prompts[:1])
        self.assertEqual(summary["outcomes"][0]["state"], "invalid_model_output")
        self.assertEqual(summary["provider_requests"], 1)
        self.assertEqual(summary["terminal_actions"], 0)
        self.assertEqual(summary["verification_calls"], 0)

    def test_refuse_overwrite_and_require_explicit_network_authorization(self):
        self.policy = "decline"
        self.run_actions()
        before = len(self.calls)
        with self.assertRaises(FileExistsError):
            self.run_actions()
        self.assertEqual(len(self.calls), before)
        with self.assertRaises(ValueError):
            run_action_experiment(self.prompts[:1], self.suite, self.manifest, audit_packet,
                                  Path(self.temp.name) / "denied", self.config, condition="raw_history",
                                  max_requests=3, max_cost_usd=1, adapter=HTTPAdapter(self.config, ""))

    def test_mismatched_private_mapping_or_evidence_is_rejected_before_run(self):
        changed = copy.deepcopy(self.prompts[:1])
        changed[0]["events"] = [{"invalid": "extra"}]
        with self.assertRaises(ValueError):
            align_cases(changed, self.suite, self.manifest)
        self.assertFalse(self.output.exists())

    def test_malformed_private_check_program_is_rejected_before_provider_contact(self):
        self.manifest["bases"][0]["scenario"]["checks"][0]["expected"] = "tampered"
        with self.assertRaises(ValueError):
            self.run_actions(prompts=self.prompts[:1])
        self.assertEqual(self.calls, [])
        self.assertFalse(self.output.exists())

    def test_private_grades_cannot_be_written_into_public_export_tree(self):
        export = Path(self.temp.name) / "public-export"
        export.mkdir()
        (export / "export_manifest.json").write_text("{}")
        for target in (export, export / "actions", export / "nested" / "actions"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.run_actions(output=target)
            self.assertEqual(self.calls, [])
            self.assertFalse((target / "private_grades.jsonl").exists())
            if target != export:
                self.assertFalse(target.exists())

    def test_zero_cost_budget_prevents_requests_and_marks_no_model_actions(self):
        summary = self.run_actions(max_cost_usd=0)
        self.assertEqual(summary["provider_requests"], 0)
        self.assertEqual(summary["n_attempted_packets"], 0)
        self.assertEqual(self.calls, [])
        self.assertEqual(summary["terminal_actions"], 0)
        self.assertFalse(summary["usage_complete"])
        self.assertEqual(summary["stop_reason"], "request_or_cost_budget_exhausted")


if __name__ == "__main__":
    unittest.main()
