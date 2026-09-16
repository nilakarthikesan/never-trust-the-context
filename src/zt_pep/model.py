"""Core data types shared across PIP / PDP / PEP."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


DIRECTIONS = ("Upward", "Downward", "Lateral", "Diagonal", "External")

# Final-action tools in CI-Work (the write boundary). See format_trajectory.py.
FINAL_ACTION_TOOLS = (
    "GmailSendEmail",
    "SlackSendMessage",
    "FacebookManagerCreatePost",
    "GoogleFormFillerSubmitForm",
    "NotionManagerSharePage",
    "MessengerShareFile",
    "MessengerSendMessage",
)


class Decision(str, Enum):
    """PEP decision for a single candidate entry."""

    ALLOW = "allow"          # passes both BLP and Biba
    DENY = "deny"            # BLP no-write-down failure -> drop
    QUARANTINE = "quarantine"  # Biba no-write-up failure -> attribute or drop, never assert as fact

    def blocks_inclusion(self, quarantine_mode: str = "drop") -> bool:
        """Whether this decision removes the entry's content from the outbound artifact."""
        if self is Decision.ALLOW:
            return False
        if self is Decision.DENY:
            return True
        # QUARANTINE
        return quarantine_mode == "drop"


@dataclass
class Entry:
    """A retrieved context entry (an 'object' in BLP/Biba terms)."""

    id: str
    content: str
    source: str = ""                 # originating tool/channel, e.g. "Slack", "Notion", "Email"
    kind: Optional[str] = None       # "sensitive" | "essential" | "corrupting" ground truth, or None
    category: Optional[str] = None   # CI-Work 9-category label if known
    C: Optional[float] = None        # confidentiality label in [0,1]
    I: Optional[float] = None        # integrity label in [0,1]
    regulated: bool = False          # PII / PCI / HIPAA / export-controlled: never theta-overridable

    def salient_keywords(self, max_k: int = 8) -> list[str]:
        """Cheap, deterministic keyword signature used by the offline judge/redactor.

        Not used by the LLM-backed path. Picks distinctive numeric/long tokens.
        """
        import re

        toks = re.findall(r"[A-Za-z0-9$%\.,\-]+", self.content)
        scored = []
        for t in toks:
            core = t.strip(".,")
            if not core:
                continue
            has_sym = ("$" in t) or ("%" in t)
            has_digit = any(c.isdigit() for c in core)
            score = 0
            if has_digit:
                # keep only distinctive numbers: money/percent, or >=3 chars
                # (bare 1-2 digit tokens like "15" or "30" are too ambiguous to redact on)
                if has_sym or len(core) >= 3:
                    score += 3
                    if has_sym:
                        score += 2
            elif len(core) >= 8:
                score += 1
            if score > 0:
                scored.append((score, core))
        scored.sort(key=lambda x: (-x[0], x[1]))
        seen, out = set(), []
        for _, t in scored:
            tl = t.lower()
            if tl and tl not in seen:
                seen.add(tl)
                out.append(t)
            if len(out) >= max_k:
                break
        return out


@dataclass
class RequestContext:
    """The zero-trust request: who is sending what to whom, over which channel."""

    sender: str = ""
    recipient: str = ""
    direction: str = "Lateral"       # one of DIRECTIONS
    channel: str = ""                # final-action tool name
    pressure_type: str = "regular"   # regular | intentional | unintentional (CI-Work)

    def __post_init__(self):
        if self.direction not in DIRECTIONS:
            # tolerate lowercase / unknown; default to the strictest reasonable prior
            norm = self.direction.capitalize()
            self.direction = norm if norm in DIRECTIONS else "Lateral"


@dataclass
class EntryDecision:
    entry: Entry
    decision: Decision
    conf_ok: bool
    integ_ok: bool
    risk: float
    reason: str = ""
