"""Inline enforcement: assemble the admissible context, then generate from it.

The difference from the post-hoc PEP in `pep.py` is not strength, it is direction. Post-hoc
receives a finished draft and can only *delete*, which leaves two failures unreachable:

  - an essential entry above the write ceiling is lost entirely, because deleting is the only
    available move and paraphrasing is not
  - a finding the agent dropped because it believed a low-integrity entry cannot be restored,
    because the PEP cannot add text the agent never wrote

Inline mode runs the PDP *before* generation and hands the writer a context that already
satisfies BLP and Biba: admitted entries verbatim, above-ceiling entries as label-checked
abstracts, and quarantined entries either withheld or explicitly marked non-authoritative.
Write-down then becomes structurally unreachable for the abstracted set rather than filtered,
which is the L2 argument in design/enforcement-mechanics.md §4.

Two writers, mirroring the judge/redactor split elsewhere in this package:

  - TemplateWriter: deterministic, no API key. Emits admitted context directly, so it measures
    the CEILING the admission policy permits rather than what a model actually does. Use it to
    isolate policy quality from model behavior, the same way eval-mode ground-truth C isolates
    the PDP from labeler error.
  - LLMWriter: the achieved number. Needs an OpenAI-compatible client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from .model import Entry, RequestContext, Decision, EntryDecision
from .policy import Policy, DEFAULT_POLICY
from .pdp import decide_all


@dataclass
class AdmittedContext:
    """What the writer is allowed to see. Nothing else reaches it."""

    verbatim: List[Entry] = field(default_factory=list)      # ALLOW: quotable
    abstracted: List[Entry] = field(default_factory=list)    # above ceiling, but abstract clears it
    attributed: List[Entry] = field(default_factory=list)    # QUARANTINE under attribute mode
    withheld: List[Entry] = field(default_factory=list)      # never reaches the writer

    def summary(self) -> str:
        return (f"verbatim={len(self.verbatim)} abstracted={len(self.abstracted)} "
                f"attributed={len(self.attributed)} withheld={len(self.withheld)}")


class Writer(Protocol):
    def compose(self, ctx: RequestContext, task: str, admitted: AdmittedContext) -> str: ...


class TemplateWriter:
    """Deterministic composer. Emits every admissible item, so metrics computed on its output
    are the upper bound achievable under the admission policy, not a model's achieved score."""

    def compose(self, ctx: RequestContext, task: str, admitted: AdmittedContext) -> str:
        parts: List[str] = []
        for e in admitted.verbatim:
            parts.append(e.content.strip())
        for e in admitted.abstracted:
            parts.append((e.abstract or "").strip())
        for e in admitted.attributed:
            snippet = e.content.strip().split(".")[0][:120]
            parts.append(f"An unverified note claims: {snippet}. I cannot treat that as "
                         f"established without a citation.")
        return " ".join(p for p in parts if p)


class LLMWriter:  # pragma: no cover
    """Generate the review from the admitted context only. The restricted specifics are absent
    from the prompt, so no-write-down is unreachable rather than filtered."""

    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def compose(self, ctx: RequestContext, task: str, admitted: AdmittedContext) -> str:
        lines = [f"- {e.content}" for e in admitted.verbatim]
        lines += [f"- {e.abstract}" for e in admitted.abstracted]
        unverified = [f"- {e.content}" for e in admitted.attributed]
        prompt = [
            f"Task: {task}",
            "",
            "Established context you may rely on and quote:",
            *lines,
        ]
        if unverified:
            prompt += [
                "",
                "Unverified claims. You may acknowledge these but must not treat them as "
                "established or let them determine your conclusion:",
                *unverified,
            ]
        prompt += [
            "",
            "Write the review. Use only the context above. Do not speculate beyond it.",
        ]
        resp = self.client.chat.completions.create(
            model=self.model, temperature=0.0,
            messages=[{"role": "user", "content": "\n".join(prompt)}],
        )
        return resp.choices[0].message.content.strip()


@dataclass
class InlineResult:
    action: str
    decisions: List[EntryDecision]
    admitted: AdmittedContext


class InlinePEP:
    """PDP before generation, so the writer never holds what it must not emit."""

    def __init__(self, policy: Policy = DEFAULT_POLICY, writer: Optional[Writer] = None):
        self.policy = policy
        self.writer = writer or TemplateWriter()

    def build_context(self, entries: List[Entry], ctx: RequestContext,
                      use_ground_truth_C: bool = True) -> tuple:
        decisions = decide_all(entries, ctx, self.policy, use_ground_truth_C=use_ground_truth_C)
        clr = self.policy.clr_C(ctx.direction)
        admitted = AdmittedContext()

        for d in decisions:
            e = d.entry
            if d.decision is Decision.ALLOW:
                admitted.verbatim.append(e)
                continue

            if d.decision is Decision.DENY:
                # An above-ceiling entry may still carry its task value forward if it has an
                # abstract that clears the ceiling on its own. Regulated entries do not get
                # this path: design/enforcement-mechanics.md §6 routes them to L3 or to
                # never being retrieved.
                if e.abstract and not e.regulated and e.abstract_C is not None \
                        and e.abstract_C <= clr:
                    admitted.abstracted.append(e)
                else:
                    admitted.withheld.append(e)
                continue

            # QUARANTINE: integrity too low to ground the artifact.
            if self.policy.quarantine_mode == "attribute":
                admitted.attributed.append(e)
            else:
                admitted.withheld.append(e)

        return decisions, admitted

    def generate(self, entries: List[Entry], ctx: RequestContext, task: str = "",
                 use_ground_truth_C: bool = True) -> InlineResult:
        decisions, admitted = self.build_context(entries, ctx, use_ground_truth_C)
        action = self.writer.compose(ctx, task, admitted)
        return InlineResult(action=action, decisions=decisions, admitted=admitted)
