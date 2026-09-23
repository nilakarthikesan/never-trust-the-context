# Paper: Never Trust the Context

LaTeX source for the conference submission. Sections are split so two people can edit without conflicts.

## Venue

**Primary target: IEEE S&P 2027, Cycle 2.**

| | Date |
|---|---|
| Abstract registration | **Tue Nov 10, 2026** — mandatory |
| Paper submission | **Tue Nov 17, 2026** |
| Early reject notice | Mon Jan 18, 2027 |
| Reviews released | Thu Feb 11, 2027 |
| Rebuttal + interactive period | Feb 16–26, 2027 |
| Notification | Fri Mar 5, 2027 |
| Conference | May 17–20, 2027, Montreal |

**Fallback: USENIX Security '27 Cycle 2, Tue Jan 26, 2027.** Ten weeks later, notification
May 6. If the LLM-judge experiment hasn't landed by ~Nov 1, roll to this rather than submit
thin — reviewers rotate across all four big security venues, and a weak submission burns the
cycle.

**Register the Nov 10 abstract regardless.** It's free and reversible. A mandatory abstract
gate is exactly what cost us SaTML 2027 (abstract was due Sep 22, unextended; the Sep 29 paper
deadline was irrelevant once that passed). Track deadlines at https://sec-deadlines.github.io/.

Venues checked and closed: SaTML 2027 (abstract Sep 22), NDSS 2027 fall (Aug 19), ACM AISec
2026 (Jul 24), AGENT-SEC 2026 (Jul 23), ACSAC 42 technical papers (May 26). ACM CCS 2027 CFP
was not posted as of Sep 23, 2026; historically Cycle A lands in January.

### S&P hard requirements — violating any is desk rejection

These are stricter than most IEEE venues and differ from the SaTML setup this draft started in.

- **`\documentclass[conference,compsoc]{IEEEtran}`.** The plain `[conference]` IEEE template
  is *explicitly* named as grounds for rejection without review. Already set in `main.tex`.
- IEEEtran.cls **v1.8b**, **US Letter** (not A4).
- **Do not** modify margins, font, or line spacing; no "egregious space scrunching."
- **Do not** `\usepackage{usenix}` — it silently overrides compsoc formatting.
- **13 pages of text + 5 pages references/appendices = 18 max.** Everything past page 13 must
  be clearly marked as appendix. Reviewers are not required to read appendices.
- **Anonymous**, including the IEEE template's default fake names. Cite our own prior work in
  the third person. `main.tex` keeps the author block commented — leave it that way.
- **No full CVE identifiers** (they deanonymize). Verified absent.
- **"Ethics Considerations" field is mandatory** on HotCRP at registration. If we believe there
  are none we must still explain how we reached that conclusion. Our §8 content covers this.
- An author may register at most 6 papers per cycle; the cap binds at abstract registration.

### ⚠️ Open action item: the artifact repo is not anonymous

S&P requires artifact repositories to be anonymized too, and explicitly warns that **account
and repository names must not identify the authors**. Ours is
`github.com/nilakarthikesan/never-trust-the-context`, which fails on the account name.

Before Nov 17, mirror the artifact through **Anonymous GitHub** or **GitFront**, and scrub
author-identifying comments and commit metadata. Note also that **artifact repos must not be
updated after the paper deadline** — so freeze the mirror at submission.

## Building

No LaTeX toolchain is installed locally.

**Overleaf.** Two upload bundles are generated at the repo root (gitignored; regenerate with
the commands below):

- `overleaf-SINGLEFILE.zip` — flat, two files, no subfolders. Use this if an upload has ever
  failed with `File 'sections/01-intro.tex' not found`, which happens when the `sections/`
  folder doesn't survive the upload.
- `overleaf-MODULAR.zip` — `main.tex` + `refs.bib` + `sections/`. Better for collaboration.

In Overleaf: **New Project → Upload Project → drop the zip.** Set the main document to
`main.tex` if it isn't detected.

**Regenerating the bundles** (run from the repo root):

```bash
# refresh the single-file build after editing ANY section
cd paper && python3 -c "
import re, pathlib
m = pathlib.Path('main.tex').read_text()
m = re.sub(r'\\\\input\{([^}]+)\}', lambda x: pathlib.Path(x.group(1)+'.tex').read_text(), m)
pathlib.Path('main-standalone.tex').write_text(m)"

# rebuild both zips
mkdir -p /tmp/ovflat && cp paper/main-standalone.tex /tmp/ovflat/main.tex \
  && cp paper/refs.bib /tmp/ovflat/ \
  && (cd /tmp/ovflat && zip -qr "$OLDPWD/overleaf-SINGLEFILE.zip" .) && rm -rf /tmp/ovflat
(cd paper && zip -qr ../overleaf-MODULAR.zip main.tex refs.bib sections/)
```

`main-standalone.tex` is **generated** — never edit it directly. Edit `sections/*.tex` and
regenerate, or the two will diverge.

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
