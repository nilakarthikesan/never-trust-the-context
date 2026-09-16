# One-Page Thesis Note — for Professor Vijay Madisetti

> Ready to send (email/Slack/PDF). This is the "go / adjust" check-in the plan calls for before we write any code beyond the prototype. Action to complete this to-do: **send this note and get a thumbs-up on thesis + venue.**

---

**To:** Prof. Madisetti
**From:** [Nila], [teammate]
**Re:** Meshing Biba + zero trust into CI-Work — proposed thesis and 6–8 week plan

## The idea in one paragraph

CI-Work (Fu et al., ACL 2026 Industry, Microsoft) shows frontier LLM agents fail enterprise privacy badly — **violation rates 15.8–50.9%, leakage up to 26.7%** — and, crucially, that **scaling and prompt defenses do not fix it**; the authors explicitly call for **"context-centric architectures."** We answer that call by treating the enterprise agent as a **zero-trust system** and putting a **Biba + Bell–LaPadula policy layer at the agent's write boundary** (the moment it sends the email/Slack/post). This directly operationalizes Tian & Song's BLP+Biba zero-trust method (ISCID 2021) — the second paper you gave us — inside a real benchmark, which their paper never had.

## The one new insight

CI-Work's "sensitive vs essential" split is a **confidentiality** axis only. It never asks the **integrity** question Biba was built for: *may low-trust retrieved content (Slack gossip, a chat proposing to fabricate a competitor price, content injected by user pressure) contaminate a high-integrity outbound artifact?* We add a second, independent label **I(e)** (provenance trust) alongside CI-Work's confidentiality label **C(e)**. In CI-Work's *own* two published examples, each agent transcript contains **one BLP leak AND one Biba contamination** — proof the axes are distinct and both live in the data.

## What we build (not a fine-tune)

A per-request zero-trust PEP: label every retrieved entry with `C` and `I`; enforce **no-write-down** (BLP → CI-Work Leakage/Violation) and **no-write-up** (Biba → a NEW contamination metric) at the final tool call; allow / redact / quarantine. No model retraining — CI-Work already proved scaling is the wrong lever.

## How we prove it

Reuse CI-Work's exact harness (repo cloned) and its three metrics (LR/VR/CR), and add **Integrity-Violation** and **Integrity-Leakage**. Baselines to beat: CI-Work's undefended agent, their Prompt Defense, and CI-CoT (their Table 2 leaves VR > 20% and cuts conveyance ~9–12 pts). Win condition: **cut violation AND contamination while keeping conveyance close to undefended** — i.e., beat the privacy–utility trade-off they report.

## We fix Tian–Song's known weakness

Surveys (He 2022; PMC 2024) criticize Tian–Song for **ad-hoc weights and no initial-trust rule**. We specify an explicit, reproducible initial-trust/label function (provenance-based), which becomes a contribution rather than a reviewer target.

## Two questions for you

1. **Thesis check:** are you happy with "ZT write-boundary PEP, dual C/I labels, evaluate on CI-Work" as the contribution — or do you want us to also extend the *benchmark* with integrity cases (a second possible paper)?
2. **Venue target:** IEEE Access / ACSAC / an NDSS or ACL workshop / ACL Findings? This shapes how heavy the eval must be (subset vs full 125-seed sweep).

## Timeline (from the plan)

Wk0 reading + repo (done) → Wk1 formal mapping + Fig 1 (done in draft) → Wk2–3 PEP prototype → Wk3–5 eval on a CI-Work subset (Upward + External first) → Wk5–6 write.

Attached/available: two 1-page reading notes, the CI×BLP×Biba×ZT mapping table, and both CI-Work examples fully dual-labeled.
