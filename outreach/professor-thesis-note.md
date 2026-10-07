# Project Review Note

## Proposed contribution

Investigate a write-boundary policy layer for language model agents using confidentiality and integrity labels. The prototype implements per-request policy decisions, post-hoc redaction, and inline context admission. The design draws on CI-Work, Bell–LaPadula, Biba, and zero-trust access control.

## Evidence available

Rule tests and deterministic offline fixtures exercise policy behavior. The current PR-review suite contains three cases, including an over-blocking control. Inline template output measures the policy's permitted context rather than a live model's achieved performance. The broader privacy/utility and integrity claims remain open.

## Review questions

1. Is the confidentiality/integrity mapping appropriate for the stated threat model?
2. Which live-model experiment and matched baselines would provide the strongest test of the proposed policy?
3. Which label assumptions need an agreement study or mechanical validation?
4. What minimum evidence is needed before targeting a research venue?

Supporting material: [reading notes](../notes/), [policy design](../design/pep-design.md), [benchmark construction](../design/pr-review-benchmark.md), and [executable walkthrough](../design/pr-review-walkthrough.md).
