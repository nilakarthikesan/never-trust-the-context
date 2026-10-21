# Never Trust the Context

**Current study: After a correction, what still counts as evidence?**

An agent should distinguish a source's historical report, its current endorsement, and the evidence currently admitted for a decision. Withdrawing a report preserves its history without establishing that the underlying claim is false. This repository implements a controlled diagnostic of those distinctions and a bounded code-review sandbox.

The empirical thesis is **unconfirmed**. The October 21, 2026 model run returned 48 HTTP 429 failures and **zero predictions**; a minimal diagnostic identified unavailable API quota. The saved deterministic results test the harness, not language-model performance. See the [results and failure record](results/correction-grounding/README.md).

## What is implemented

- **Cases and labels:** 24 different program contracts, each with unchanged/update evidence packets: 48 packets and 144 scope judgments across six update families. These are openly authored provisional cases, with no independent human validation or held-out claim.
- **Ground-truth separation:** a finite evidence oracle handles owner-scoped withdrawal/replacement and historical assertions. A separate sandbox actually executes 72 bounded acceptance checks. Source support is not a guarantee of program correctness.
- **Model collection:** four conditions, public-input exports, explicit model snapshots, exact request/response records, request/cost budgets, failure circuits, hash-checked resume, and offline replay. Constrained bare-proposition reconstruction is a local diagnostic, not a reproduction of a published graph-regeneration method.
- **Baselines and analysis:** two deliberately limited non-LLM evidence heuristics, four executable reference policies, strict scope/status/citation scoring, and paired analysis resampling whole base situations. Ordinary entailment and matched-call model comparators are still required.
- **Research material:** [25-reference primary-source ledger](research/correction-grounding/references.json), [literature review](research/correction-grounding/literature.md), [labs and researchers map](research/correction-grounding/research-map.md), and a [first paper draft](paper/correction-grounding-draft.md).

Start with the [research guide](research/correction-grounding/README.md), [review brief](research/correction-grounding/review-brief.md), and [four review examples](research/correction-grounding/review-cases.md). The [protocol](research/correction-grounding/protocol.md) states what would falsify or narrow the thesis.

## Run offline

Python 3.9 or later; the new correction workflow uses the standard library. The older policy walkthrough also needs PyYAML.

```sh
python3 -m pip install -e '.[test]'
python3 tests/test_pdp.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 eval/correction_scope_demo.py validate
python3 eval/build_correction_pilot.py validate
python3 eval/verify_walkthrough.py
```

Create fresh outputs; the export/scoring commands refuse to overwrite previous runs:

```sh
python3 eval/run_correction_eval.py export   --suite eval/fixtures/correction_pilot.json --output-dir /tmp/correction-public
python3 eval/run_correction_models.py heuristic   --prompts /tmp/correction-public/prompts.jsonl   --method initial_records_heuristic --output-dir /tmp/correction-control
python3 eval/run_correction_eval.py score   --suite eval/fixtures/correction_pilot.json --export-dir /tmp/correction-public   --predictions /tmp/correction-control/predictions.jsonl   --output-dir /tmp/correction-control-scored   --source-label deterministic_heuristic_NOT_LLM
python3 eval/analyze_correction_pilot.py   --metrics /tmp/correction-control-scored/metrics.json   --output /tmp/correction-control-paired.json
python3 eval/build_correction_pilot.py reference-policies   --output /tmp/correction-reference-policies.json
```

## Run a model

See the [model instructions](research/correction-grounding/README.md#model-collection) and [planned configurations](config/correction-study.json). Set your provider key in the environment; never put credentials in files or command arguments. Review a `plan` before an explicitly budgeted `run`. A key that lists models can still lack generation quota.

Only exported public packets go to evaluated models. Files named fixtures, manifests, scored results, and analyses contain private grading labels; “private” here means withheld from the evaluated model, not a restricted-access file.

## Research scope and collaboration

Nila owns implementation, case construction, experiment operations, initial analysis, and the first draft. An initial scientific review can be limited to the definitions and four cases: do historical attribution, present endorsement, and surviving support have clear, reproducible grading rules? Collaborator participation and scientific ownership remain to be agreed.

[Venue options](research/correction-grounding/venues.md) include SAFE at AAAI 2027 (November 2, 2026), ACL 2027 through ARR (January 4, 2027), and LangCode at NAACL (February 5, 2027). These are alternative routes; choose after pilot validation and check the venue's concurrent-submission rules.

## Earlier policy prototype

The existing BLP/Biba policy layer remains under [src/zt_pep](src/zt_pep), with its [design](design/pep-design.md), [worked example](design/pr-review-walkthrough.md), and [older IEEE manuscript](paper/main.tex). Its template-writer and keyword-judge scores are deterministic demonstrations, not measured LLM robustness. The walkthrough verifier now calls the production policy implementation, and the LLM redactor interface has an integration regression test. The older evaluation CLI's `--judge llm` changes the judge; it does not turn its template writer into a real model experiment.

```sh
python3 eval/run_eval.py --source fixture --judge keyword
```
