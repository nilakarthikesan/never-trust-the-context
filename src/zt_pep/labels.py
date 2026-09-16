"""PIP: assign confidentiality C(e) and integrity I(e) labels.

C(e): eval mode uses CI-Work ground truth (sensitive=1, essential=0); inference mode
      would call a CI classifier (reusing CI-Work's tag_context.j2). Stubbed heuristic here.
I(e): a transparent provenance rubric (design/pep-design.md §1.3). Deterministic and auditable.
"""

from __future__ import annotations

from typing import Optional

from .model import Entry, RequestContext
from .policy import Policy, DEFAULT_POLICY


def label_confidentiality(entry: Entry, ctx: RequestContext, policy: Policy = DEFAULT_POLICY,
                          use_ground_truth: bool = True) -> float:
    """Return C(e) in [0,1]. High => disclosure is inappropriate for the recipient."""
    if use_ground_truth and entry.kind in ("sensitive", "essential"):
        return 1.0 if entry.kind == "sensitive" else 0.0

    # Inference-mode heuristic fallback (placeholder for the CI classifier).
    text = entry.content.lower()
    high_conf_hits = (
        "confidential", "internal only", "do not share", "walk-away", "walk away",
        "budget", "salary", "compensation", "acquisition", "m&a", "litigation",
        "credential", "password", "ssn", "patient", "board",
    )
    score = 0.2
    for h in high_conf_hits:
        if h in text:
            score = max(score, 0.85)
    return score


def label_integrity(entry: Entry, ctx: RequestContext, policy: Policy = DEFAULT_POLICY) -> float:
    """Return I(e) in [0,1] from a provenance rubric. High => authoritative/trustworthy origin.

    Signals: source channel, artifact-type keywords, manipulation markers, pressure origin.
    """
    text = entry.content.lower()
    source = (entry.source or "").lower()

    # 1) base score from source channel
    base = None
    for key, val in policy.source_integrity.items():
        if key in source:
            base = val if base is None else max(base, val)
    if base is None:
        base = policy.integrity_prior

    score = base

    # 2) high-integrity artifact markers pull up
    for m in policy.high_integrity_markers:
        if m in text:
            score = max(score, 0.85)
            break

    # 3) low-integrity / manipulation markers pull down (strongest signal)
    fabrication = any(m in text for m in ("let's claim", "lets claim", "fabricat", "pretend", "imply", "off the record"))
    for m in policy.low_integrity_markers:
        if m in text:
            score = min(score, 0.35)
            break
    if fabrication:
        score = min(score, 0.15)  # content proposing deception is forced low

    # 4) pressure-introduced content penalty
    if ctx.pressure_type == "intentional":
        score = max(0.0, score - policy.pressure_integrity_penalty)

    return round(max(0.0, min(1.0, score)), 3)


def required_outbound_integrity(ctx: RequestContext, policy: Policy = DEFAULT_POLICY) -> float:
    """lvl_I(a_fin): the integrity high-water mark the outbound artifact must meet."""
    return policy.lvl_I(ctx.direction)


def label_entry(entry: Entry, ctx: RequestContext, policy: Policy = DEFAULT_POLICY,
                use_ground_truth_C: bool = True) -> Entry:
    """Populate entry.C and entry.I in place and return it."""
    if entry.C is None:
        entry.C = label_confidentiality(entry, ctx, policy, use_ground_truth=use_ground_truth_C)
    if entry.I is None:
        entry.I = label_integrity(entry, ctx, policy)
    return entry
