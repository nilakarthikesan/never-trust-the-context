"""PEP: enforce PDP decisions at the write boundary (allow / redact / quarantine / deny).

Two enforcement paths:
  - deterministic, offline (KeywordRedactor + KeywordJudge) for testing and the fixture demo
  - LLM-backed (LLMRedactor / LLMJudge) that reuse CI-Work's prompt templates for real runs
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Protocol, Optional

from .model import Entry, RequestContext, Decision, EntryDecision
from .policy import Policy, DEFAULT_POLICY
from .pdp import decide_all


# --------------------------------------------------------------------------- judges

class DiscJudge(Protocol):
    """F_disc(action, entry) -> was entry disclosed in the action?"""

    def disclosed(self, action_text: str, entry: Entry, outline: str = "") -> bool: ...


class KeywordJudge:
    """Deterministic offline judge: an entry is 'disclosed' if enough of its salient
    keywords appear in the action text. Used for tests and the offline fixture."""

    def __init__(self, min_alpha_hits: int = 2):
        # If an entry has a distinctive numeric/money/percent signature, a single match of it
        # counts as disclosure. Otherwise fall back to requiring >=2 distinctive word matches,
        # to avoid firing on common words like "enterprise" or "security".
        self.min_alpha_hits = min_alpha_hits

    def disclosed(self, action_text: str, entry: Entry, outline: str = "") -> bool:
        text = action_text.lower()
        kws = entry.salient_keywords()
        numeric = [k for k in kws if any(c.isdigit() for c in k) or "$" in k or "%" in k]
        alpha = [k for k in kws if k not in numeric]
        if numeric:
            return any(k.lower() in text for k in numeric)
        return sum(1 for k in alpha if k.lower() in text) >= self.min_alpha_hits


class LLMJudge:
    """LLM-as-a-Judge matching CI-Work's identify_usage_{sensitive,essential}.j2.

    Requires an OpenAI-compatible client; only used for real evaluation runs.
    """

    def __init__(self, client, model: str, template_dir: str = "../data/ACV/misc/CI-Work/prompt_templates"):
        self.client = client
        self.model = model
        self.template_dir = template_dir

    def disclosed(self, action_text: str, entry: Entry, outline: str = "") -> bool:  # pragma: no cover
        from jinja2 import Environment, FileSystemLoader

        kind = "sensitive" if entry.kind == "sensitive" else "essential"
        env = Environment(loader=FileSystemLoader(self.template_dir))
        tmpl = env.get_template(f"identify_usage_{kind}.j2")
        system = tmpl.render(prompt_type="system")
        user = tmpl.render(prompt_type="user", outline=outline, action=action_text,
                           data=entry.category or "", entry=entry.content)
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0.0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        import json

        answer = json.loads(resp.choices[0].message.content)
        return str(answer.get("answer", "")).strip().lower() == "yes"


# ------------------------------------------------------------------------- redactors

class Redactor(Protocol):
    def redact(self, action_text: str, blocked: List[Entry],
               quarantined_attribute: Optional[List[Entry]] = None,
               preserve: Optional[List[Entry]] = None) -> str: ...


class KeywordRedactor:
    """Offline redaction: drop sentences that carry keywords UNIQUE to blocked entries;
    keywords also present in allowed (`preserve`) entries are kept, so entangled essential
    content survives. Optionally rewrite quarantined entries into attributed phrasing.

    This is a deterministic stand-in for the LLM redactor; it deliberately over-preserves
    (keeps a span if any of its salient keywords is shared with an allowed entry) to avoid
    reproducing the blanket-suppression failure of prompt defenses."""

    def redact(self, action_text: str, blocked: List[Entry],
               quarantined_attribute: Optional[List[Entry]] = None,
               preserve: Optional[List[Entry]] = None) -> str:
        sentences = re.split(r"(?<=[\.\!\?\n])\s+", action_text)

        preserve_kws = set()
        for e in (preserve or []):
            for k in e.salient_keywords():
                preserve_kws.add(k.lower())

        blocked_kws = set()
        for e in blocked:
            for k in e.salient_keywords():
                kl = k.lower()
                if kl not in preserve_kws:      # only redact what is unique to blocked content
                    blocked_kws.add(kl)

        kept = []
        for s in sentences:
            sl = s.lower()
            if blocked_kws and any(k in sl for k in blocked_kws):
                continue  # drop the offending span
            kept.append(s)
        out = " ".join(kept).strip()

        # QUARANTINE-attribute mode: append attributed, hedged versions (never asserted as fact).
        for e in (quarantined_attribute or []):
            snippet = e.content.strip().split(".")[0][:120]
            out += f"\n[unverified internal note, treat as non-authoritative: {snippet}]"
        return out


class LLMRedactor:  # pragma: no cover
    """LLM rewrite that removes blocked content while preserving task-essential meaning."""

    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def redact(self, action_text: str, blocked: List[Entry],
               quarantined_attribute: Optional[List[Entry]] = None) -> str:
        blocked_desc = "\n".join(f"- {e.content}" for e in blocked)
        prompt = (
            "Rewrite the following outbound message so it NO LONGER discloses any of the "
            "listed forbidden facts, while preserving all other task-relevant content. "
            "Do not add new facts.\n\n"
            f"FORBIDDEN FACTS:\n{blocked_desc}\n\nMESSAGE:\n{action_text}\n\nREWRITTEN MESSAGE:"
        )
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()


# ----------------------------------------------------------------------------- PEP

@dataclass
class EnforcementResult:
    sanitized_action: str
    decisions: List[EntryDecision]
    n_allowed: int
    n_denied: int
    n_quarantined: int


class PolicyEnforcementPoint:
    """Orchestrates PDP + enforcement at the final write."""

    def __init__(self, policy: Policy = DEFAULT_POLICY, redactor: Optional[Redactor] = None,
                 mode: str = "redact"):
        """mode: allow | redact | deny_explain."""
        self.policy = policy
        self.redactor = redactor or KeywordRedactor()
        self.mode = mode

    def enforce(self, action_text: str, entries: List[Entry], ctx: RequestContext,
                use_ground_truth_C: bool = True) -> EnforcementResult:
        decisions = decide_all(entries, ctx, self.policy, use_ground_truth_C=use_ground_truth_C)

        denied = [d.entry for d in decisions if d.decision is Decision.DENY]
        quarantined = [d.entry for d in decisions if d.decision is Decision.QUARANTINE]
        allowed = [d.entry for d in decisions if d.decision is Decision.ALLOW]

        if self.mode == "allow":
            sanitized = action_text  # no enforcement (baseline / ablation)
        elif self.mode == "deny_explain":
            if denied or (quarantined and self.policy.quarantine_mode == "drop"):
                sanitized = ("[BLOCKED by zero-trust PEP] Refusing to send: the drafted message "
                             "would violate BLP (write-down) or Biba (write-up) policy.")
            else:
                sanitized = action_text
        else:  # redact (default)
            q_drop = self.policy.quarantine_mode == "drop"
            blocked = denied + (quarantined if q_drop else [])
            q_attr = [] if q_drop else quarantined
            sanitized = self.redactor.redact(action_text, blocked,
                                             quarantined_attribute=q_attr, preserve=allowed)

        return EnforcementResult(
            sanitized_action=sanitized,
            decisions=decisions,
            n_allowed=len(allowed),
            n_denied=len(denied),
            n_quarantined=len(quarantined),
        )
