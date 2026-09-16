"""zt_pep: a zero-trust (Biba + Bell-LaPadula) policy layer for enterprise LLM agents.

Implements the design in design/pep-design.md:
  PIP (labels.py)  -> confidentiality C(e) and integrity I(e) labels + request context
  PDP (pdp.py)     -> BLP no-write-down + Biba no-write-up rules, weighted zero-trust score
  PEP (pep.py)     -> allow / redact / quarantine / deny enforcement at the write boundary

The package is dependency-light and runs fully offline for the deterministic core
(labels, decisions, keyword-based enforcement/judging). LLM-backed labelers/judges
that match CI-Work's prompt templates are optional and only needed for real runs.
"""

from .model import Entry, RequestContext, Decision
from .policy import Policy, DEFAULT_POLICY
from .labels import label_confidentiality, label_integrity, required_outbound_integrity
from .pdp import decide_entry, decide_all
from .pep import PolicyEnforcementPoint

__all__ = [
    "Entry",
    "RequestContext",
    "Decision",
    "Policy",
    "DEFAULT_POLICY",
    "label_confidentiality",
    "label_integrity",
    "required_outbound_integrity",
    "decide_entry",
    "decide_all",
    "PolicyEnforcementPoint",
]
