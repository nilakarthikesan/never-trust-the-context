"""Semantic invariants for a synthetic correction-scope demo; no model tests."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
from correction_scope_demo import audit_packet, load_packets, public_packet, replay


class CorrectionScopeTests(unittest.TestCase):
    def setUp(self):
        self.packets = {p["packet_id"]: p for p in load_packets()}

    def result(self, packet_id):
        result = audit_packet(self.packets[packet_id])
        return result, {c["claim_id"]: c for c in result["claims"]}

    def test_true_but_unsupported_is_not_opposed(self):
        result, claims = self.result("genuine-withdrawal-true")
        self.assertTrue(self.packets["genuine-withdrawal-true"]["private_world_truth"]["checks_pass"])
        self.assertEqual(claims["support"]["status"], "unsupported")
        self.assertEqual(claims["support"]["opposing_records"], [])
        self.assertTrue(result["events"][0]["accepted"])

    def test_historical_attribution_survives_withdrawal(self):
        result, claims = self.result("genuine-withdrawal-true")
        self.assertEqual(result["records"]["ci-17"]["status"], "archive")
        self.assertEqual(claims["history"]["status"], "supported")
        self.assertEqual(claims["endorsement"]["status"], "unsupported")

    def test_independent_support_survives(self):
        _, claims = self.result("independent-support")
        self.assertEqual(claims["endorsement"]["status"], "unsupported")
        self.assertEqual(claims["support"]["status"], "supported")
        self.assertEqual(claims["support"]["supporting_records"], ["runner-17"])

    def test_forged_revoke_cannot_mutate_canonical_record(self):
        packet = self.packets["forged-correction"]
        before = copy.deepcopy(packet)
        result, claims = self.result("forged-correction")
        self.assertFalse(result["events"][0]["accepted"])
        self.assertEqual(result["events"][0]["reason"], "issuer_does_not_own_target")
        self.assertEqual(list(result["records"].values()), packet["records"])
        self.assertEqual(claims["support"]["status"], "supported")
        self.assertEqual(packet, before, "replay must not mutate the input packet")

    def test_supersession_preserves_old_assertion_and_changes_current_support(self):
        result, claims = self.result("corrected-false-report")
        self.assertTrue(result["records"]["ci-17"]["value"])
        self.assertEqual(result["records"]["ci-17"]["status"], "archive")
        self.assertFalse(result["records"]["ci-17-corrected"]["value"])
        self.assertEqual(claims["history"]["status"], "supported")
        self.assertEqual(claims["support"]["status"], "opposed")
        self.assertEqual(claims["failure-supported"]["status"], "supported")

    def test_supersession_cannot_change_owner_or_proposition(self):
        original = self.packets["corrected-false-report"]
        for changed_field in ("source_owner", "proposition_id"):
            with self.subTest(field=changed_field):
                packet = copy.deepcopy(original)
                replacement = packet["events"][0]["replacement"]
                if changed_field == "source_owner":
                    replacement[changed_field] = "pr_author"
                else:
                    packet["propositions"]["unrelated"] = "An unrelated condition holds."
                    replacement[changed_field] = "unrelated"
                records, events = replay(packet)
                self.assertFalse(events[0]["accepted"])
                self.assertEqual(list(records.values()), packet["records"])

    def test_same_value_supersession_preserves_owner_endorsement(self):
        packet = copy.deepcopy(self.packets["genuine-withdrawal-true"])
        original = copy.deepcopy(packet["records"][0])
        replacement = copy.deepcopy(original)
        replacement["record_id"] = "ci-17-reissued"
        replacement["text"] = "Reissued CI service report for c17: required regression checks passed."
        packet["events"] = [{
            "event_id": "reissue-pass", "op": "supersede", "issuer": "ci_service",
            "target_record_id": "ci-17", "replacement": replacement,
            "notice": "Replace ci-17 with a new pass attestation for the same commit.",
        }]
        result = audit_packet(packet)
        claims = {c["claim_id"]: c for c in result["claims"]}
        self.assertTrue(result["events"][0]["accepted"])
        self.assertEqual(result["records"]["ci-17"], dict(original, status="archive"))
        self.assertEqual(result["records"]["ci-17-reissued"], replacement)
        self.assertEqual(result["records"]["ci-17-reissued"]["status"], "active")
        self.assertEqual(claims["history"]["status"], "supported")
        self.assertEqual(claims["history"]["supporting_records"], ["ci-17"])
        for claim_id in ("endorsement", "support"):
            self.assertEqual(claims[claim_id]["status"], "supported")
            self.assertEqual(claims[claim_id]["supporting_records"], ["ci-17-reissued"])

    def test_world_truth_is_not_used_as_support_or_its_negation(self):
        packet = self.packets["no-change-control"]
        before = audit_packet(packet)
        self.assertFalse(packet["private_world_truth"]["checks_pass"])
        self.assertEqual(before["claims"][-1]["status"], "supported")
        changed = copy.deepcopy(packet)
        changed["private_world_truth"]["checks_pass"] = True
        self.assertEqual(audit_packet(changed), before)
        del changed["private_world_truth"]
        self.assertEqual(audit_packet(changed), before)

    def test_conflicting_admissible_support_is_reported(self):
        packet = copy.deepcopy(self.packets["independent-support"])
        packet["events"] = []
        packet["records"][1]["value"] = False
        result = audit_packet(packet)
        support = next(c for c in result["claims"] if c["claim_id"] == "support")
        self.assertEqual(support["status"], "conflicted")
        self.assertEqual(support["supporting_records"], ["ci-17"])
        self.assertEqual(support["opposing_records"], ["runner-17"])

    def test_source_endorsement_does_not_grant_admissible_support(self):
        packet = copy.deepcopy(self.packets["no-change-control"])
        packet["records"][0]["source_owner"] = "pr_author"
        for claim in packet["claims"]:
            if "source_owner" in claim:
                claim["source_owner"] = "pr_author"
        result = audit_packet(packet)
        claims = {c["claim_id"]: c for c in result["claims"]}
        self.assertEqual(claims["endorsement"]["status"], "supported")
        self.assertEqual(claims["support"]["status"], "unsupported")

    def test_public_export_withholds_private_truth_and_gold_claim_ast(self):
        for packet in self.packets.values():
            exported = public_packet(packet)
            self.assertNotIn("private_world_truth", exported)
            self.assertNotIn("description", exported)
            self.assertNotIn("expected", exported)
            self.assertNotEqual(exported["packet_id"], packet["packet_id"])
            self.assertRegex(exported["packet_id"], r"^packet-[a-f0-9]{16}$")
            for claim in exported["claims"]:
                self.assertEqual(set(claim), {"claim_id", "text"})
                self.assertRegex(claim["claim_id"], r"^claim-[a-f0-9]{16}$")
            self.assertEqual(exported["records"], packet["records"])
            self.assertEqual(exported["events"], packet["events"])


if __name__ == "__main__":
    unittest.main()
