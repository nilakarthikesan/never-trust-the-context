# Evidence revision before action

Study package, October 21, 2026. **After a correction, what still counts as evidence?**

Read the [short review brief](review-brief.md) and [four examples](review-cases.md) first. Nila owns the implementation, case construction, experimental operations, initial analysis, and first draft. The first request to a scientific collaborator is focused review of the constructs, wording, and grading rules; participation and further responsibilities are unconfirmed.

CI can withdraw a report about build 41 because it actually tested build 40. Its historical report remains part of the record. Current endorsement and current admissible support require valid surviving evidence. A same-owner replacement may restore support. Withdrawal does not prove failure.

## Implemented artifacts

- [Finite evidence oracle](../../eval/correction_scope_demo.py), [annotation guide](annotation-guide.md), and five original development examples.
- [Pilot builder](../../eval/build_correction_pilot.py): 24 different bounded program contracts, 48 unchanged/update packets, 144 scope queries. Six families cover withdrawal, opposite correction, same-value replacement, independently asserted support, forged notice, and a surviving conflict. The public source reports are fictional assertions, not sandbox execution output.
- [Executable sandbox](../../src/zt_pep/correction_pilot.py): 24 whitelisted Python functions, 72 explicit checks, and `verify`, `approve`, and `decline` tools. No arbitrary code executes. Approval eligibility is graded separately from finite test correctness.
- [Model runner](../../eval/run_correction_models.py): raw history, deterministic source-filtered rereading, constrained candidate reconstruction followed by an audit, and a model-extracted support ledger followed by an audit. Gold scope and world labels are withheld.
- [Interactive action runner](../../eval/run_correction_actions.py): actual `verify`/`approve`/`decline` choices, delivered tool outputs, exact provider traces, and separate private grades. Raw-history and filtered-rereading conditions are implemented; no model action result is available.
- [Strict scorer](../../eval/run_correction_eval.py), [paired analysis](../../eval/analyze_correction_pilot.py), and [coverage/reconstruction analysis](../../eval/summarize_correction_models.py). Incomplete predictions are not assigned an accuracy score.
- [Literature review](literature.md), [reference ledger](references.json), [research map](research-map.md), and [first paper draft](../../paper/correction-grounding-draft.md).

**Observed model coverage is zero.** The attempted mini-model run returned 48 HTTP 429 failures; a minimal diagnostic reported `insufficient_quota`. See [saved results](../../results/correction-grounding/README.md). Deterministic control results are explicitly NONLLM and establish no model-behavior finding.

## Offline workflow

Python 3.9 or later. Run the commands in the [root README](../../README.md#run-offline). The [verification record](testing.md) distinguishes software checks, actual bounded executions, and unavailable model results.

The pilot's manifest contains authored gold, finite test cases, and pairing metadata. Only export files from `run_correction_eval.py export` are model inputs. The openly authored development/provisionally locked partitions have not been human-validated or preregistered; neither is a defensible held-out benchmark. All cases sharing a base count as correlated observations. Family and scenario identity are currently confounded.

## Model collection

Set `OPENAI_API_KEY` or `CORRECTION_API_KEY` in your environment. These commands target a specific snapshot; use a new directory for a new model/configuration/code version. Prices are caller-declared accounting rates, not a guaranteed bill. See [configurations and official rate sources](../../config/correction-study.json).

```sh
python3 eval/run_correction_eval.py export   --suite eval/fixtures/correction_pilot.json --output-dir /tmp/correction-model-public
python3 eval/run_correction_models.py plan   --prompts /tmp/correction-model-public/prompts.jsonl   --model gpt-4.1-mini-2025-04-14 --base-url https://api.openai.com/v1   --input-price-per-million 0.4 --output-price-per-million 1.6   --max-output-tokens 800 --max-retries 0
python3 eval/run_correction_models.py run   --prompts /tmp/correction-model-public/prompts.jsonl   --output-dir /tmp/correction-mini-raw --condition raw_history   --model gpt-4.1-mini-2025-04-14 --base-url https://api.openai.com/v1   --input-price-per-million 0.4 --output-price-per-million 1.6   --max-output-tokens 800 --max-retries 0   --max-requests 48 --max-cost-usd 0.25 --allow-network
```

Run each of the four conditions separately, recording failures and matching packet coverage. Raw/reread conditions use one call per packet; reconstruction/ledger conditions use two, so they do not isolate a benefit from additional computation. A matched-call control remains necessary. Provider failures are not repaired or silently removed. A complete run can use the standard scorer followed by paired analysis; the summary tool reports missing coverage without inventing accuracy:

```sh
python3 eval/summarize_correction_models.py   --run-dir /tmp/correction-mini-raw --output /tmp/correction-mini-summary.json
python3 eval/run_correction_models.py replay   --source-dir /tmp/correction-mini-raw --output-dir /tmp/correction-mini-replay
```

Replay requires successful saved provider bodies and exact request hashes. It cannot recreate this repository's quota-failed run. Resume requires unchanged inputs, code, configuration, and budgets. The historical failure record predates the new failure circuit and is retained unchanged; a future run needs a fresh directory.

## Interactive action collection

This separate workflow permits up to three provider attempts per packet and one acquired verification. It executes only the whitelisted local functions. A model must request an actual tool; predicted support labels are never converted into purported model actions. `approve` and `decline` end a session, and private outcome grades are never appended to model context. There is no action-session resume.

```sh
python3 eval/run_correction_actions.py plan   --prompts /tmp/correction-model-public/prompts.jsonl   --suite eval/fixtures/correction_pilot.json   --private-manifest eval/fixtures/correction_pilot_manifest.json   --condition raw_history --model gpt-4.1-mini-2025-04-14   --base-url https://api.openai.com/v1   --input-price-per-million 0.4 --output-price-per-million 1.6   --max-output-tokens 800 --max-retries 0
```

Use `run` with an explicit fresh `--output-dir`, `--max-requests`, `--max-cost-usd`, and `--allow-network` only after reviewing the plan. This has not been run against a live model. Always verifying then acting fits within the call limit and is perfect on the defining checks; the initial action workflow is a finite tool-choice diagnostic, not a test of a new defense. Audit-mediated action effects remain a future experiment.

## Scientific boundaries

The reconstruction probe emits selected **bare public propositions**. It is observed constrained candidate selection with the candidate anchored in the prompt. It is not free-form knowledge-graph reconstruction, source-withheld regeneration, or a reproduction of Keep Your Receipts. Historical attribution queries are scored separately and are never counted as unsupported bare-proposition emissions.

The finite evidence oracle is exact only for the declared symbolic records. Lexical cues make the current scope questions easy; a score here does not establish unrestricted narrative or entailment understanding. Ordinary grounding and sentence-level receipts/entailment remain required comparators. The [protocol](protocol.md) states the falsification gates and how the task differs from temporal alignment contracts.

Use the [roadmap](roadmap.md) for scientific review and the [venue options](venues.md) for timing. Later deadlines provide time for validated cases and a real model study.
