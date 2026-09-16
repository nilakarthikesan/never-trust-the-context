# Never Trust the Context

### A Biba-Grounded Zero-Trust Layer for Enterprise LLM Agents

Working repository for the paper with Prof. Vijay Madisetti. Working title above; see [`outreach/thesis.md`](outreach/thesis.md) for the locked thesis.

We mesh two papers:

- **CI-Work** (Fu et al., ACL 2026 Industry) — a benchmark showing enterprise LLM agents leak sensitive context (violation 15.8–50.9%), and that scaling/prompt defenses do not fix it. Repo cloned at `data/ACV/misc/CI-Work`.
- **Tian & Song** (ISCID 2021) — a zero-trust access-control method combining Bell–LaPadula (confidentiality) and Biba (integrity) with per-component trust scores.

**Thesis:** put a Biba + BLP **zero-trust policy layer at the agent's write boundary**. CI-Work only measures the confidentiality axis (leak / no-leak). We add the missing **integrity axis** (Biba no-write-up): low-trust retrieved context must not contaminate a high-integrity outbound artifact.

## Layout

| Path | What |
|---|---|
| `notes/` | 1-page reading notes for both papers (+ confirmed CI-Work repo interface) |
| `design/mapping-table.md` | The mesh: CI × BLP × Biba × ZT entity/rule mapping; the dual `C`/`I` labels |
| `design/dual-labeled-examples.md` | CI-Work's two published cases fully dual-labeled (source for Figure 1) |
| `design/pep-design.md` | The system: PIP / PDP / PEP, org lattice, initial-trust rule, enforcement modes |
| `design/weight-calibration.md` | **Where every weight comes from.** Three tiers, `w_C`/`w_I` derived instead of hand-set, severity model, two implementation bugs |
| `design/pr-review-benchmark.md` | Benchmark construction for the PR-review agent: rule precedence, the third entry class `E_corr`, entangled twins, worked seeds, null cases |
| `design/pr-review-walkthrough.md` | One case traced end-to-end through BLP, Biba, and zero trust with real arithmetic; two counterfactuals |
| `design/enforcement-mechanics.md` | How read-but-never-emit is actually enforced: the L0–L3 ladder, handle-mediated citation, Biba as action downgrade |
| `outreach/thesis.md` | the locked thesis, falsifiable claim, paper skeleton |
| `outreach/explain-simple.md` | the thesis in plain words (the lease story) + SafeLattice link |
| `outreach/professor-thesis-note.md` | 1-page thesis note to send Prof. Madisetti |
| `src/zt_pep/` | The policy layer implementation (PIP/PDP/PEP, metrics) |
| `eval/` | CI-Work adapter, offline fixture, and the evaluation runner |
| `tests/` | Unit tests for the rules + dual-labeled cases |
| `config/policy.example.yaml` | Tunable policy (every reported number traces here) |
| `config/policy.pr-review.yaml` | PR-review policy with **derived** `w_C`/`w_I` and an artifact-level integrity rubric |

## Quick start (offline, no API key)

```bash
python3 tests/test_pdp.py            # 10 unit tests, incl. regressions for both fixed bugs
python3 eval/run_eval.py --source fixture --judge keyword
python3 eval/verify_walkthrough.py   # reproduces every number in the PR-review walkthrough (needs pyyaml)
```

`verify_walkthrough.py` recomputes the PDP decisions for case `ext-01` under all three request
configurations in `design/pr-review-walkthrough.md` and asserts them, so the prose cannot silently drift
from `config/policy.pr-review.yaml`. It also fails if a regulated entry is ever released by the `θ`
override, which is the §4.4 bug.

Offline demo result (2 dual-labeled CI-Work cases, deterministic keyword judge):

```
                LR     VR     CR     IL     IVR
undefended      50.0  100.0  100.0   25.0   50.0
zt_pep          0.0    0.0   100.0    0.0    0.0     <- cuts leak AND contamination, keeps utility
zt_pep_deny     0.0    0.0     0.0    0.0    0.0     <- naive "refuse": privacy at the cost of all utility
```

