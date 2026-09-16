# The Mesh: CI × BLP × Biba × Zero Trust

This is the intellectual core of the paper (plan §"The mesh"). It formalizes how CI-Work's information-flow model maps onto Tian–Song's dual-label zero-trust control, and defines the two independent labels that make the integrity axis new.

## 0. Notation

For any retrieved context entry `e`, and a request `(sender u, agent A, tool/channel k, recipient r, task I)`:

- **`C(e)` — confidentiality / CI-appropriateness label.** "How restricted is disclosure of `e` to `r` in this context?" High-C = disclosing to `r` breaks a privacy norm. This is exactly CI-Work's Essential/Sensitive axis, made continuous.
- **`I(e)` — integrity / provenance-trust label.** "How trustworthy is the *origin* of `e` as a basis for a high-stakes outbound artifact?" High-I = authoritative, verified (signed contract, board minute). Low-I = unverified, informal, or manipulable (Slack gossip, a chat message proposing to fabricate a number, content injected via user pressure).

Key claim: **C and I are independent axes.** A walk-away price is high-C (do not leak) *and* high-I (it is a real, authoritative number). A fabricated "claim competitor quotes are $90" chat is low-I; its sensitivity is almost incidental. `E_sens ≠ low-I`.

```
        high C (secret)
             │
  board memo │ board memo
  (H-C,H-I)  │  ── keep secret, safe to rely on
─────────────┼───────────────  high I (trusted)
  gossip     │  signed lease abstract
  (L-C,L-I)  │  (L-C, H-I) public-ish + authoritative
             │
        low C (shareable)
```

## 1. Entity mapping (CI-Work ⟷ Tian–Song ⟷ NIST ZT)

| CI-Work entity | CI parameter | Tian–Song component | NIST ZT role | Trust-score inputs |
|---|---|---|---|---|
| User `u` (data sender) | Sender | user (subject) | subject/requester | role in org lattice, seniority, authN strength |
| LLM agent `A` | (the actor) | application (subject) | subject (software agent) | never implicitly trusted; agent identity, session risk |
| Tool (Gmail/Slack/Notion) | (transmission channel) | terminal / channel | resource/PEP location | channel egress class (internal vs external) |
| Retrieved entry `e` | Data type + Data subject | file (object) | resource/object | dual labels `C(e)`, `I(e)`, provenance (source tool, author seniority, artifact type) |
| Recipient `r` | Recipient | user (subject) | subject (target) | clearance (max C it may receive), integrity need |
| Outbound message | Transmission principle | write to new object on channel | access request (write) | direction (Up/Down/Lateral/Diagonal/External) |

## 2. Rule mapping (this is the enforcement core)

Enforced at the **final write action** `a_fin` (and optionally at retrieve). Let `clr_C(r)` be the recipient's confidentiality clearance and `lvl_I(a_fin)` be the required integrity level of the outbound artifact.

| Classical rule | Direction | In our system | Maps to CI-Work metric |
|---|---|---|---|
| **BLP ⋆-property: no write down** | confidentiality | Do not place `e` with `C(e) > clr_C(r)` into a message to `r`. | **Leakage / Violation** (this is what CI-Work already scores) |
| **BLP simple: no read up** | confidentiality | Agent acting for `u` should not *retrieve* `e` with `C(e)` above `u`'s clearance. | (retrieval-time guard; not in CI-Work metrics) |
| **Biba ⋆-axiom: no write up** | **integrity** | Do not inject `e` with `I(e) < lvl_I(a_fin)` into a high-integrity artifact (board email, external negotiation, HR record). | **NEW: Integrity-Violation / Contamination** |
| **Biba simple: no read down** | **integrity** | A high-integrity task should not *consume* low-`I` sources unless they are sandboxed / quarantined / excluded from the write. | **NEW: Integrity-Leakage** |

Mnemonic kept from Tian–Song: *BLP keeps secrets from leaking down; Biba keeps garbage from flowing up.* CI-Work only measured the first half.

## 3. Zero-trust decision (Tian–Song, made explicit)

For each candidate entry `e` being considered for inclusion in `a_fin`, compute a per-request decision from a **weighted confidentiality/integrity score** — Tian–Song's idea, but with the initial-trust rule they omitted (their published weakness; see `notes/tian-song-reading-note.md` §4):

```
allow_confidentiality(e, r) := C(e) ≤ clr_C(r)          # BLP no-write-down
allow_integrity(e, a_fin)   := I(e) ≥ lvl_I(a_fin)       # Biba no-write-up

decision(e) =
    ALLOW   if allow_confidentiality ∧ allow_integrity
    DENY    if ¬allow_confidentiality           # would leak: drop the span
    QUARANTINE if allow_confidentiality ∧ ¬allow_integrity   # may include only if attributed / not asserted as fact
```

- **Never trust the context**: labels are recomputed per request, not cached because "the data is internal" or "already in the window."
- **Weighting** `w_C, w_I` lets a deployment tune strictness by direction (e.g., External raises `w_C`; board/exec artifacts raise `w_I`). Defaults and the initial-trust rule are specified in `design/pep-design.md`.

## 4. Label sources (how we assign C and I without hand-waving)

To avoid Tian–Song's "ad hoc weights" critique, every label has a stated, reproducible source:

- **`C(e)`**: (a) ground truth in CI-Work for evaluation (`sensitive`→high-C, `essential`→low-C); (b) at inference, a role-lattice + CI-judge (reuse CI-Work's `tag_context.j2` 9-category scheme) mapped to a C level. Recipient clearance `clr_C(r)` from the org lattice by direction (External < Diagonal < Lateral < Downward-from-exec, etc.).
- **`I(e)`**: a **provenance function** over observable signals, not vibes:
  - source tool/channel (signed doc store > official email > Slack DM > casual chat)
  - artifact type (contract/board minute/ledger = high-I; "draft", "speculation", "let's claim…", "gossip", "rumor" = low-I)
  - author authority (exec/legal/finance-of-record > peer > anonymous)
  - manipulation markers (content proposing deception, or content introduced only under user pressure)
  - optional LLM integrity-judge with a human spot-check protocol copied from CI-Work Appendix C.
- **`lvl_I(a_fin)`**: required integrity of the outbound artifact, from direction + recipient (External negotiation, board report, HR action = high; internal FYI = medium).

## 5. Worked cross-walk on CI-Work's own examples

See `design/dual-labeled-examples.md` for the two published qualitative cases (Fig 20 software renewal, Fig 21 lease negotiation) fully dual-labeled, each showing one BLP violation and one Biba violation in the *same* transcript. That file is the source for the paper's Figure 1.
