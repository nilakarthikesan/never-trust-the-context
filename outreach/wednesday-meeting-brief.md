# Wednesday Meeting Brief — Prof. Marisetti

Notes to speak from. Order: (1) what each paper says, (2) the gap, (3) our thesis, (4) how we test, (5) the artifact, (6) venues, (7) decisions we need from him.

---

## 1. The two papers in plain terms

### Paper 1 — CI-Work: it's a *test*, not a *fix*

Microsoft + Huazhong University, ACL 2026 Industry Track.

**The setting.** An enterprise AI assistant (think Microsoft Copilot) can read your company data — email, Slack, Notion, meeting transcripts — and then *act* for you: send an email, post a Slack message.

**The problem.** To do the job it searches your data, and the search comes back with a *mix*:
- things it **must** include to finish the task (they call this the **essential set**)
- things that are topically related but **must not** go to this particular recipient (the **sensitive set**)

Example from their paper: you ask it to email a vendor to negotiate a license renewal. The search also surfaces your internal budget ceiling and your walk-away price. Both are "about the renewal." Only one belongs in the email.

**The theory.** Helen Nissenbaum's *Contextual Integrity*: privacy isn't secrecy, it's **appropriateness**. The same fact can be fine to tell your manager and wrong to tell a vendor. So context — who is sending, who is receiving, what type of data, under what norm — decides whether a flow is a violation.

They test five directions of workplace communication: **Upward** (to your boss), **Downward** (to staff), **Lateral** (peers), **Diagonal** (cross-org), **External** (outsiders).

**Three metrics.**
| Metric | Plain meaning |
|---|---|
| **Leakage (LR)** | what fraction of the secrets got out |
| **Violation (VR)** | did *any* secret get out — yes/no per task |
| **Conveyance (CR)** | did it actually include the info needed to do the job (usefulness) |

**Headline results.** Violation **15.8%–50.9%** depending on the model; leakage up to **26.7%**. So somewhere between 1-in-6 and 1-in-2 tasks leak something they shouldn't.

**The four findings that matter for us:**
1. **Privacy–utility trade-off.** The more useful the agent is, the more it leaks (correlation r ≈ 0.40). You seem forced to choose.
2. **Inverse scaling.** *Bigger models leak more*, not less. They're better at finding buried details, and more eager to please the user ("sycophancy") than to respect an unstated social norm.
3. **Prompt defenses don't solve it.** Telling the model "don't share sensitive things," or making it reason about contextual integrity first (their CI-CoT), only gets violation down to ~21–22% — and costs 9–12 points of usefulness.
4. **User pressure makes it worse.** If the user says "be thorough" or lists the sources to check, violations nearly double *and* usefulness drops. A lose–lose.

### ⭐ The "ask" — this is the sentence that shaped our thesis

Their own conclusion:

> "safeguarding enterprise workflows requires a paradigm shift, moving beyond **model-centric scaling** toward **context-centric architectures**."

Read that as an admission and an invitation: *you cannot fix this by making the model bigger or by writing a better prompt — someone needs to build an architecture around the context.* They diagnosed the disease and explicitly said the cure is architectural, then didn't build it. **That unbuilt cure is our paper.** They even released the benchmark and code, so the yardstick already exists.

### Paper 2 — Tian & Song: the control model we borrow

5-page paper, ISCID 2021, Ministry of Public Security research institute (China).

Two classic 1970s security models:

| Model | Protects | Rules | One-liner |
|---|---|---|---|
| **Bell–LaPadula (BLP)** | confidentiality | no read up, **no write down** | keeps secrets from leaking **down** |
| **Biba** | integrity | no read down, **no write up** | keeps garbage from flowing **up** |

They're mirror images. BLP stops a cleared person copying secrets into a place uncleared people can read. Biba stops untrusted junk being written into a trusted place.

**Their contribution.** Classic versions use rigid labels (Confidential / Secret / Top Secret). They make it **dynamic and zero-trust**: give every component — users, terminals, channels, files, applications — a continuous **trust score**, weight confidentiality against integrity, and re-decide on **every single request** ("never trust, always verify").

**Its documented weaknesses** (from later surveys — He 2022, and a 2024 review): no principled way to set the **initial** trust values, the weights are **ad hoc**, and it was never evaluated on a real system. Those three gaps are conveniently our contributions.

---

## 2. The gap we're filling (the heart of the pitch)

CI-Work's essential-vs-sensitive split answers exactly one question:

> **"Should this be disclosed to this person?"** — that's **confidentiality**.

It never asks the second question:

