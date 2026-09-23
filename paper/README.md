# Paper: Never Trust the Context

LaTeX source for the conference submission. Sections are split so two people can edit without conflicts.

## Venue

**Primary target: IEEE SaTML 2027.** Chosen because the topic list is a direct hit
("novel defenses for machine learning", "machine learning system security", "privacy in
machine learning", "secure and safe machine learning in practice") and because it has
*mandatory artifact submission* — our artifact runs in under a second with no dependencies,
which is a genuine advantage rather than a chore.

| | Date | Note |
|---|---|---|
| Abstract registration | **Tue Sep 22, 2026** | Mandatory. Tentative title, non-blank abstract, **fixed author list**, fixed topics. |
| Paper submission | **Tue Sep 29, 2026** | |
| Early reject notice | Wed Nov 4, 2026 | |
| Discussion + revision | Nov 25 – Dec 9, 2026 | SaTML has an interactive revision phase, which favors a paper with a strong idea and a thin eval. |
| Decision | Wed Dec 16, 2026 | |
| Conference | Early May 2027, Reykjavik | |

Submission is **anonymous**. `main.tex` keeps the author block commented out; do not uncomment
it until camera-ready.

**Fallback: USENIX Security '27 Cycle 2, Tue Jan 26, 2027.** Four extra months, which is
roughly what the open experiments need. The writing carries over directly; only the class
file and the page budget change. Registering the SaTML abstract on Sep 22 costs nothing and
keeps both doors open, so do that regardless of which way the Sep 29 decision goes.

Other venues checked and closed: NDSS 2027 fall cycle (Aug 19), ACM AISec 2026 (Jul 24),
AGENT-SEC 2026 (Jul 23), ACSAC 42 technical papers (May 26). ACSAC still has poster/WiP
tracks open around Sep 19–22 if a low-cost feedback venue is wanted.

## Building

No LaTeX toolchain is installed locally. Two options:

**Overleaf (recommended for collaboration).** Upload the `paper/` directory as a new project.
It compiles as-is; `IEEEtran` is in Overleaf's standard distribution.

**Locally**, install MacTeX (`brew install --cask mactex-no-gui`), then:

```bash
cd paper && latexmk -pdf main.tex
```

## Layout

| File | Contents |
|---|---|
| `main.tex` | Preamble, notation macros, abstract, section includes |
| `refs.bib` | Bibliography, grouped by role in the argument |
| `sections/01-intro.tex` | Motivation, production incidents, **RQ1–RQ3**, contributions |
| `sections/02-background.tex` | CI, BLP/Biba, zero trust, prompt injection, related work |
| `sections/03-threat.tex` | Formal threat model, the two failure conditions, adversaries |
| `sections/04-method.tex` | **Architecture**, labels, PDP, precedence, ladder, action downgrade, weights |
| `sections/05-benchmark.tex` | Three entry classes, twins, null seeds, metrics |
| `sections/06-eval.tex` | Results, organized by RQ |
| `sections/07-discussion.tex` | Theory contributions, the two bugs, the prediction, limitations |
| `sections/08-ethics.tex` | Conclusion, ethics, open science |
| `sections/09-appendix.tex` | Reproduction, full case text, severity model, parameter inventory |

## Conventions

- **Use the notation macros** (`\Cl`, `\Il`, `\clr`, `\lvlI`, `\Eess`, `\Esens`, `\Ecorr`,
  `\sys`). Never hardcode `$C$` or the system name — we may rename either.
- **`\needsrun{...}`** marks a claim that is written but not yet backed by a run.
  **`\todo{...}`** marks missing prose or figures. Both render in color; both must be gone
  before submission. `grep -rn 'needsrun\|todo' sections/` is the pre-submission checklist.
- Every number in the paper must trace to `config/` or to a command in Appendix A.

## Open experiments, in priority order

Ordered by how much each one changes the paper's standing, not by effort.

1. **LLM-judge run on CI-Work trajectories.** Without this the paper evaluates on three
   hand-built cases with a keyword judge. This is the single biggest credibility gap.
   Needs `OPENAI_API_KEY` / `OPENAI_API_BASE`.
2. **Inverse-scaling experiment** (3 model sizes × L0/L1/L2). The headline falsifiable claim
   of §7.3. Small matrix, large payoff — it directly contradicts CI-Work's scaling result if
   it works.
3. **`VC` (verdict corruption) and `GR` (grounding rate).** §6.5 shows `IL` undercounts
   contamination by exactly the entries silently believed rather than repeated. Until `VC`
   exists, all integrity results are a lower bound. `VC` needs paired runs per case.
4. **Scale the suite to ~100 seeds, ≥20% null.** Current n=3 supports existence claims only.
5. **θ sweep** over 0.0→0.5 with the leakage/conveyance curve, plus sensitivity at θ/2 and 2θ.
   §4.9 argues a single θ with no curve is not defensible — so we must not ship one.
6. **Prompt-Defense and CI-CoT baselines** from CI-Work Table 2, run on our suite. Right now
   we compare against their published numbers on *their* cases, which is not a like-for-like
   comparison and a reviewer will say so.
7. **Labeler agreement study** (Tier 2 protocol, §4.9). Two annotators, held-out split.
   Determines whether inference mode is deployable at all.
8. **Adversarial reconstruction check** on L2 abstracts. Until it exists, abstract safety is
   an assumption, and we say so in §7.5.

Items 1–3 are what separate "interesting design paper" from "result." If only one can be
done before Sep 29, do 1.

## Figures still to draw

- **Figure 1** — two-panel dual-labeled CI-Work transcript: entries as a C×I scatter, the sent
  message, arrows marking the BLP leak and the Biba contamination. Source content is in
  `design/dual-labeled-examples.md`; both panels are fully specified there.
- **Figure 2** — the request pipeline as a block diagram, with the two ceilings (`clr_C`,
  `lvl_I`) marked and the content/action planes as parallel tracks. Source in
  `design/pep-design.md` and §4.1.
- **Figure 3** (if space) — θ sweep curve, once experiment 5 lands.

## Title

Currently *"Never Trust the Context: A Biba-Grounded Zero-Trust Write Boundary for Enterprise
LLM Agents."* The repo README uses "Layer" instead of "Write Boundary"; pick one before
abstract registration. "Write Boundary" names the contribution more precisely.
