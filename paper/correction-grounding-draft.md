# After Withdrawal: Distinguishing Reconstruction, Source Support, and Historical Attribution in Agent Review

**Working research draft — 21 October 2026. RESULTS PENDING.** This document describes an implemented diagnostic harness and a provisional evaluation plan. It does not establish a new correction method, a model failure rate, or a model improvement. The attempted model run produced zero valid predictions. Authorship, venue formatting, and the final empirical scope remain to be agreed.

## Abstract

When a source withdraws a report, several claims about that report can acquire different evidential standing. The report can remain evidence that a source previously asserted a proposition while ceasing to establish the source's current endorsement or the proposition's current admissible support. A model's ability to reconstruct the proposition is a further, distinct observation. We ask whether these distinctions expose a useful diagnostic failure in model-assisted review, beyond ordinary document-support checking and existing correction systems. We implement an openly authored pilot containing 24 bounded program-review situations, paired unchanged and updated evidence packets, three claim scopes, an independent finite-record oracle, a budgeted model runner, and a separate verification-and-approval sandbox. The materials and runner permit comparisons between raw history, source-filtered rereading, constrained proposition reconstruction, and a model-inferred support ledger. **Model results are pending:** 48 attempted raw-history requests returned provider errors and yielded no valid predictions. Deterministic sandbox reference policies verify that source-policy eligibility, acquired verification, and bounded program outcomes are separately observable; they are not evidence of language-model behavior. A plain grounding comparator, human validation, and actual model action traces are required before claiming an empirical contribution.

## 1. Research question and motivation

Consider a review service that reports that a candidate program passed its acceptance checks. The service subsequently withdraws that exact report because its run attribution cannot be established. Withdrawal establishes neither that the program fails nor that it passes. It also need not erase the historical event that the service reported a pass. A valid replacement from the same service can restore its current endorsement; another independently admissible report can preserve current support despite withdrawal of the first report.

This study separates three questions:

1. **Historical assertion:** did this source, in this identified historical record, report P?
2. **Current endorsement:** does this source currently attest P?
3. **Current support:** does the task's currently admissible evidence support P?

The program's actual acceptance-check outcome is a fourth quantity. A correct guess about that outcome does not create a missing attestation. Conversely, a procedurally admissible report can be mistaken about the program. We therefore score source-policy compliance and bounded factual outcomes separately.

The central research question is: **does observed reconstruction of a proposition diverge from its surviving source support, and does an explicit scope-and-support audit improve review decisions beyond fresh rereading and ordinary grounding checks?** This is a falsifiable empirical question. The distinctions themselves and the need to repair downstream actions are established in prior work.

The proposed study contains three separable hypotheses. H1 concerns reconstruction/support disagreement after valid withdrawal. H2 concerns scope-specific errors, including loss of valid historical attribution and confusion between a source's current endorsement and other surviving support. H3 concerns the effect of an audit intervention on actual decisions and verification use. The current implementation supports collecting audit observations for H1 and H2. A separate interactive action runner connects real model tool choices to the sandbox, but it has not produced model action observations. It currently compares raw history with filtered rereading, not randomized audit interventions; an experiment capable of testing H3 remains necessary. None of the three hypotheses is confirmed here.

## 2. Related work and contribution boundary