> **"Is this retrieved item trustworthy enough to base an outbound message on?"** — that's **integrity**. That's Biba. **CI-Work has no metric for it.**

**Concrete example (from their own paper).** An agent drafting an external negotiation email retrieves a Slack message where the procurement team says *"let's tell the vendor competitors quoted $90 — actually we got $95 — to pressure them."* If the agent repeats the $90 to the vendor, that isn't really a "leak." It's the agent **laundering an unverified, fabricated internal suggestion into an authoritative external commitment.** Biba's *no-write-up* is precisely the rule that forbids this. CI-Work would not score it at all.

### The subtlety that makes this a real contribution (and pre-empts the obvious objection)

**Sensitive ≠ untrustworthy. They are independent axes.**

|  | **Trustworthy (high integrity)** | **Untrustworthy (low integrity)** |
|---|---|---|
| **Secret (high confidentiality)** | walk-away price, board memo — *don't send, but it's real* | fabricated negotiation tactic — *don't send AND don't rely on* |
| **Shareable (low confidentiality)** | signed lease abstract — *safe to send and rely on* | office gossip, unconfirmed Slack — *harmless to send, unsafe to rely on* |

Because they're independent, you need **two labels**, not one relabeling of theirs. That's why this is an addition rather than a rename.

### Proof it's already in their data

In **both** of CI-Work's published example transcripts, the agent commits **one of each** failure. In the lease-negotiation case the sent email:
- reveals the **walk-away threshold ($54/sqft)** to the landlord → a **BLP / confidentiality** failure (CI-Work scores this)
- asserts a **13,000–15,000 sqft** space requirement whose *only* source is an **unconfirmed HR Slack message** → a **Biba / integrity** failure (CI-Work does **not** score this)

Show him this. It's their own figure, so it isn't cherry-picked.

---

## 3. Our thesis (one sentence)

> Enterprise LLM agents fail because they treat any retrieved context as **trusted the moment it lands in the context window**. We insert a **zero-trust policy layer at the agent's write boundary** that labels every retrieved item on two axes — confidentiality and integrity — and enforces **Bell–LaPadula (no-write-down) plus Biba (no-write-up)** before the message is sent.

Why the write boundary? Because that's the only place where sender, recipient, channel, and the full set of retrieved content are all known at once. It's the choke point.

Working title: **"Never Trust the Context: A Biba-Grounded Zero-Trust Layer for Enterprise LLM Agents."**

Why the ordering he suggested (Biba → CI-Work → zero trust) is right:
1. **CI-Work** gives us the problem *and* the measuring stick.
2. **Biba** supplies the missing integrity rule.
3. **Zero trust** is the architecture that applies both checks per request instead of hoping a prompt holds.

---

## 4. How we test it

Reuse CI-Work's harness and its three metrics; add two new ones:

| New metric | What it measures |
|---|---|
| **Integrity-Violation (IVR)** | did *any* low-trust content get written into a high-integrity outbound artifact |
| **Integrity-Leakage (IL)** | what fraction of low-trust items got written up |

**Baselines we must beat** (their Table 2): undefended agent (VR 27.8%, CR 93.0%), Prompt Defense (VR 21.3%, CR 81.0%), CI-CoT (VR 22.1%, CR 84.9%).

**Win condition — state this explicitly to him:** cut violation *and* the new contamination metric **while keeping conveyance near the undefended 93%**. If we merely trade usefulness for privacy, we've reinvented their prompt defense and the paper has no result.

**Scope control.** Start with a subset — one or two directions (External and Upward are the most interesting: External is where integrity matters most, Upward is where they saw the worst leakage) or their 25 human-curated seeds. Their full 125-seed × 9-model sweep used GPT-5.2 as the judge and is expensive; we do not need it for a first paper.

---

## 5. The artifact (already prototyped — repo is live)

**Repo:** https://github.com/nilakarthikesan/never-trust-the-context (public)

It's deliberately a **hybrid / neuro-symbolic** system: **deterministic access-control rules wrapped around a neural agent.** No fine-tuning — CI-Work already proved scaling and more reasoning don't fix this, so the contribution has to be the layer, not the model.

Three parts, standard zero-trust vocabulary (NIST SP 800-207), which he'll recognize:

| Component | Job |
|---|---|
| **PIP** (Policy Information Point) | assign the two labels: `C(e)` confidentiality, `I(e)` integrity. `I` comes from a transparent **provenance rubric** — source channel (signed doc > email > Notion > Slack DM > casual chat), artifact type, author authority, and markers of fabrication |
| **PDP** (Policy Decision Point) | run the two checks — BLP `C(e) ≤ recipient clearance`, Biba `I(e) ≥ required integrity of the artifact` — plus Tian–Song's weighted risk score |
| **PEP** (Policy Enforcement Point) | act at the final tool call (`GmailSendEmail`, `SlackSendMessage`, …): **allow / redact / quarantine / deny** |

