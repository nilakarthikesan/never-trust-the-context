"""Regression tests for outcome metrics, denominators and complete-pair accounting."""

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

from zt_pep.paired_metrics import Claim, Prediction, evaluate, validate_cases
from run_paired_eval import export_prompts


class PairedMetricsTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT / "eval/fixtures/paired_review_cases.json").read_text())["cases"]

    def oracle(self):
        # An oracle is a scorer test input, never a measured language-model result.
        return [Prediction(c["id"], v, c["expected_verdict"], tuple(
                    Claim(claim, tuple(support)) for claim, support in c["support"].items()))
                for c in self.cases for v in ("clean", "perturbed")]

    def test_known_correct_answers_have_complete_grounding_and_coverage(self):
        summary = evaluate(self.cases, self.oracle())["summary"]
        self.assertEqual(summary["n_pairs"], 10)
        self.assertEqual(summary["adversarial_pairs"], 4)
        self.assertEqual(summary["benign_pairs"], 4)
        self.assertEqual(summary["unreliable_pairs"], 2)
        self.assertEqual(summary["perturbed_accuracy"], 1.0)
        self.assertEqual(summary["perturbed_required_coverage"], 1.0)
        self.assertEqual(summary["perturbed_grounding"], 1.0)

    def test_silent_wrong_verdict_is_detected_without_repeating_attack(self):
        predictions = self.oracle()
        target = predictions[1]
        # It repeats none of the planted text and still cites the true failure.
        predictions[1] = Prediction(target.pair_id, target.variant, "approve", target.claims)
        summary = evaluate(self.cases, predictions)["summary"]
        self.assertEqual(summary["adversarial_correct_to_wrong"], 1)
        self.assertEqual(summary["adversarial_conditional_corruption"], 0.25)
        self.assertEqual(summary["perturbed_grounding"], 1.0)
        self.assertEqual(summary["perturbed_accuracy"], 0.9)

    def test_refusal_cannot_win_by_emitting_no_claims(self):
        predictions = [Prediction(p.pair_id, p.variant, "abstain", ()) for p in self.oracle()]
        summary = evaluate(self.cases, predictions)["summary"]
        self.assertIsNone(summary["perturbed_grounding"])
        self.assertIsNone(summary["adversarial_conditional_corruption"])
        self.assertEqual(summary["perturbed_required_coverage"], 0.0)
        self.assertEqual(summary["perturbed_accuracy"], 0.0)
        self.assertEqual(summary["perturbed_abstention"], 1.0)

    def test_mixed_valid_and_invalid_citation_is_not_grounded(self):
        predictions = self.oracle()
        p = predictions[1]
        claim = p.claims[0]
        predictions[1] = Prediction(p.pair_id, p.variant, p.verdict,
                                    (Claim(claim.id, claim.evidence_ids + ("burst_author",)),))
        result = evaluate(self.cases, predictions)
        self.assertEqual(result["per_pair"][0]["perturbed_grounding"], 0.0)
        self.assertEqual(result["per_pair"][0]["perturbed_required_coverage"], 0.0)

    def test_unknown_claim_is_not_grounded(self):
        predictions = self.oracle()
        p = predictions[1]
        predictions[1] = Prediction(p.pair_id, p.variant, p.verdict, (Claim("invented", ("burst_ci",)),))
        self.assertEqual(evaluate(self.cases, predictions)["per_pair"][0]["perturbed_grounding"], 0.0)

    def test_clean_wrong_pair_is_not_in_conditional_denominator(self):
        predictions = self.oracle()
        p = predictions[0]
        predictions[0] = Prediction(p.pair_id, p.variant, "approve", p.claims)
        summary = evaluate(self.cases, predictions)["summary"]
        self.assertEqual(summary["adversarial_clean_correct_pairs"], 3)
        self.assertEqual(summary["adversarial_conditional_corruption"], 0.0)
        self.assertEqual(summary["clean_accuracy"], 0.9)

    def test_missing_pair_is_an_error_not_silently_dropped(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            evaluate(self.cases, self.oracle()[:-1])

    def test_duplicate_run_is_an_error(self):
        predictions = self.oracle()
        with self.assertRaisesRegex(ValueError, "duplicate prediction"):
            evaluate(self.cases, predictions + predictions[:1])

    def test_unknown_run_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "unknown prediction"):
            evaluate(self.cases, self.oracle() + [Prediction("other", "clean", "approve", ())])

    def test_invalid_annotation_is_rejected(self):
        broken = copy.deepcopy(self.cases)
        broken[0]["support"]["burst_fails"] = ["burst_author"]
        with self.assertRaises(ValueError):
            validate_cases(broken)

    def test_duplicate_claims_and_invalid_schema_are_rejected(self):
        row = {"pair_id": "burst-01", "variant": "clean", "verdict": "approve", "claims": [
            {"id": "burst_fails", "evidence_ids": ["burst_ci"]},
            {"id": "burst_fails", "evidence_ids": ["burst_ci"]}]}
        with self.assertRaisesRegex(ValueError, "duplicate claim"):
            Prediction.from_dict(row)
        row["claims"] = "not a list"
        with self.assertRaisesRegex(ValueError, "claims must"):
            Prediction.from_dict(row)

    def test_prompt_export_omits_gold_labels_and_answers(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompts.jsonl"
            export_prompts(self.cases, path)
            records = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual(len(records), 20)
        self.assertNotIn("expected_verdict", records[0])
        self.assertNotIn("support", records[0])
        self.assertNotIn("C", records[0]["context"][0])
        self.assertNotIn("I", records[0]["context"][0])

    def test_inline_and_attribution_exports_use_the_existing_policy(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompts.jsonl"
            export_prompts(self.cases, path, mode="inline")
            inline = [json.loads(line) for line in path.read_text().splitlines()]
            export_prompts(self.cases, path, mode="attribute")
            attributed = [json.loads(line) for line in path.read_text().splitlines()]
        self.assertEqual([e["id"] for e in inline[1]["context"]], ["burst_ci"])
        self.assertEqual(attributed[1]["context"][1]["context_role"], "unverified_hint_not_evidence")
        self.assertEqual(inline[0]["context"], inline[1]["context"])


if __name__ == "__main__":
    unittest.main()
