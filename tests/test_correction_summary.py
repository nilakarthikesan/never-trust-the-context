"""Coverage/provenance regressions; fixtures here are explicitly not model results."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from run_correction_eval import build_materials, prompt_bytes
from correction_scope_demo import load_packets
from summarize_correction_models import positive_support_gold, summarize


class SummaryTests(unittest.TestCase):
    def make_run(self, directory, *, complete=False):
        suite = ROOT / "eval/fixtures/correction_pilot.json"
        prompts, gold, _ = build_materials(load_packets(suite))
        inputs = prompt_bytes(prompts)
        # Oracle-derived rows exist only inside a temporary software test.
        predictions = b""
        if complete:
            predictions = b"".join((json.dumps({"packet_id": p["packet_id"], "claims": [
                {"claim_id": c["claim_id"], **gold[p["packet_id"], c["claim_id"]]}
                for c in p["claims"]]}) + "\n").encode() for p in prompts)
        (directory / "public_inputs.jsonl").write_bytes(inputs)
        (directory / "predictions.jsonl").write_bytes(predictions)
        (directory / "run_manifest.json").write_text(json.dumps({
            "inputs_sha256": hashlib.sha256(inputs).hexdigest(), "condition": "raw_history",
            "origin": "oracle_diagnostic_NOT_LLM", "config": {"model": "fake-test-only"}}))
        (directory / "run_summary.json").write_text(json.dumps({
            "predictions_sha256": hashlib.sha256(predictions).hexdigest(),
            "n_valid": len(prompts) if complete else 0, "n_packets": len(prompts),
            "complete": complete, "outcomes": [], "provider_requests": 0,
            "reported_cost_usd_at_declared_rates": 0}))
        return suite

    def test_empty_failure_has_no_model_accuracy(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            suite = self.make_run(directory)
            result = summarize(directory, suite)
            self.assertEqual(result["prediction_coverage"], 0)
            self.assertIsNone(result["model_metrics"])
            self.assertFalse(result["complete"])

    def test_changed_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            suite = self.make_run(directory)
            with (directory / "public_inputs.jsonl").open("ab") as stream:
                stream.write(b" ")
            with self.assertRaisesRegex(ValueError, "manifest"):
                summarize(directory, suite)

    def test_complete_diagnostic_preserves_its_nonmodel_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            suite = self.make_run(directory, complete=True)
            result = summarize(directory, suite)
            self.assertTrue(result["complete"])
            self.assertEqual(result["origin"], "oracle_diagnostic_NOT_LLM")
            self.assertEqual(result["model_metrics"]["summary"]["all_fields_correct_rate"], 1)

    def test_unbacked_auxiliary_is_not_an_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            suite = self.make_run(directory)
            manifest_path = directory / "run_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["condition"] = "regeneration_audit"
            manifest_path.write_text(json.dumps(manifest))
            packet = json.loads((directory / "public_inputs.jsonl").read_text().splitlines()[0])
            trace = directory / "traces" / hashlib.sha256(packet["packet_id"].encode()).hexdigest()[:24]
            trace.mkdir(parents=True)
            (trace / "auxiliary.json").write_text(json.dumps({"packet_id": packet["packet_id"], "emitted_candidates": []}))
            with self.assertRaisesRegex(ValueError, "saved probe result"):
                summarize(directory, suite)

    def test_negative_query_cannot_grade_positive_candidate(self):
        private = load_packets(ROOT / "eval/fixtures/correction_pilot.json")
        prompts, gold, _ = build_materials(private)
        query = next(c for c in private[0]["claims"] if c["kind"] == "current_support")
        query["value"] = False
        with self.assertRaisesRegex(ValueError, "positive query"):
            positive_support_gold(private[0], prompts[0], gold)


if __name__ == "__main__":
    unittest.main()
