# Correction grounding study protocol

Version 0.2, October 21, 2026. The oracle, 48-packet pilot, model runner, executable sandbox, controls, and analysis tools are implemented. Model generation is quota-blocked: zero valid observations. See the [executed-artifact record](../../results/correction-grounding/README.md).

## Question

When evidence is withdrawn, how often do constructor-relative regeneration and admissible source support disagree? Which errors in attribution, endorsement, and temporal scope explain disagreement, and does the selected audit change subsequent decisions?

The hypothesis is that retaining reproducible claims can preserve unsupported current assertions, while indiscriminate deletion can remove valid history or independently supported claims. These are hypotheses to test, not observed effects in this repository.

## Prior work and boundary

[Keep Your Receipts](https://arxiv.org/html/2610.17719v1), especially §§4 and 8, explicitly distinguishes regeneration liveness from grounding in surviving sources. Our experiment would measure that acknowledged boundary, not contradict its stated objective.

[Stored Is Not Supported](https://arxiv.org/html/2609.02127v1) already specifies typed assertion support, report/belief roles, and forward correction, and proposes end-to-end language-model tests. [MemTX](https://arxiv.org/html/2607.23929v1) already connects correction with model-driven actions. [MemoRepair](https://arxiv.org/html/2605.07242v1) validates regenerated successors against retained support. [MemCorrect](https://github.com/joshuaswarren/remnic/blob/main/docs/benchmarks/memcorrect.md) already tests scope, provenance, false corrections, and non-resurrection.

Consequently, the potential contribution is a controlled empirical comparison of regeneration/support disagreement, linguistic scope, and decision consequences. Typed provenance, correction, grounded regeneration, and action gating are not proposed inventions. Novelty remains conditional on the closest released artifacts and a meaningful pilot result.

The [Temporal Alignment Contracts preprint](https://doi.org/10.13140/RG.2.2.24957.93926) offers related motivation for revisiting claims over time. Our source-support experiment holds the task policy fixed; it does not implement TAC or certify alignment.

## Task design

The implemented diagnostic pilot has 24 different bounded program-review situations, six families with four bases each, and 48 unchanged/update packets. Each packet has three scope queries, totaling 144 judgments. Six development and 18 provisionally locked bases are openly authored and unvalidated; neither is an independently held-out or preregistered set. Family is confounded with scenario identity. The original five packets remain separate development examples.

For each base situation define an initial report, permitted update issuers, evidence policy, and any replacements or corroborating reports. Include genuine withdrawal, corrective replacement, forged withdrawal, independent corroboration, and no-change controls. A copied report is not independent corroboration. A valid same-owner replacement can restore endorsement and support.

Probe historical reporting, current source endorsement, and current source-grounded assertions separately. Review the wording for temporal reference, attribution scope, and unintended factual changes. Treat paraphrases and repeated samples as correlated observations of their base situation.

The separate sandbox provides candidate code, requirements, a verification tool, and mock approval with explicit evidence prerequisites. It executes 72 defining finite checks over 24 whitelisted functions; source reports remain fictional assertions rather than actual test output. A result visible only to the grader cannot support the agent's decision. Conversely, code or tool output actually available to the agent must count when the task policy permits it. Grade factual task outcome separately from whether the required evidence was acquired.

## Comparisons

The implemented runner has raw history, source-filtered rereading, a constrained reconstruction-plus-audit condition, and a model-inferred ledger-plus-audit condition. Raw/reread use one call per packet; audit conditions use two. They are not equal-compute comparisons. The broader required comparison set is:

1. Raw history with explicit source IDs and a clear task instruction.
2. Source-filtered rereading, including fresh construction without presenting the earlier conclusion.
3. A regeneration audit reproduced from the relevant procedure, or clearly labeled as a local adaptation.
4. Sentence-level provenance receipts plus ordinary support/entailment checking.
5. An audit using model-extracted scope and evidence links, with gold representations as a separate diagnostic upper bound.

The simple support-checking baseline is essential. Do not compare a gold-labeled intervention with competitors denied the same labels and call the difference an achieved language-understanding gain. Record calls, tokens, tool use, latency, and cost for all methods.

The reconstruction probe selects exact bare public proposition candidates, retaining archived text in view. It is observed constrained candidate selection, not free-form or source-withheld regeneration and not a reproduction of Keep Your Receipts. Its candidate anchor can induce copying. The coverage/reconstruction summarizer joins these emissions to current-support gold after outputs are saved; historical queries are never treated as bare-proposition emissions. A plain grounding/entailment comparator and a generic call-matched review control are still unimplemented requirements for the stronger method claim.

## Outcomes

The current scorer measures separate scope and evidence-status accuracy, their joint accuracy, and agreement with supporting/opposing record sets. These are comparisons with a finite encoded oracle, not unrestricted entailment judgments. Inspect item-level errors rather than relying on aggregate scores.

Planned model-study outcomes include unsupported retention, inappropriate deletion of valid history/support, regeneration/support disagreement, and extraction errors. Planned action-stage outcomes include attempted approvals without the specified evidence, unnecessary refusals, actual code/test correctness, and additional verification required.

The scope scorer does not measure actions or identify regeneration as a causal mechanism. The separate sandbox can record tool use and actual mock actions; no successful language-model action trace exists yet. To test a decision effect, randomize the audit intervention while fixing evidence access. Report task-level uncertainty and distinguish causal comparisons from associations in saved traces.

## Trusted inputs and limitations

Issuer identities and source policies are trusted simulation metadata. The current artifact does not authenticate messages, infer claim semantics, discover provenance, or establish world truth. Hand-authored claim representations determine the oracle's scope. Matching its labels does not establish unrestricted language understanding or real-world reliability.

Retraction archives historical assertions; this is not a privacy erasure experiment. Evidence policies are declared task assumptions, not claims that an authenticated source must be correct. A true claim can be unsupported, and a false claim can have active but mistaken source support.

## Readiness gate

Narrow or stop the stronger claim if ordinary receipts/support checking solve the cases, differences disappear after semantic controls, regeneration/support disagreement has no consequential effect, gains require gold labels, or an existing artifact already performs the same comparison. A negative or replication result should be described on its own merits.