**"Quarantine" is our nice third option** that neither leak/no-leak framing nor a prompt can express: content that's fine to mention but not authoritative gets **attributed and hedged** ("per an unverified internal note…") instead of asserted as fact.

**It plugs into CI-Work cheaply.** Their pipeline dumps a `formatted_trajectory.json` containing the retrieved items and the agent's final action. Our layer runs **post-hoc** on that file — relabel, re-decide, sanitize, re-judge — so we don't pay to regenerate trajectories. An inline variant wraps the tool call directly.

**Current offline demo** (2 dual-labeled cases, deterministic stand-in judge):

```
                LR     VR     CR     IL    IVR
undefended      50.0  100.0  100.0  25.0   50.0
ours (redact)    0.0    0.0  100.0   0.0    0.0   <- privacy AND integrity fixed, usefulness kept
naive refuse     0.0    0.0    0.0   0.0    0.0   <- the trap: safe but useless
```

**Be upfront with him:** those are on a 2-case fixture with a keyword-matching stand-in for the LLM judge — they prove the plumbing works and the metrics move the right way, **not** a publishable result. Real numbers need API access and their LLM judge.

**We also fix Tian–Song's published weakness.** Surveys criticize them for ad-hoc weights and no initial-trust rule. Every label in ours traces to a stated rubric with a documented default, and every number lives in one `policy.yaml`. That converts a reviewer attack into a contribution.

---

## 6. Venues to discuss (his call — it sets how heavy the eval must be)

| Tier | Venue | Why / trade-off |
|---|---|---|
| **Fast, likely** | **IEEE Access** | rolling submission, quick turnaround, he publishes here often; fits a systems + evaluation paper |
| **Direct reply** | **ACL / EMNLP Industry Track** | CI-Work itself is ACL Industry — publishing where the problem was posed is a strong narrative; needs ARR cycle timing |
| **Security-native** | **AISec @ CCS**, **SaTML**, **PETS** | exactly this topic (ML security/privacy); workshops are a realistic first target and fast feedback |
| **Applied security** | **ACSAC** | applied, systems-flavored, appreciates a deployable enforcement layer |
| **Stretch** | **USENIX Security / NDSS / IEEE S&P** | top-tier; would need the full sweep, an inline implementation, and probably a real-system case study |

Suggested framing for him: **target a security workshop or IEEE Access first for speed, with ACL Industry as the stretch narrative.** We should check this year's actual deadlines before committing — I haven't verified current dates.

---

## 7. Decisions we need from him on Wednesday

1. **Scope:** defense-only (build the layer, evaluate on CI-Work), or also extend the *benchmark* with integrity cases? The second is arguably a second paper.
2. **Venue**, since it determines whether a subset eval is enough or we need the full 125-seed × multi-model sweep.
3. **Compute / API access:** we need Azure or OpenAI credits to run their LLM judge (they used GPT-5.2). This is currently the hard blocker on real numbers.
4. **Labeling effort:** do we recruit human annotators to validate our integrity labels (mirroring their Appendix C protocol)? Reviewers will ask how we know an item is "low integrity."
5. Should we email the CI-Work authors? They released the code; a short note may get us their exact judge configuration.

---

## Anticipated questions and answers

**"Isn't integrity just sensitivity again?"** No — see the 2×2. A walk-away price is maximally secret *and* maximally reliable; gossip is barely secret *and* unreliable. Two independent axes.

**"Why not just fine-tune the model?"** CI-Work tested that direction: bigger models and more reasoning made leakage *worse* or barely better. And a policy layer is auditable and configurable per organization; a fine-tune is neither.

**"Why will your redaction not destroy usefulness like their prompt defense?"** Because we block at the level of *specific labeled items*, not by telling the whole model to be cautious. Blanket caution suppressed 9–12 points of useful content; targeted removal shouldn't. This is our main risk and our main claim — it's exactly what the experiment measures.

**"Where does the integrity label come from?"** A stated provenance rubric (source channel, artifact type, author authority, fabrication markers), with an LLM second-labeler and human spot-checks. Deliberately transparent so it's auditable.

**"Is 1970s MLS really applicable to LLMs?"** That's the interesting claim: the context window is a place where data of wildly different provenance gets mixed and then written out with uniform authority — which is precisely the condition Biba was invented for. Tian–Song already showed how to make the labels dynamic; we move the objects from files to retrieved context.
