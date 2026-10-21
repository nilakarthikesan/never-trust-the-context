# Never Trust the Context

A research prototype for controlling disclosure and use of untrusted context in language model agents. The policy layer labels retrieved entries for confidentiality and integrity, then checks them at an outbound write boundary.

The design draws on Bell–LaPadula, Biba, and zero-trust access control. [CI-Work](https://arxiv.org/abs/2604.21308) supplies the contextual-integrity evaluation setting; [Tian and Song](https://doi.org/10.1109/ISCID52796.2021.00031) supplies a related access-control model. Reading notes and design assumptions are recorded in [notes/](notes/) and [design/](design/).

## Current scope

The repository implements a policy information/decision/enforcement pipeline, post-hoc redaction, and inline context admission. It includes two adapted CI-Work fixtures and three PR-review fixtures, a deterministic keyword judge, a template writer, and regression tests.

The current offline results measure behavior on these small fixtures. They do not establish improved reliability for deployed LLM agents. Inline results from `TemplateWriter` describe the output permitted by the policy under fixed labels; they are not achieved scores from a live language model. Live writer and judge adapters are implemented, but broader evaluation remains open.

## Run the offline evaluation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 tests/test_pdp.py
python3 eval/run_eval.py --source fixture --judge keyword
python3 eval/verify_walkthrough.py
python3 eval/run_eval.py --source fixture \
  --path eval/fixtures/pr_review_cases.json \
  --policy config/policy.pr-review.yaml --per-case
```

The three PR-review fixtures document an aggregate conveyance score of 83.33% for post-hoc redaction and 91.67% for inline template output; the undefended fixture output is also 91.67%. Keyword-scored leakage and integrity-disclosure metrics are zero for both policy modes on these cases. [The walkthrough](design/pr-review-walkthrough.md) explains each decision and the limits of those measurements.

`LR`, `VR`, and `CR` measure leakage, violation, and conveyance. `IL` and `IVR` are integrity-disclosure proxies. They do not directly establish whether a model relied on a misleading entry when forming a verdict. `PC` measures conveyance through fixture-provided abstracts.

## Code and documentation

- [src/zt_pep/](src/zt_pep/): entry labels, policy decisions, redaction, inline admission, and metrics.
- [eval/](eval/): fixture runner, CI-Work adapter, and executable walkthrough checks.
- [config/](config/): example policy and PR-review policy.
- [tests/test_pdp.py](tests/test_pdp.py): rule tests, including provenance caps and regulated-content handling.
- [design/pep-design.md](design/pep-design.md): architecture and request flow.
- [design/enforcement-mechanics.md](design/enforcement-mechanics.md): proposed enforcement levels and action constraints.
- [design/weight-calibration.md](design/weight-calibration.md): parameter derivation and calibration assumptions.
- [paper/](paper/): manuscript source and experiment backlog.

The code caps integrity uplift from author-controlled content and prevents the soft threshold override from releasing regulated entries. These fixes have regression coverage in `tests/test_pdp.py`.

## Limitations and next experiments

The fixture suite is too small to estimate generalization or false-suppression rates. Keyword judges can miss paraphrases and confuse shared numeric tokens. Label quality and the confidentiality of abstracts are assumptions requiring validation.

The next experiments are live-model evaluation on CI-Work trajectories, matched Prompt-Defense and CI-CoT baselines, larger PR-review suites, paired verdict-corruption measurements, labeler agreement, and adversarial reconstruction tests on abstracts. Detailed proposals are in [design/pr-review-benchmark.md](design/pr-review-benchmark.md) and [paper/README.md](paper/README.md).

### October 2026 extension: measure the decision, not only disclosure

The [current literature map](notes/context-provenance-literature-2026-10-18.md) reviews CI-Work, CaMeL, ARGUS, PAA, AgentDyn and newer contextual-integrity benchmarks. It narrows the proposed contribution rather than claiming the first provenance-based defense. The [paired study protocol](design/paired-outcome-study.md) adds a concrete experiment around misleading instructions, mistaken/stale accounts, helpful hints and benign controls. [Collaboration scopes](design/collaboration-scopes.md) offers opt-in intellectual work packages without assigning authorship.

Ten authored synthetic pairs and an outcome scorer are now available. They measure clean/perturbed verdict accuracy, conditional correct-to-wrong transitions, annotated-support grounding, required-claim coverage and abstention. No live-model result is included, and the new pilot does not measure confidentiality leakage.

```bash
python3 -m unittest discover -s tests -p 'test_paired_metrics.py' -v
python3 eval/run_paired_eval.py --export-prompts /tmp/paired-raw.jsonl
python3 eval/run_paired_eval.py --export-prompts /tmp/paired-inline.jsonl --mode inline
python3 eval/run_paired_eval.py --predictions /path/to/model-run.jsonl
```

Prompt export uses the existing inline admission policy and withholds gold decisions/support annotations. Real writer execution remains separate. The scorer rejects missing or duplicate paired observations and records input hashes. See the protocol for labels, limitations and matched-baseline requirements.

## Research status

This is an ongoing project. The broader claim—that a write-boundary policy can reduce disclosure and integrity failures while preserving task utility—remains a hypothesis to test on live models and held-out cases.
