"""Policy configuration: org lattice, per-direction weights/thresholds, provenance rubric.

Every number the paper reports traces to a Policy instance. Defaults live here in Python
so the package runs with no external files; an optional YAML loader is provided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


# Recipient confidentiality clearance clr_C(r) by direction (design/pep-design.md §4).
DEFAULT_CLEARANCE: Dict[str, float] = {
    "Downward": 0.7,
    "Upward": 0.9,
    "Lateral": 0.6,
    "Diagonal": 0.4,
    "External": 0.2,
}

# Required outbound integrity lvl_I(a_fin) by direction (high water mark for the write).
# Calibrated so genuinely low-trust sources (Slack/chat ~0.4) fail, while authoritative
# documents (Notion/email ~0.7, contracts/board ~0.9) pass. See design/pep-design.md.
DEFAULT_REQUIRED_INTEGRITY: Dict[str, float] = {
    "Downward": 0.45,
    "Upward": 0.55,
    "Lateral": 0.45,
    "Diagonal": 0.6,
    "External": 0.6,
}

# Per-direction confidentiality/integrity weights and risk threshold theta_d.
DEFAULT_WC: Dict[str, float] = {d: 1.0 for d in DEFAULT_CLEARANCE}
DEFAULT_WI: Dict[str, float] = {
    "Downward": 0.8,
    "Upward": 1.0,
    "Lateral": 0.8,
    "Diagonal": 1.0,
    "External": 1.2,   # external artifacts most sensitive to low-integrity contamination
}
DEFAULT_THETA: Dict[str, float] = {d: 0.15 for d in DEFAULT_CLEARANCE}


# Integrity provenance rubric (design/pep-design.md §1.3). Base score by source channel.
DEFAULT_SOURCE_INTEGRITY: Dict[str, float] = {
    "contract": 0.95,
    "legal": 0.95,
    "ledger": 0.9,
    "finance": 0.85,
    "board": 0.9,
    "notion": 0.7,
    "document": 0.75,
    "doc": 0.75,
    "email": 0.7,
    "gmail": 0.7,
    "calendar": 0.7,
    "meeting": 0.65,
    "slack": 0.4,
    "messenger": 0.4,
    "chat": 0.35,
    "dm": 0.35,
}

# Content markers that lower integrity (unverified / manipulable / fabricated).
# Downward markers need no clamp: an attacker who lowers their own content's integrity
# achieves nothing, so the asymmetry is safe.
DEFAULT_LOW_INTEGRITY_MARKERS = (
    "gossip", "rumor", "rumour", "speculat", "unconfirmed", "draft", "tentative",
    "let's claim", "lets claim", "imply", "pretend", "fabricat", "off the record",
    "heard that", "i think", "maybe", "allegedly", "complain",
)

# Content markers that raise integrity (authoritative artifacts).
# "approved" and "final" are deliberately absent: they are the most trivially writable
# words in the set, and an uplift marker on an author-controlled channel is an injection
# vector. See design/weight-calibration.md §3.1.
DEFAULT_HIGH_INTEGRITY_MARKERS = (
    "signed", "executed contract", "audited", "official",
    "board minutes", "resolution", "of record", "policy", "filing",
)

DEFAULT_INTEGRITY_PRIOR = 0.5   # when no signal fires (stated default; fixes Tian-Song gap)

# Integrity is a property of PROVENANCE; content cannot vouch for its own provenance.
# A high-integrity content marker may therefore raise I only by a bounded amount above
# the source channel's base score, never to an absolute target.
DEFAULT_MAX_CONTENT_UPLIFT = 0.25

# Channels whose content is written by the party under review. No content marker can
# raise these past the ceiling, because the author controls the marker too.
DEFAULT_AUTHOR_CONTROLLED_SOURCES = (
    "pr_description", "pr_body", "author_comment", "code_comment", "todo",
    "commit_message", "self_report",
)
DEFAULT_AUTHOR_CONTROLLED_CEILING = 0.25

# Confidentiality at or above this level is never eligible for the theta override,
# regardless of how small its margin over the recipient's clearance is.
# See design/weight-calibration.md §4.4.
DEFAULT_HARD_DENY_FLOOR = 0.75


@dataclass
class Policy:
    clearance: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_CLEARANCE))
    required_integrity: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_REQUIRED_INTEGRITY))
    w_C: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WC))
    w_I: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WI))
    theta: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THETA))

    source_integrity: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_SOURCE_INTEGRITY))
    low_integrity_markers: tuple = DEFAULT_LOW_INTEGRITY_MARKERS
    high_integrity_markers: tuple = DEFAULT_HIGH_INTEGRITY_MARKERS
    integrity_prior: float = DEFAULT_INTEGRITY_PRIOR

    # provenance-over-content clamps (design/weight-calibration.md §3.1)
    max_content_uplift: float = DEFAULT_MAX_CONTENT_UPLIFT
    author_controlled_sources: tuple = DEFAULT_AUTHOR_CONTROLLED_SOURCES
    author_controlled_ceiling: float = DEFAULT_AUTHOR_CONTROLLED_CEILING

    # regulated / high-C entries are never released by the risk threshold (§4.4)
    hard_deny_floor: float = DEFAULT_HARD_DENY_FLOOR

    # slack terms (epsilons) so labels near a boundary are not over-blocked
    eps_C: float = 0.0
    eps_I: float = 0.0

    # enforcement
    quarantine_mode: str = "drop"      # drop | attribute
    pressure_integrity_penalty: float = 0.15  # penalty for content present only under explicit pressure

    def clr_C(self, direction: str) -> float:
        return self.clearance.get(direction, 0.2)

    def lvl_I(self, direction: str) -> float:
        return self.required_integrity.get(direction, 0.7)

    @classmethod
    def from_yaml(cls, path: str) -> "Policy":
        import yaml  # optional dependency

        with open(path) as f:
            data = yaml.safe_load(f) or {}
        base = cls()
        for k, v in data.items():
            if hasattr(base, k):
                setattr(base, k, v)
        return base


DEFAULT_POLICY = Policy()
