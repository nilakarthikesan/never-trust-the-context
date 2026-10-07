# Research Hypothesis and Evaluation Plan

## Hypothesis

A policy layer at an LLM agent's outbound write boundary may reduce unauthorized disclosure and use of untrusted context while retaining useful task content. The prototype labels retrieved entries for confidentiality and integrity and applies Bell–LaPadula- and Biba-inspired rules per request.

Confidentiality and integrity are separate concerns: a reliable fact can be restricted, while a shareable statement can still be unreliable. The design treats these concerns independently rather than inferring one label from the other.

## Current evidence

The implementation has rule tests, two adapted CI-Work fixtures, and three PR-review fixtures. Offline results use deterministic keyword judging and template output. They establish behavior in those cases, rather than live-model effectiveness. [The walkthrough](../design/pr-review-walkthrough.md) separates policy-permitted output from model-achieved output.

## Experiments needed

Compare undefended, Prompt-Defense, CI-CoT, post-hoc policy, and inline policy modes on the same held-out cases with the same writer and judge. Report leakage, violation, conveyance, integrity-disclosure proxies, and paired verdict corruption where implemented.

Vary enforcement mode, label source, thresholds, and case structure. Include null cases to measure false suppression and adversarial reconstruction checks for abstracts. The hypothesis is weakened if confidentiality gains require a substantial conveyance loss, if integrity failures persist, or if label error eliminates the fixture-level benefit.

Published results from CI-Work are motivation, rather than a matched baseline for these fixtures. See [the benchmark plan](../design/pr-review-benchmark.md) and [paper/README.md](../paper/README.md) for the experiment backlog.