`LR/VR/CR` are CI-Work's Leakage/Violation/Conveyance (confidentiality). `IL/IVR` are the **new** Integrity-Leakage / Integrity-Violation metrics (Biba). The story: the PEP beats the privacy-utility trade-off that CI-Work's prompt defenses could not.

> The offline `KeywordJudge`/`KeywordRedactor` are deterministic **stand-ins** for CI-Work's LLM-as-a-Judge and an LLM redactor. They key on distinctive numeric/money tokens and can be noisy on entangled shared numbers; the real evaluation uses the LLM judge (below). They exist so the whole pipeline runs and is testable with zero dependencies.

## Real evaluation on CI-Work data

1. Generate/obtain a CI-Work `formatted_trajectory.json` (see `data/ACV/misc/CI-Work/README.md`; needs Azure/OpenAI keys).
2. Run with the LLM judge that reuses CI-Work's own templates:

```bash
export OPENAI_API_KEY=...   # and OPENAI_API_BASE for Azure
python3 eval/run_eval.py --source formatted \
  --path data/ACV/misc/CI-Work/data/trajectory/<model>/naive/ess4_sen4/formatted_trajectory.json \
  --judge llm
```

## Fixed: two latent policy bugs

Both were found while deriving the weights in `design/weight-calibration.md`, and both were reachable under
the configuration the paper was about to adopt rather than the one already measured.

- [x] **`labels.py` — content markers could override the source channel.** A high-integrity marker such as
  `"approved"` raised `I` to 0.85 regardless of source, so an author-controlled PR description containing
  that one word cleared the Biba check: our own integrity labeler being prompt-injected by the party under
  review. Now the uplift is bounded by provenance (`max_content_uplift`) with an absolute
  `author_controlled_ceiling` applied last. `"approved"` and `"final"` removed from the marker defaults.
  Principle and code in `design/weight-calibration.md` §3.1.
- [x] **`pdp.py` — the `θ` override could release regulated content.** The override applied to `DENY`, not
  just `QUARANTINE`, with no floor. `Entry.regulated` and `Policy.hard_deny_floor` now hard-block above the
  override. Measured across the planned `θ` sweep, the pre-fix code released a named-customer regulated
  entry at every operating point from `θ = 0.2` upward; see the table in
  `design/weight-calibration.md` §4.4.

The offline demo numbers below are unchanged, because `DEFAULT_POLICY` (`w_C = 1.0`, `θ = 0.15`) never
reached the override. That is a fact about the old configuration, not a defense of it. Regression coverage:
`test_author_controlled_marker_cannot_raise_integrity`, `test_regulated_entry_never_released_by_theta`, and
two paired tests pinning the behavior that must *not* change.

## Status / human actions still needed

- [ ] Obtain the full Tian–Song IEEE PDF (paywalled) to lock exact trust-score formulas.
- [ ] Send `outreach/professor-thesis-note.md` to Prof. Madisetti; confirm thesis + venue.
- [ ] Run the LLM-judge evaluation on a CI-Work subset (Upward + External first) once API access is set up.
- [ ] Add Prompt-Defense and CI-CoT baselines (CI-Work Table 2) to the comparison table.
- [ ] Add the `corrupting` entry class to the schema; recompute `IL`/`IVR` over `E_corr` instead of
  `sensitive + essential` (`design/pr-review-benchmark.md` §3).
- [ ] Add `VC` (verdict corruption, paired runs) and `GR` (grounding rate) — the only metrics that measure
  contamination directly rather than by disclosure proxy.
- [ ] Write `ext-01` into `eval/fixtures/cases.json` so `design/pr-review-walkthrough.md` is executable
  rather than hand-computed.
- [ ] Add null seeds (≥20%) to measure false suppression. Without them, over-blocking is invisible and
  `design/pep-design.md` §6's top risk is unmeasured.
- [ ] Run the inverse-scaling experiment (3 model sizes × L0/L1/L2). This is the strongest falsifiable
  claim available: `design/enforcement-mechanics.md` §4 predicts the leakage-vs-size slope flattens under
  handle-mediated citation, contradicting CI-Work's scaling result.
