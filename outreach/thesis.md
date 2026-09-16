# The Thesis (locked) — and the paper that follows from it

One page. Lead the meeting with this.

---

## The thesis

> Enterprise LLM agents fail because they treat every retrieved item as both **sendable and trustworthy** the moment it enters the context window. Placing a **zero-trust checkpoint at the moment the agent sends** — which labels each retrieved item on two independent axes (*too secret to send?* / *too unreliable to rely on?*) and enforces **Bell–LaPadula** plus **Biba** — reduces both leakage **and** a class of integrity failure CI-Work cannot currently measure, **without the usefulness collapse that prompt-based defenses cause.**

## Why it's defensible in one sentence

CI-Work's own conclusion says the fix must be **architectural**, not a bigger model or a better prompt. We build that architecture, and add the **integrity** axis they left out.

## The conceptual core (the whole paper in one table)

|  | **Trustworthy** | **Untrustworthy** |
|---|---|---|
| **Secret** | walk-away price — *don't send, but it's real* | fabricated tactic — *don't send AND don't rely on* |
| **Shareable** | signed contract — *safe both ways* | office gossip — *harmless to send, unsafe to rely on* |

Two independent axes ⇒ two labels are required. CI-Work has only the vertical one.

## The claim, stated so it can fail

| Metric | Undefended (their Table 2) | Their best prompt defense | What we must show |
|---|---|---|---|
| Violation (VR) ↓ | 27.8% | 21.3% | **clearly below 21%** |
| Conveyance (CR) ↑ | 93.0% | 81.0% | **stays near 93%, not ~81%** |
| Integrity-Violation (IVR) ↓ | *unmeasured* | *unmeasured* | **large drop from our own measured baseline** |

**What would falsify the thesis:** we cut VR but CR lands in the low 80s. That would mean we merely rebuilt their prompt defense with extra machinery, and the paper has no result. This is the honest risk and we should say so out loud.

## Paper skeleton that follows

1. **Intro** — their "context-centric architectures" call; integrity is the missing axis.
2. **Background** — Contextual Integrity; Bell–LaPadula; Biba; NIST zero trust; Tian–Song.
3. **Threat model** — extend CI-Work's formal model with integrity contamination.
4. **Method** — the two labels, the provenance rubric, PIP/PDP/PEP at the write boundary.
5. **Experiments** — CI-Work's 3 metrics + our 2, against undefended / Prompt Defense / CI-CoT.
6. **Discussion** — why this is zero trust; limits (label error); ethics (their synthetic-data disclaimer).

**Figure 1** — one CI-Work transcript, dual-labeled, showing a Bell–LaPadula leak *and* a Biba contamination side by side. (Already drafted from their published examples.)
**Table 1** — the 5-metric comparison above.
**Ablations** — enforcement mode (redact vs quarantine vs deny) and label source (ground-truth vs inferred).

## The one experiment that decides the paper

Run the same CI-Work cases four ways — undefended, Prompt Defense, CI-CoT, ours — and report all five metrics. Everything else is supporting material.

Scope it to one or two flow directions first: **External** (where integrity matters most) and **Upward** (where they measured the worst leakage).
