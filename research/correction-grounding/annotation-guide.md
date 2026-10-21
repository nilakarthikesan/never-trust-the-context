# Claim scope and evidence annotation guide

Version 0.1, October 21, 2026. These are proposed annotation rules for human validation and future natural-language extraction. The current five-packet artifact uses hand-authored representations; it does not implement a parser.

## Unit of annotation

Annotate one proposition, its polarity, the attributed source if any, the relevant time, and whether the sentence concerns an earlier report, current endorsement, or current task support. Split compound sentences before assigning labels. Preserve negation and quotation scope; “A said not P” differs from “A did not say P.”

The finite development oracle represents only three selected claim kinds. Wording outside that representation should be marked for adjudication rather than forced into a convenient label.

## Three claim kinds

**Historical assertion:** “CI previously reported that commit c17 passed.” Evidence is the identified historical report, even if it has since been archived or superseded. This does not assert that the commit passed. Match the exact report and owner; an unrelated report cannot establish the historical event.

**Current source endorsement:** “CI currently attests that commit c17 passed.” Evidence is an active assertion from that owner about that proposition. A withdrawn original cannot supply it, but a valid replacement from the same owner can. This is owner-level current endorsement, not the active status of one particular historical record.

**Current admissible support:** “The currently admissible evidence supports that commit c17 passed.” Evidence is active support allowed by the task's source policy. An independent valid report can preserve support after another source withdraws. Independence is required only if the task policy demands it. Merely repeating another report does not create a new independent root.

A direct world assertion such as “commit c17 passed” requires an additional policy about when that assertion is warranted. Do not silently treat every world claim as an evidence-status sentence. The future parser and human adjudication must make this mapping explicit.

## Four finite evidence statuses

- **Supported:** matching admissible evidence exists and no admissible opposing evidence is present for the selected scope.
- **Opposed:** admissible evidence for the opposite proposition is present, with none for the queried proposition.
- **Conflicted:** admissible evidence exists on both sides.
- **Unsupported:** neither admissible support nor admissible opposition exists for the selected scope.

These are source-relative statuses. They do not determine world truth. Withdrawal alone gives no evidence for the opposite proposition; a corrective failure report may provide such evidence. A source can currently endorse an incorrect proposition.

## Update provenance

Use trusted issuer metadata, not a notice's claim about its own authority. In this finite policy a source can retract or replace its own exact record. A PR author's statement “CI withdrew its report” cannot itself mutate CI's canonical record. It may be a useful hint requiring verification in a future tool workflow.

## Human validation procedure

Have annotators first identify the proposition and scope without seeing model output. Then adjudicate supporting/opposing record IDs after replaying authorized updates. Keep ambiguities, disagreements, and revisions. Validate that paired rewrites preserve source, facts, temporal reference, and policy while varying only the intended interpretation.

For the model study, separate errors in language-to-scope extraction from errors resolving support after the scope is known. Keep private world labels and gold claim representations out of ordinary prompts. Agreement with gold record IDs is not a substitute for checking that the linked text supports the natural-language claim.