Truth-maintenance systems and database provenance already represent dependencies and alternative justifications. The reference chain in our ledger traces this background through Doyle's truth-maintenance work, de Kleer's assumption-based systems, and [Green, Karvounarakis, and Tannen's provenance semirings](https://www.cs.ucdavis.edu/~green/papers/pods07.pdf). Alternative supporting bundles and jointly necessary premises must not be conflated. Our initial pilot uses a much simpler finite record model; it does not introduce a new dependency calculus.

[Keep Your Receipts](https://arxiv.org/html/2610.17719v1) is the closest motivation for measuring reconstruction separately from support. Its constructor-relative re-derivation audit concerns artifact liveness after withdrawal. Its limitations explicitly distinguish this objective from groundedness in surviving sources. A claim being reproducible without an earlier source therefore does not violate that paper's stated contract. Our reconstruction probe is a constrained local adaptation, not an implementation-level reproduction of its method or its knowledge-graph setting.

[Stored Is Not Supported](https://arxiv.org/html/2609.02127v1) already distinguishes stored reports, assertion standing, endorsement authority, preserved history, alternative support, and revocation. Its structured conformance tests and proposed end-to-end evaluation directly constrain our framing. The potential remaining contribution is a measured language-model comparison, not invention of the typed semantics. [MemTX](https://arxiv.org/pdf/2607.23929) already evaluates transactional correction/revocation and downstream mock actions with models. [MemoRepair](https://arxiv.org/html/2605.07242v1) already validates regenerated successors against retained support and evaluates post-event stale use. Adding correction or an approval tool does not establish differentiation from either work.

[When Evidence Changes](https://arxiv.org/html/2610.03902v1) compares repair with rereading and includes revoked, retained, conflicting, and ambiguous support. It motivates a strong source-filtered rereading comparison. [MemCorrect's public specification](https://github.com/joshuaswarren/remnic/blob/main/docs/benchmarks/memcorrect.md) includes scoped correction, non-resurrection, collateral preservation, provenance, and false-correction cases. Our forged-notice family is consequently a control, not a novel benchmark concept. [StateAuditor](https://arxiv.org/html/2608.01619v1) further shows why chronology and provenance alone do not establish semantic supersession. [Belief-R](https://aclanthology.org/2024.emnlp-main.586/) motivates measuring appropriate preservation alongside appropriate updating.

Ordinary document grounding is an essential competitor. [MiniCheck](https://aclanthology.org/2024.emnlp-main.499/) supplies a relevant whole-sentence checking approach; its decomposition findings also caution against assuming that explicit claim decomposition is beneficial. A claim that our scope ledger helps requires comparison against a plain grounding or entailment checker with equivalent evidence and comparable inference budget. That comparator is not yet implemented in the current runner.

At the control boundary, [CaMeL](https://arxiv.org/html/2503.18813v2) already uses provenance-dependent integrity and confidentiality policies, and [APEX](https://arxiv.org/html/2610.06966v1) already connects authorization and endorsed evidence to actions and released outputs. We make no broad claim to originate provenance-aware action gating.

More recent direct overlaps further narrow the claim. [Revoked but Still Authoritative](https://arxiv.org/html/2609.08258v1) already connects revocation failures to unsafe downstream use. [Structure Before Intelligence](https://arxiv.org/html/2610.19507v1) supplies deterministic release/retraction control with an optional model proposer. [Invalidation Contracts](https://arxiv.org/html/2609.00243v1) distinguishes cached-evidence validity from planner compliance, while [GSAR](https://arxiv.org/html/2604.23366v1) connects typed grounding to recovery choices. Neither the presence of a withdrawal gate nor an action trace differentiates our study from this literature.

[Static Alignment Is Not Enough](https://doi.org/10.13140/RG.2.2.24957.93926) motivates time-indexed, revisable alignment claims over deployment and evaluation conditions. Our experiment holds the task policy fixed while changing the evidence admitted under it. This is narrower than revising stakeholder values, evaluation contracts, or permissible interventions. [TUNa](https://aclanthology.org/2025.acl-long.1013/) motivates careful interpretation of textual reliability, but narrative unreliability labels are not used as factuality, maliciousness, or authorization labels here.

The [25-entry reference ledger](../research/correction-grounding/references.json) records inspected versions, reading depth, artifact access, overlap, and verified affiliations. The review is targeted rather than systematic and does not certify novelty.

## 3. Task semantics

Each packet contains identified sources, proposition-linked records, update events, and natural-language query claims. Sources have a fixed, explicitly stated admission policy. Accepted updates target an exact active record and require the issuer to match its owner. A replacement must preserve the owner and proposition identity while supplying a new active record. A forged third-party notice can be inspected as data but cannot itself revoke another source's record.

Withdrawal archives the targeted record. Archival preserves evidence for an allowed historical-assertion query; it removes the record's force as a current attestation. Current endorsement is owner-level: a valid replacement from the same owner can supply it even though the original record remains archived. Current support can survive through another eligible record. Independence is an explicit fictional lineage assumption in these materials, not an inference from different service names.

For each scoped query, the oracle returns eligible supporting and opposing records. Its four evidence statuses are `supported` when support alone remains, `opposed` when only opposition remains, `conflicted` when both remain, and `unsupported` when neither remains. Bare withdrawal does not create opposing evidence. These statuses describe the authored source policy, not unrestricted world truth.

The model must infer a claim's scope from its text and return its evidence status and record references. Public prompts disclose the policy and scope definitions but withhold the query's gold scope, private claim representation, reference labels, and executable outcome. The oracle operates on authored structured representations; it does not independently establish unrestricted natural-language entailment.

## 4. Provisional materials

The implemented generator creates **24 distinct bounded program contracts**, each with three explicit acceptance cases and one whitelisted Python candidate function. Examples include a retry schedule, path containment, secret masking, leap-year checking, CSV escaping, version matching, and UTF-8 truncation. Some candidates meet their three checks and others deliberately fail one or more. Passing means passing exactly these checks, not general program correctness.

The six update families are genuine withdrawal, opposite-valued correction, same-valued replacement, independent surviving support, forged notice, and surviving conflict. Each family has four distinct base situations. Every base yields an unchanged and an update packet, and each packet asks the three scope questions. The resulting material has **48 packets and 144 claim opportunities**, clustered within 24 bases.

This is an openly authored diagnostic pilot, with coding-assistant assistance. It is not an established benchmark. The private manifest designates six development bases and 18 provisionally locked bases, but all were authored openly; the latter are not an independently held-out or preregistered test set. Human validation remains pending. The existing assignment also confounds update family with scenario identity, so family differences cannot be interpreted as isolated causal effects. More balanced, independently reviewed materials are required for a stronger study.

Source reports are fictional authored assertions, including their claimed execution lineage. They are not measurements produced by running the sandbox. Only an acquired `verify` tool result supplies actual local execution output. This distinction permits supported-but-mistaken source reports without presenting fabricated reports as genuine observations.

Before model evaluation, human reviewers should check proposition identity, temporal reference, attribution target, replacement validity, and independence assumptions. Richer negative queries, paraphrases, indirect attribution, and less explicit scope wording should be added only with independent label checks. Agreement with the initial templates alone would demonstrate constrained rule application, not general narrative understanding.

## 5. Implemented audit conditions and required controls

The runner currently implements four conditions using identical public base material:

1. **Raw history:** the model directly audits the packet containing its records and update events.
2. **Source-filtered rereading:** a deterministic preprocessor replays the visible owner/exact-target rules, changes record status, retains archives for historical queries, and provides the resulting packet. It supplies no gold claim scopes or support labels. This condition measures the benefit of reliable update replay as well as rereading.
3. **Constrained reconstruction audit:** an auxiliary model call emits a subset of exact bare-proposition candidates. The prompt permits the supplied material and the model's own knowledge. The final audit receives this observed emission as fallible auxiliary output.
4. **Source-support audit:** an auxiliary model call infers each claim's scope and eligible supporting/opposing record IDs. A final audit receives that inferred ledger as fallible auxiliary output.

Reconstruction candidates are bare propositions, separate from historical and endorsement queries. They are supplied verbatim, creating substantial anchoring and copying opportunities. The probe is neither free-form regeneration nor a source-withheld reconstruction: archived source text remains visible. Its output measures constrained candidate emission. It cannot by itself distinguish parametric memory, residual text, copying, or an interpretation of the reconstruction instruction. Claim-blind reconstruction, synthetic-name controls, and an authentic comparison implementation would be needed for stronger mechanism or reproduction claims.

The audit conditions each use two model calls, while raw history and filtered rereading use one. Report calls, prompt/completion tokens, latency, and cost; add a call-matched generic review control before attributing an effect specifically to scope reasoning. The next required comparator is plain whole-sentence support/entailment checking over the same admissible records. Gold scopes or links, if used, must be reported separately as an upper-bound diagnostic, never as model-inferred performance.

The runner saves public inputs, exact request/response traces, code and input hashes, explicit model configuration, request/cost limits, failures, and replay information. It validates output structure without repairing malformed predictions. Incomplete runs are not scored as if their successful subset covered the full suite. User-declared token prices support budget accounting; they are not a guarantee of provider billing.

## 6. Verification and decision extension

A separate bounded sandbox exposes `verify`, `approve`, and `decline`. Verification executes the three authored acceptance checks; the default budget allows one call. A passing acquired verification authorizes a mock approval and a failing result blocks it. Without verification, approval requires current admitted support and no admitted opposing record. Historical assertion alone is insufficient. This procedural contract is explicit; code inspection alone does not satisfy it. Decline is always permitted.

The gate records attempted approvals separately from accepted mock approvals. Private grading also records whether the candidate actually passes the bounded checks. A source-supported false report can therefore permit approval of a failing candidate; a gate checking procedural eligibility does not guarantee source correctness. An always-decline policy avoids bad approvals while losing valid opportunities, so preservation and utility must accompany violation counts.

The separate interactive action runner saves model tool requests, actual delivered outputs, attempted mock actions, and private grades. It permits raw history or source-filtered rereading, with a maximum of three provider attempts per packet. No successful model action run is available. Always verifying and then acting fits within two calls and is perfect by construction on the defining checks, so this is a narrow tool-choice workflow. To test audit-caused decision consequences, connect a randomized audit intervention to the same task rather than interpreting this basic tool loop as an intervention result. An association between audit error and action error would not establish that the audit caused the action. Audit accuracy alone is also insufficient to claim improved agent control.

## 7. Analysis plan

Report scope accuracy, evidence-status accuracy, their joint accuracy, exact supporting/opposing evidence-set agreement, and unknown citations. Exact evidence-set agreement is agreement with the finite authored oracle, not proof of model reliance. Report unsupported or opposed current claims marked supported, supported historical claims needlessly removed, and supported current claims needlessly removed. Separate reconstruction emission from the final audit's support judgment.

For each bare proposition, compare observed reconstruction emission with current-support status. Historical claims must not be scored as unsupported bare world propositions merely because their underlying report was withdrawn. Retain conflict as a separate status rather than merging it with absence of evidence. Inspect disagreement traces before interpreting a single aggregate measure.

Compare unchanged and updated observations within each base. The implemented analysis resamples whole bases with all their claims and variants together; its bootstrap intervals are descriptive intervals over this small authored collection, not population generalization or preregistered significance tests. Family-level summaries remain exploratory. For later model action traces, report verification calls, ineligible attempted approvals, accepted approvals of failing candidates, declined passing candidates, and cost separately.

## 8. Results status — RESULTS PENDING

**There are zero valid language-model predictions and no scientific coverage of the proposed model comparison.** The attempted raw-history run issued 48 requests and received HTTP 429 provider failures for all 48 packets. A diagnostic attributed the block to insufficient quota. These failures are execution metadata, not evidence that the model could or could not solve the task. No reconstruction/support disagreement rate, model accuracy, intervention effect, or model action result can be reported.

The [saved deterministic reference-policy artifact](../results/correction-grounding/reference-policies.json) contains executed **non-LLM harness checks**. Each policy encountered the same 48 packets, comprising 20 passing and 28 failing candidate instances:

- Always verify then act used 48 verification calls, approved the 20 passing instances, and declined the 28 failing instances. Perfect finite selection is expected because verification runs the exact checks defining the outcome.
- Never verify and follow the exact admissible-support rule made 32 eligible approvals, including 18 failing candidates, and declined six passing candidates. These are consequences of authored reports and policy, not model extraction errors.
- Blindly approve attempted 48 approvals; the gate rejected 16 ineligible attempts. Of 32 accepted approvals, 18 concerned failing candidates.
- Always decline made no approvals and declined all 20 passing instances.

The saved lexical NONLLM controls also complete the export, prediction, scoring, and paired-analysis workflow. The initial-records control gets 120/144 statuses correct (104/144 all fields); the latest-notice control gets 136/144 statuses and all fields correct. These are deliberately limited software rules, not LLM baselines or a substitute for plain entailment.

These controls demonstrate that the harness exposes verification use, attempted-policy violations, gate outcomes, and bounded program correctness as distinct quantities. Their rates are properties of this constructed suite. They establish neither realistic error prevalence nor an advantage for a proposed defense. **Replace this section only with trace-backed observations and preserve the distinction between deterministic controls and model results.**

## 9. Limitations and falsification criteria

The main empirical thesis is unconfirmed. The project should be narrowed to a replication or diagnostic tool if a prior artifact already measures the same reconstruction/support disagreement, scope distinctions, and consequences. A targeted primary-source review cannot establish a global absence of prior work.

The scope-aware intervention earns no distinct method claim if ordinary grounding or source-filtered rereading solves the materials at comparable cost. If benefit appears only with gold links, report an extraction bottleneck. If disagreement is rare, attributable entirely to candidate anchoring, or unrelated to decisions, reject the proposed main finding. If preserving history increases mistaken current endorsement, report the tradeoff rather than counting retention as unconditional success.

The oracle assumes trusted source identity, correct proposition linkage, and a fixed evidence policy. It does not solve authenticated identity, semantic source extraction, arbitrary dependency graphs, hidden instruction attacks, or real organizational authorization. The current templates reveal scope explicitly and use only positive acceptance propositions. The finite sandbox has no repository state, external side effects, concurrency, or unrestricted code execution. Its verification budget and procedural attestation requirement are authored choices whose sensitivity should be tested.

Historical retention is allowed by this task and must not be generalized to privacy erasure. Evidence-policy updates, stakeholder preference changes, and temporal alignment-contract revision are outside the fixed-policy experiment. Claims about malicious intent, narrator psychology, hidden model reasoning, or collaborators' personal incentives are not supported by these materials.

## 10. Reproducibility and next decision

The reviewable artifacts are the pilot generator and fixtures, private annotation manifest, public prompt export, strict offline scorer, trace-preserving runner, bounded sandbox, reference policies, and versioned literature ledger. Private gold must remain excluded from evaluated prompts even when distributed in the same repository. Human label validation, a plain grounding comparator, successful model audit observations, and successful interactive model action traces are the next requirements for a substantive empirical paper.

The immediate decision is whether the diagnostic produces a reproducible failure beyond simple grounding and rereading. A negative result would justify reporting a narrow replication or benchmark limitation. A positive result would warrant a larger balanced study with independently authored cases and carefully matched intervention budgets. Neither outcome is presently known.
