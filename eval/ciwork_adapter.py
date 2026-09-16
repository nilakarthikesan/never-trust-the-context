"""Adapter: map CI-Work data (fixture or real formatted_trajectory.json) into zt_pep objects.

Real CI-Work `formatted_trajectory.json` entries (see notes/ci-work-reading-note.md §9) carry:
  - case.sensitive_data / case.essential_data : ground-truth items with 'Content' and 'Source'
  - sensitive_entries / essential_entries      : matched retrieval entries
  - final_action                               : "Action: GmailSendEmail\nAction Input: {...}"
  - case.detailed_plot                         : outline for the judge
  - case.seed.type                             : information-flow direction
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zt_pep.model import Entry, RequestContext


@dataclass
class Case:
    name: str
    ctx: RequestContext
    sensitive: List[Entry]
    essential: List[Entry]
    undefended_action: str
    outline: str = ""


def _entry_from_ci(item: dict, idx: int, prefix: str, kind: str) -> Entry:
    content = item.get("Content") or item.get("Input Abstract") or item.get("content") or ""
    source = item.get("Source") or item.get("source") or ""
    category = item.get("category") or item.get("category_name") or None
    return Entry(id=f"{prefix}_{idx}", content=content, source=source, kind=kind, category=category)


def load_fixture(path: str) -> List[Case]:
    with open(path) as f:
        raw = json.load(f)
    cases = []
    for c in raw:
        ctx = RequestContext(
            sender=c.get("sender", ""),
            recipient=c.get("recipient", ""),
            direction=c.get("direction", "Lateral"),
            channel=c.get("channel", ""),
        )
        sensitive = [_entry_from_ci(e, i, "sens", "sensitive") for i, e in enumerate(c["sensitive"])]
        essential = [_entry_from_ci(e, i, "ess", "essential") for i, e in enumerate(c["essential"])]
        # fixture provides explicit id / already-clean content
        for e, src in zip(sensitive, c["sensitive"]):
            e.id = src.get("id", e.id)
        for e, src in zip(essential, c["essential"]):
            e.id = src.get("id", e.id)
        cases.append(Case(
            name=c["name"], ctx=ctx, sensitive=sensitive, essential=essential,
            undefended_action=c["undefended_action"], outline=c.get("outline", ""),
        ))
    return cases


def _action_text(final_action: str) -> str:
    """Extract the human-readable body from a CI-Work final_action string."""
    m = re.search(r"Action Input:\s*(\{.*\})", final_action, re.DOTALL)
    if not m:
        return final_action
    try:
        payload = json.loads(m.group(1))
    except Exception:
        return final_action
    # Common body keys across Gmail/Slack/Messenger tools
    for k in ("body", "message", "content", "text", "post"):
        if k in payload and isinstance(payload[k], str):
            return payload[k]
    return json.dumps(payload)


def load_formatted_trajectory(path: str) -> List[Case]:
    """Load a real CI-Work formatted_trajectory.json into Cases."""
    with open(path) as f:
        data = json.load(f)
    cases = []
    for i, entry in enumerate(data):
        case = entry.get("case", {})
        seed = case.get("seed", {}) if isinstance(case.get("seed"), dict) else {}
        direction = seed.get("type") or case.get("type") or "Lateral"
        ctx = RequestContext(
            sender=seed.get("data_sender", ""),
            recipient=seed.get("data_recipient", ""),
            direction=direction,
            channel=entry.get("final_action", "").split("\n")[0].replace("Action:", "").strip(),
        )
        sens_src = entry.get("sensitive_data") or case.get("sensitive_data") or []
        ess_src = entry.get("essential_data") or case.get("essential_data") or []
        sensitive = [_entry_from_ci(e, j, "sens", "sensitive") for j, e in enumerate(sens_src)]
        essential = [_entry_from_ci(e, j, "ess", "essential") for j, e in enumerate(ess_src)]
        cases.append(Case(
            name=str(entry.get("case_idx", entry.get("name", i))),
            ctx=ctx,
            sensitive=sensitive,
            essential=essential,
            undefended_action=_action_text(entry.get("final_action", "")),
            outline=case.get("detailed_plot", ""),
        ))
    return cases
