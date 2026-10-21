# Pilot roadmap and focused review

Updated October 21, 2026. **Use a pilot-driven schedule rather than assume SAFE readiness by November 2.** The [venue options](venues.md) include ACL via ARR on January 4, 2027 and LangCode on February 5. These are alternatives to evaluate, not promised submissions.

## Nila's work begins now

Nila owns the literature comparison, scenario construction and provisional annotation, executable oracle, model adapters, sandbox tools, baseline implementation, experiment runs, reproducible logs and cost records, initial error analysis, and first manuscript draft. Initial work does not depend on a collaborator committing to the project.

The current package includes the finite support oracle, 24 bounded program contracts/48 paired packets, public export, strict scoring, budgeted model adapters, verification/approval tools, executed NONLLM controls, paired analysis, and a first draft. Generation quota blocked the real model pilot; it produced zero predictions. The [review brief](review-brief.md) and [four examples](review-cases.md) make the first scientific feedback request concrete. No successful model study is available.

## Initial request to Anneliese

Invite one first pass on the short brief and examples: whether the scope distinctions are meaningful, whether the wording/labels are defensible, and what alternative explanation or counterexample would most challenge the study. Short comments or a discussion are sufficient for this first checkpoint. Her preferred involvement remains open.

A second, optional checkpoint could inspect a few actual pilot failures and the supported claim. Do not assume that either review entails ongoing implementation, large-scale annotation, or a deadline commitment.

## Build sequence

**First: validate the question and materials.** Review the nearest released artifacts, refine the scope rules, and author independent base situations with unchanged/update pairs. Keep private base/family/split metadata outside exported prompts. The current four examples are variants around one proposition, not independent benchmark tasks.

**Then: run a diagnostic scope/support pilot.** Use the implemented adapter after model access is available, preserving exact requests/responses and settings. Add the ordinary-grounding and matched-call baselines before making a comparative claim. Validate labels independently. This stage tests scope and finite support judgments; it cannot by itself establish a regeneration or action failure.

**Next: test the central comparison and consequences.** Validate the constrained reconstruction diagnostic, add a faithful source-withheld/claim-blind comparison where feasible, and use the implemented fresh-rereading condition. Connect the sandbox tools to successful model runs under the explicit evidence prerequisites. Measure audit disagreement and decision effects separately. Retain cost and task-level uncertainty records.

**Finally: choose the paper claim and venue.** Continue only where the results survive simple baselines and semantic controls. Write the result the experiment supports, including a negative or replication finding if appropriate. Select January ACL or February LangCode according to scope, readiness, and collaborator interest; recheck current submission and concurrent-review rules.

The study's fixed assumptions, human-review ambiguities, and gold-versus-extracted representation gap must remain visible. Additional development examples or passing software checks do not establish model performance.
