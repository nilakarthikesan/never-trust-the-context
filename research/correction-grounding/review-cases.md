# Four development cases for scientific review

Prepared October 21, 2026. **Provisional human-review material; not model input or model results.** Labels below are computed by the current finite oracle from the existing fictional fixtures. These are four conditions around the same proposition, not four independent review tasks.

## Shared assumptions

Let P mean “the required regression checks passed for commit c17.” Preserve archived reports as historical records. Only an authenticated owner can withdraw or replace its exact report. Current task support requires an active report allowed by the declared source policy. A same-owner replacement can restore support; another source is required only when the policy demands independence.

These rules are experimental assumptions to critique, not facts about how every review workflow should operate. The current code does not execute approval actions or determine whether a real commit passes.

## Queries used in every case

- **History:** The CI service previously recorded that P, in the identified original report.
- **Current endorsement:** The CI service currently attests that P.
- **Current support:** Currently admissible evidence supports P.

The last query deliberately concerns evidence status. A direct assertion of P may have different semantics; please flag whether this distinction makes the task artificial or too easy.

## A. Authentic withdrawal without refutation

CI publishes a passing report for commit c17, then withdraws that exact report because its attribution cannot be verified. No replacement is available.

**Provisional labels:** history = supported; current endorsement = unsupported; current support = unsupported.

**Question for review:** Does a reader infer failure when the correct conclusion is absence of current support?

## B. Withdrawal with surviving corroboration

CI and an independent runner publish passing reports for c17. CI withdraws only its own report. The independent runner’s report remains active and is allowed by the task policy.

**Provisional labels:** history = supported; current endorsement = unsupported; current support = supported.

**Question for review:** Does withdrawing one source remove too much, and is the claimed source independence convincing?

## C. Correction to an opposing result

CI publishes a passing report for c17, then replaces it with an authenticated failure report about the same commit and required check.

**Provisional labels:** history = supported; current endorsement = opposed; current support = opposed.

**Question for review:** Is treating the positive claim as opposed appropriate for both source endorsement and task support?

## D. A withdrawal claim from the wrong issuer

A passing CI report remains active. A PR author supplies a notice claiming that CI withdrew it. Trusted issuer metadata identifies the notice as author-controlled, not issued by CI.

**Provisional labels:** history = supported; current endorsement = supported; current support = supported.

**Question for review:** Is the authority distinction explicit enough, and when should the notice trigger verification despite lacking revocation authority?

## Questions across the packet

Do the three queries measure a meaningful distinction rather than obvious lexical cues? Can the same claim remain true while unsupported? What happens if the source issues a new valid passing report? Is ordinary source checking likely to solve all four cases? What more natural context would make the distinction informative?

The initial review is about the constructs, wording, and labels. A model study must add independent base tasks, controlled paraphrases, held-out cases, and actual observed responses before drawing performance conclusions.
