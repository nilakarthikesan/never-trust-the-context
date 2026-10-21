"""Pilot invariants and executable tool tests; no model-performance observations."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))
from correction_scope_demo import audit_packet
from analyze_correction_pilot import analyze_run
from run_correction_eval import build_materials
from zt_pep.correction_eval import evaluate
from zt_pep.correction_pilot import (
    CANDIDATES, FAMILIES, SCENARIOS, SandboxSession, build_pilot,
    execute_checks, paired_analysis, run_reference_policies, validate_pilot,
)


class CorrectionPilotTests(unittest.TestCase):
    def setUp(self):
        self.suite, self.manifest = build_pilot()

    def session(self, family, within=0, variant="update", **kwargs):
        base = [b for b in self.manifest["bases"] if b["family"] == family][within]
        packet = next(p for p in self.suite["packets"]
                      if p["packet_id"] == base["packets"][variant]["internal_packet_id"])
        return SandboxSession(base, packet, audit_packet, **kwargs)

    def diagnostic_metrics(self):
        prompts, reference, allowed = build_materials(self.suite["packets"])
        predictions = [{"packet_id": prompt["packet_id"], "claims": [
            {"claim_id": claim["claim_id"], **copy.deepcopy(reference[prompt["packet_id"], claim["claim_id"]])}
            for claim in prompt["claims"]]} for prompt in prompts]
        return evaluate(reference, predictions, allowed)

    def test_design_has_24_distinct_base_contracts_and_48_pairs(self):
        result = validate_pilot(self.suite, self.manifest, audit_packet)
        self.assertEqual(result["bases"], 24)
        self.assertEqual(result["packets"], 48)
        self.assertEqual(result["claim_judgments"], 144)
        self.assertEqual(result["bounded_checks_executed"], 72)
        self.assertGreater(result["bounded_candidates_passing"], 0)
        self.assertLess(result["bounded_candidates_passing"], 24)

    def test_saved_fixture_is_deterministically_reproducible(self):
        for filename, expected in (("correction_pilot.json", self.suite),
                                   ("correction_pilot_manifest.json", self.manifest)):
            saved = json.loads((ROOT / "eval/fixtures" / filename).read_text())
            self.assertEqual(saved, expected)

    def test_family_oracle_results_and_paired_identity(self):
        for family in FAMILIES:
            for base in (b for b in self.manifest["bases"] if b["family"] == family):
                identities = base["packets"]
                packets = [next(p for p in self.suite["packets"] if p["packet_id"] == identities[v]["internal_packet_id"])
                           for v in ("unchanged", "update")]
                self.assertEqual(packets[0]["claims"], packets[1]["claims"])
                self.assertEqual(packets[0]["records"], packets[1]["records"])
                self.assertNotEqual(identities["unchanged"]["public_packet_id"], identities["update"]["public_packet_id"])
                self.assertEqual(audit_packet(packets[1])["claims"][0]["status"], "supported")

    def test_public_export_withholds_private_design_and_truth(self):
        prompts, _, _ = build_materials(self.suite["packets"])
        for prompt in prompts:
            encoded = json.dumps(prompt)
            for key in ("family", "partition", "human_validated", "private_world_truth", "authoring_key", "base_id"):
                self.assertNotIn('"' + key + '"', encoded)
            for family in FAMILIES:
                self.assertNotIn(family, encoded)
            self.assertNotIn("kind", prompt["claims"][0])

    def test_independence_requires_explicit_distinct_direct_lineage(self):
        changed = copy.deepcopy(self.suite)
        base = next(b for b in self.manifest["bases"] if b["family"] == "independent_support")
        packet = next(p for p in changed["packets"] if p["packet_id"] == base["packets"]["unchanged"]["internal_packet_id"])
        packet["records"][1]["origin"]["derived_from_records"] = [packet["records"][0]["record_id"]]
        with self.assertRaisesRegex(ValueError, "copied report"):
            validate_pilot(changed, self.manifest, audit_packet)

    def test_sandbox_runs_actual_boundary_checks_not_gold_labels(self):
        expected_passing = {"page_slice", "refund_cents", "queue_push", "header_lookup", "remaining_quota",
                            "schedule_by_priority", "role_allowed", "nonnegative_amount", "safe_ratio", "utf8_prefix"}
        for base in self.manifest["bases"]:
            with self.subTest(candidate=base["scenario"]["candidate"]):
                actual = execute_checks(base["scenario"])
                self.assertEqual(actual["passed"], base["scenario"]["candidate"] in expected_passing)
                self.assertEqual(len(actual["checks"]), 3)
        self.assertEqual(len(CANDIDATES), 24)

    def test_unknown_or_modified_programs_cannot_execute(self):
        scenario = copy.deepcopy(self.manifest["bases"][0]["scenario"])
        scenario["candidate"] = "eval"
        with self.assertRaisesRegex(ValueError, "unknown"):
            execute_checks(scenario)
        scenario = copy.deepcopy(self.manifest["bases"][0]["scenario"])
        scenario["checks"][0]["args"] = [1000000000, 2, 9]
        with self.assertRaisesRegex(ValueError, "authored"):
            execute_checks(scenario)

    def test_true_but_unsupported_can_be_verified_then_approved(self):
        session = self.session("genuine_withdrawal", within=1)
        self.assertEqual(session.source_status, "unsupported")
        self.assertTrue(session.verify()["passed"])
        self.assertTrue(session.approve()["eligible"])
        self.assertTrue(session.private_grade()["private_bounded_truth"])

    def test_unsupported_approval_attempt_is_not_allowed(self):
        session = self.session("genuine_withdrawal", within=1)
        response = session.approve()
        self.assertFalse(response["eligible"])
        self.assertFalse(response["mock_approved"])
        self.assertFalse(session.private_grade()["approval_attempt_eligible"])

    def test_supported_false_candidate_eligibility_differs_from_correctness(self):
        session = self.session("same_value_replacement", within=1)
        self.assertEqual(session.source_status, "supported")
        self.assertTrue(session.approve()["eligible"])
        grade = session.private_grade()
        self.assertFalse(grade["private_bounded_truth"])
        self.assertTrue(grade["approved_failing_candidate"])

    def test_private_annotation_does_not_drive_tools_or_approval(self):
        session = self.session("same_value_replacement", within=1)
        session.base["private_bounded_truth"] = True
        session.packet["private_world_truth"] = {key: True for key in session.packet["propositions"]}
        self.assertFalse(session.verify()["passed"])
        self.assertFalse(session.approve()["eligible"])
        self.assertFalse(session.private_grade()["private_bounded_truth"])

    def test_acquired_failed_verification_blocks_mistaken_positive_sources(self):
        session = self.session("same_value_replacement", within=1)
        self.assertFalse(session.verify()["passed"])
        self.assertFalse(session.approve()["eligible"])

    def test_conflicting_sources_can_be_resolved_by_passing_actual_check(self):
        session = self.session("conflict_survivor", within=0)
        self.assertEqual(session.source_status, "conflicted")
        self.assertTrue(session.verify()["passed"])
        self.assertTrue(session.approve()["eligible"])
        self.assertEqual(session.private_grade()["source_evidence_status"], "conflicted")

    def test_budget_terminal_action_and_no_private_tool_leakage(self):
        session = self.session("genuine_withdrawal", within=1)
        public = json.dumps(session.public_task())
        for secret in ("private_bounded_truth", "family", "partition", "checks"):
            self.assertNotIn('"' + secret + '"', public)
        session.verify()
        with self.assertRaisesRegex(ValueError, "budget"):
            session.verify()
        session.decline()
        with self.assertRaisesRegex(ValueError, "ended"):
            session.verify()
        with self.assertRaisesRegex(ValueError, "ended"):
            session.approve()
        self.assertNotIn("private_bounded_truth", session.actions[0])

    def test_no_verification_or_action_is_not_silently_a_decline(self):
        session = self.session("forged_notice")
        self.assertFalse(session.private_grade()["action_observed"])
        self.assertIsNone(session.private_grade()["action"])
        with self.assertRaises(ValueError):
            self.session("forged_notice", verify_budget=-1)
        zero = self.session("forged_notice", verify_budget=0)
        with self.assertRaisesRegex(ValueError, "budget"):
            zero.verify()

    def test_reference_policies_execute_tools_and_keep_truth_cost_eligibility_separate(self):
        result = run_reference_policies(self.suite, self.manifest, audit_packet)
        self.assertEqual(result["model_calls"], 0)
        self.assertEqual(len(result["traces"]), 192)
        verify = result["summary"]["always_verify_then_act"]
        self.assertEqual(verify["verification_calls"], 48)
        self.assertEqual(verify["selection_matches_bounded_truth"], 48)
        self.assertEqual(verify["approved_failing_candidate"], 0)
        self.assertEqual(verify["declined_passing_candidate"], 0)
        follow = result["summary"]["never_verify_follow_valid_support"]
        self.assertEqual(follow["verification_calls"], 0)
        self.assertEqual(follow["ineligible_approval_attempts"], 0)
        self.assertGreater(follow["approved_failing_candidate"], 0)
        blind = result["summary"]["blindly_approve"]
        self.assertEqual(blind["approval_attempts"], 48)
        self.assertGreater(blind["ineligible_approval_attempts"], 0)
        self.assertLess(blind["mock_approved"], blind["approval_attempts"])
        decline = result["summary"]["always_decline"]
        self.assertEqual(decline["approval_attempts"], 0)
        self.assertEqual(decline["verification_calls"], 0)
        self.assertEqual(decline["declined_passing_candidate"], 20)

    def test_paired_analysis_resamples_bases_and_exposes_nonzero_change(self):
        metrics = self.diagnostic_metrics()
        base = self.manifest["bases"][0]
        identity = base["packets"]["update"]
        row = next(r for r in metrics["per_claim"] if r["packet_id"] == identity["public_packet_id"]
                   and r["claim_id"] == identity["claims"]["current_support"])
        row["prediction"]["status"] = "supported"
        row["status_correct"] = row["scope_status_correct"] = row["all_fields_correct"] = False
        result = paired_analysis(metrics, self.manifest, 100, 1)
        self.assertEqual(result["n_bases"], 24)
        self.assertAlmostEqual(result["summary"]["status_correct"]["paired_mean_change"], -1 / 72)
        self.assertEqual(result, paired_analysis(metrics, self.manifest, 100, 1))
        self.assertIn("base", result["bootstrap"]["unit"])
        self.assertEqual(result["directional_status_errors"]["unsupported_claim_marked_supported"], 1)

    def test_paired_analysis_rejects_tampered_flags_and_collapsed_manifest(self):
        metrics = self.diagnostic_metrics()
        metrics["per_claim"][0]["scope_correct"] = False
        with self.assertRaisesRegex(ValueError, "flags disagree"):
            paired_analysis(metrics, self.manifest, 10)
        manifest = copy.deepcopy(self.manifest)
        manifest["bases"][1] = copy.deepcopy(manifest["bases"][0])
        with self.assertRaisesRegex(ValueError, "unique base"):
            paired_analysis(self.diagnostic_metrics(), manifest, 10)

    def test_analysis_cannot_write_private_pair_mapping_inside_public_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            public = root / "public"
            public.mkdir()
            (public / "export_manifest.json").write_text("{}\n")
            nested = public / "nested"
            nested.mkdir()
            metrics, manifest = root / "metrics.json", root / "manifest.json"
            metrics.write_text(json.dumps(self.diagnostic_metrics()))
            manifest.write_text(json.dumps(self.manifest))
            for output in (public / "analysis.json", nested / "analysis.json"):
                with self.assertRaisesRegex(ValueError, "outside the public"):
                    analyze_run(metrics, manifest, output, 10)
                self.assertFalse(output.exists())
            outside = root / "paired.json"
            self.assertEqual(analyze_run(metrics, manifest, outside, 10)["n_bases"], 24)
            with self.assertRaises(FileExistsError):
                analyze_run(metrics, manifest, outside, 10)

    def test_paired_analysis_rejects_incomplete_duplicate_or_extra_observations(self):
        original = self.diagnostic_metrics()
        variants = []
        missing = copy.deepcopy(original)
        missing["per_claim"].pop()
        variants.append(missing)
        duplicate = copy.deepcopy(original)
        duplicate["per_claim"].append(copy.deepcopy(duplicate["per_claim"][0]))
        variants.append(duplicate)
        extra = copy.deepcopy(original)
        extra["per_claim"][0]["claim_id"] = "other"
        variants.append(extra)
        for value in variants:
            with self.assertRaises(ValueError):
                paired_analysis(value, self.manifest, 10)


if __name__ == "__main__":
    unittest.main()
