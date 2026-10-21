"""Offline schema/scoring tests; oracle predictions below are diagnostics, not model results."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))
from correction_scope_demo import DEFAULT_SUITE, load_packets
from run_correction_eval import build_materials, export_run, score_run, sha256
from zt_pep.correction_eval import evaluate, parse_predictions


class CorrectionEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.prompts, self.reference, self.allowed = build_materials(load_packets())
        self.predictions = []
        for prompt in self.prompts:
            claims = []
            for visible in prompt["claims"]:
                gold = self.reference[prompt["packet_id"], visible["claim_id"]]
                claims.append({"claim_id": visible["claim_id"], **copy.deepcopy(gold)})
            self.predictions.append({"packet_id": prompt["packet_id"], "claims": claims})

    def score(self, predictions=None):
        return evaluate(self.reference, self.predictions if predictions is None else predictions,
                        self.allowed)

    def prediction_text(self):
        return "".join(json.dumps(row) + "\n" for row in self.predictions)

    def test_oracle_diagnostic_checks_scoring_not_model_performance(self):
        result = self.score()
        self.assertEqual(result["summary"]["n_claims"], 16)
        self.assertEqual(result["summary"]["all_fields_correct_rate"], 1.0)
        self.assertEqual(result["summary"]["n_packets"], 5)

    def test_correct_status_does_not_hide_wrong_extracted_scope(self):
        changed = copy.deepcopy(self.predictions)
        changed[0]["claims"][0]["scope"] = "current_support"
        result = self.score(changed)["summary"]
        self.assertEqual(result["status_correct_rate"], 1.0)
        self.assertEqual(result["scope_correct_rate"], 15 / 16)
        self.assertEqual(result["scope_status_correct_rate"], 15 / 16)

    def test_correct_scope_does_not_hide_wrong_status(self):
        changed = copy.deepcopy(self.predictions)
        changed[0]["claims"][0]["status"] = "unsupported"
        result = self.score(changed)["summary"]
        self.assertEqual(result["scope_correct_rate"], 1.0)
        self.assertEqual(result["status_correct_rate"], 15 / 16)

    def test_hallucinated_citation_is_a_scored_error(self):
        changed = copy.deepcopy(self.predictions)
        changed[0]["claims"][0]["supporting_records"].append("invented-record")
        result = self.score(changed)["summary"]
        self.assertEqual(result["claims_with_unknown_citations"], 1)
        self.assertEqual(result["evidence_sets_exact_rate"], 15 / 16)

    def test_missing_duplicate_and_unknown_observations_are_rejected(self):
        variants = []
        missing = copy.deepcopy(self.predictions)
        missing[0]["claims"].pop()
        variants.append(missing)
        variants.append(self.predictions + [copy.deepcopy(self.predictions[0])])
        unknown = copy.deepcopy(self.predictions)
        unknown[0]["claims"][0]["claim_id"] = "unknown"
        variants.append(unknown)
        for predictions in variants:
            with self.subTest(predictions=predictions[:1]), self.assertRaises(ValueError):
                self.score(predictions)

    def test_invalid_status_and_duplicate_references_fail_schema(self):
        for field, value in (("status", "true"), ("supporting_records", ["x", "x"]),
                             ("scope", "world_truth")):
            changed = copy.deepcopy(self.predictions[0])
            changed["claims"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                parse_predictions(json.dumps(changed))

    def test_duplicate_json_keys_and_malformed_json_are_not_repaired(self):
        for text in ('{"packet_id":"a","packet_id":"b","claims":[]}', "not JSON"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_predictions(text)

    def test_prompt_export_withholds_gold_scopes_and_private_labels(self):
        for prompt in self.prompts:
            self.assertNotIn("private_world_truth", prompt)
            self.assertNotIn("description", prompt)
            for claim in prompt["claims"]:
                self.assertEqual(set(claim), {"claim_id", "text"})
            self.assertIn("response_schema", prompt)
            self.assertIn("no gold claim scopes", prompt["response_instructions"])

    def test_public_prompts_state_generic_update_and_scope_rules(self):
        for prompt in self.prompts:
            policy = prompt["evidence_policy"]
            self.assertIn("source owner", policy["update_authority"])
            self.assertIn("exact target_record_id", policy["update_authority"])
            self.assertIn("same source_owner", policy["supersession"])
            self.assertIn("same proposition_id", policy["supersession"])
            self.assertIn("changes no canonical record", policy["failed_update"])
            self.assertIn("may_support", policy["support_admission"])
            scopes = prompt["scope_definitions"]
            self.assertEqual(set(scopes), {"historical_assertion", "current_endorsement", "current_support"})
            self.assertIn("archived", scopes["historical_assertion"])
            self.assertIn("any active record", scopes["current_endorsement"])
            self.assertIn("separately surviving", scopes["current_support"])

    def test_external_prediction_replay_saves_hashes_and_exact_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            export = base / "public"
            manifest = export_run(DEFAULT_SUITE, export)
            supplied = base / "diagnostic.jsonl"
            supplied.write_text(self.prediction_text())
            result, provenance = score_run(DEFAULT_SUITE, export, supplied, base / "scored",
                                           "oracle_diagnostic", "unit test only")
            self.assertEqual(result["summary"]["n_claims"], 16)
            self.assertEqual(provenance["predictions_sha256"], sha256(supplied.read_bytes()))
            self.assertEqual(provenance["suite_sha256"], manifest["suite_sha256"])
            self.assertEqual((base / "scored/predictions.jsonl").read_bytes(), supplied.read_bytes())
            self.assertEqual(json.loads((base / "scored/metrics.json").read_text()), result)
            self.assertEqual(provenance["declared_prediction_origin"], "oracle_diagnostic")
            with self.assertRaises(FileExistsError):
                export_run(DEFAULT_SUITE, export)

    def test_modified_prompt_export_cannot_be_silently_scored(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            export_run(DEFAULT_SUITE, base / "public")
            (base / "public/prompts.jsonl").write_text("{}\n")
            predictions = base / "diagnostic.jsonl"
            predictions.write_text(self.prediction_text())
            with self.assertRaisesRegex(ValueError, "prompts"):
                score_run(DEFAULT_SUITE, base / "public", predictions, base / "scored")
            self.assertFalse((base / "scored").exists())

    def test_changed_suite_and_partial_run_are_rejected_before_writing_results(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            suite = base / "suite.json"
            suite.write_bytes(DEFAULT_SUITE.read_bytes())
            export_run(suite, base / "public")
            predictions = base / "partial.jsonl"
            predictions.write_text(json.dumps(self.predictions[0]) + "\n")
            with self.assertRaisesRegex(ValueError, "missing"):
                score_run(suite, base / "public", predictions, base / "scored")
            self.assertFalse((base / "scored").exists())
            suite.write_bytes(suite.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "suite changed"):
                score_run(suite, base / "public", predictions, base / "scored")

    def test_gold_results_cannot_be_written_inside_public_prompt_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            export_run(DEFAULT_SUITE, base / "public")
            predictions = base / "diagnostic.jsonl"
            predictions.write_text(self.prediction_text())
            with self.assertRaisesRegex(ValueError, "outside"):
                score_run(DEFAULT_SUITE, base / "public", predictions, base / "public/scored")


if __name__ == "__main__":
    unittest.main()
