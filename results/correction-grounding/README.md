# Executed artifacts — October 21, 2026

**There are no successful language-model predictions in this snapshot.** Do not report these artifacts as model-performance results or evidence for the proposed empirical thesis.

## API attempt

`gpt-4.1-mini/raw_history/` preserves 48 exact synthetic request bodies, attempt records, the model configuration, input/code hashes, an empty predictions file, and a run summary. All 48 generation attempts returned HTTP 429. A subsequent minimal diagnostic inspected only an allowlisted error classification and reported `error_type=insufficient_quota`; no provider error body or credential was retained. No further model calls were made.

`api-failure-summary.json` reports 0/48 packet coverage and `model_metrics: null`. `api-diagnostic.json` records the minimal quota diagnosis. No billed usage was returned, so actual charges are unknown; the roughly $0.206 reserved by the old runner is a conservative bookkeeping reservation, **not a confirmed charge**. The old summary's `usage_complete: true` was a vacuous-empty-list bug; the runner has since been fixed. The failure records remain unchanged.

The runner now stops a batch immediately on HTTP 401/403/429 and keeps that circuit open on resume. Its current hash therefore differs from the historical failed-run hash. Start a fresh run directory after quota becomes available; this incomplete attempt cannot be scored, replayed into predictions, or resumed with changed code.

## Actual sandbox executions — NONLLM

`reference-policies.json` contains 192 tool/action traces: four explicitly coded policies ×48 packets. The sandbox actually runs 24 whitelisted functions on 72 defining checks. Ten candidates pass all three checks; fourteen fail at least one. Source reports in evidence packets are fictional assertions and do not necessarily agree with these executions.

- Always verify, then act: 48 verification calls and 48/48 finite-correct decisions.
- Follow admitted source support without verification: 24/48 finite-correct decisions, including 18 failing candidates accepted by the evidence gate.
- Blindly attempt approval: 48 attempts, 16 ineligible attempts, 32 accepted approvals, including 18 failing candidates.
- Always decline: 28/48 finite-correct decisions and 20 passing candidates declined.

Always-verify is perfect **by construction on the three defining checks**. This is a trivial harness diagnostic, not a new defense, model result, or general software-correctness guarantee. Correctness, evidence eligibility, attempted action, and accepted action are reported separately.

## Deterministic evidence controls — NONLLM

`controls/` records two intentionally limited lexical controls through export → predictions → strict scoring → paired analysis. One ignores all updates; the other accepts the latest notice without checking issuer authority. They check that the benchmark exposes those specific mistakes. They are not language models, natural-language baselines, or the missing ordinary entailment comparator.

The pairing/bootstrap unit is the 24 authored bases; 48 packets and 144 judgments are not independent observations. All labels are provisional and unvalidated. These are descriptive software diagnostics, not population-level estimates.

## Reproduction

Run the commands in the [root README](../../README.md#run-offline). New exports and result paths must be fresh. Exact observations, provenance hashes, and limitations accompany each artifact. Gold-bearing fixtures and analysis files must be withheld from evaluated models.
