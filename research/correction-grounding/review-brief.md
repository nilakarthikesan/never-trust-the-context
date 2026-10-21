# Initial scientific review request

Prepared October 21, 2026. This is a proposed, bounded first review for a prospective collaborator. It does not assume a project commitment. The [four cases](review-cases.md) include provisional labels for critique and must not be used as model inputs.

## Question and comparison

After a source is withdrawn, does a model's ability to reproduce an earlier claim overstate its surviving evidential support? Does confusing historical attribution with current endorsement contribute to that mismatch, and does the chosen audit affect decisions?

For example, an authentic CI report says a commit passed. CI then withdraws that report. The earlier report remains a historical event; its content may lose current support. Withdrawal does not prove the commit failed. A valid replacement or other admissible report can restore support.

The planned comparison is regeneration-based auditing versus source-filtered rereading and ordinary support checking, followed by a mock review decision under explicit evidence prerequisites. A scope-aware variant must extract its own labels; gold labels are a diagnostic upper bound. Existing work already covers correction and provenance. A useful contribution requires a distinct empirical result, not merely a new set of labels.

## Nila's proposed responsibility

Nila will prepare the literature comparison, author the scenarios and provisional labels, implement the oracle and sandbox, connect model adapters, run and document baselines, maintain reproducible traces and cost records, perform the initial error analysis, and prepare the first manuscript draft. Initial task construction and software work can proceed before any collaborator commits.

## Requested first review

Please review this brief and the four examples for:

1. **Construct validity:** are historical reporting, current endorsement, and current support meaningfully distinct here? Do the wording changes accidentally change the proposition or task?
2. **Grading validity:** do the provisional labels follow from the available evidence and declared policy? Where are the rules too artificial or linguistically ambiguous?
3. **Scientific value:** what counterexample, simpler baseline, or prior result most seriously challenges the proposed claim?

Short comments or a brief discussion would be enough for this first pass. A later, optional checkpoint could examine a small number of actual pilot failures and revisit the question. Preferred involvement and any broader collaboration remain to be discussed.

## Current status and venue

The prototype now includes 24 bounded program contracts, 48 paired evidence packets, provisional labels, the evidence oracle, model adapters, strict scoring, executable verification/approval tools, deterministic controls, and a first methods/paper draft. The attempted model run produced zero predictions because generation quota was unavailable, so no empirical regeneration comparison or model action result is established. The [results record](../../results/correction-grounding/README.md) separates actual sandbox executions from missing model evidence. The four review examples expose assumptions; they are not four independently sampled benchmark tasks.

[ACL in January or LangCode in February](venues.md) are more realistic planning options than forcing an unfinished study into SAFE's November deadline. Publication scope and contribution expectations should follow the evidence and participants' interests.
