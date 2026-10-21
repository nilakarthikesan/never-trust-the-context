"""Integration regressions for audited prototype failures; no network calls."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

from zt_pep.model import Entry, RequestContext, Decision
from zt_pep.pep import LLMRedactor, PolicyEnforcementPoint
from zt_pep.policy import Policy
from verify_walkthrough import production_decision, POLICY_PATH, ENTRIES


class LegacyIntegrationTests(unittest.TestCase):
    def test_pep_calls_llm_redactor_with_preserved_allowed_entries(self):
        calls = []
        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(
                message=SimpleNamespace(content="Allowed task detail."))])
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        allowed = Entry("ok", "Allowed task detail", C=0.0, I=1.0)
        blocked = Entry("secret", "Restricted internal identifier", C=1.0, I=1.0)
        pep = PolicyEnforcementPoint(redactor=LLMRedactor(client, "test-model"))
        result = pep.enforce("Original draft", [allowed, blocked], RequestContext(direction="External"))
        self.assertEqual(result.sanitized_action, "Allowed task detail.")
        self.assertEqual(len(calls), 1)
        prompt = calls[0]["messages"][0]["content"]
        self.assertIn("PERMITTED TASK FACTS", prompt)
        self.assertIn(allowed.content, prompt)
        self.assertIn(blocked.content, prompt)

    def test_walkthrough_uses_production_hard_deny_floor(self):
        policy = Policy.from_yaml(POLICY_PATH)
        e7 = next(row for row in ENTRIES if row[0] == "e7")
        result = production_decision(e7, "Downward", "comment", policy)
        self.assertEqual(result.decision, Decision.DENY)
        self.assertLess(result.risk, policy.theta["Downward"])
        self.assertIn("hard_deny_floor", result.reason)

    def test_regulated_entry_stays_denied_even_with_permissive_threshold(self):
        policy = Policy.from_yaml(POLICY_PATH)
        policy.theta["Downward"] = 100.0
        e5 = next(row for row in ENTRIES if row[0] == "e5")
        self.assertEqual(production_decision(e5, "Downward", "comment", policy).decision,
                         Decision.DENY)


if __name__ == "__main__":
    unittest.main()
