# Reading Note 1 — CI-Work

**Fu, Qin, Zhang, Lin, Wutschitz, Sim, Rajmohan, Zhang. "CI-Work: Benchmarking Contextual Integrity in Enterprise LLM Agents." ACL 2026 Industry Track.**
arXiv: [2604.21308](https://arxiv.org/abs/2604.21308) · MSR page: [aka.ms/ci-work](https://aka.ms/ci-work) · code/data: `https://aka.ms/ci-work-code`

---

## 1. One-sentence summary

CI-Work is a **benchmark** (not a defense) that measures whether an enterprise LLM agent can convey the *essential* content of a task while withholding *sensitive* content when both are entangled in a dense retrieval context.

## 2. The problem they frame

Enterprise agents (Microsoft 365 Copilot, Claude Cowork, etc.) retrieve internal data (email, Slack, Notion, calendar, meeting transcripts) and *act* on the user's behalf. The core capability — retrieve-and-act — is also the attack surface. The failure is a **Contextual Integrity (CI)** violation (Nissenbaum 2004): information flows to a recipient it should not, given the context.

Three gaps in prior CI benchmarks (ConfAIde, CI-Bench, PrivacyLens, CIMemories, PrivaCI-bench) that CI-Work claims to close:
1. Prior work isolates a **single** information flow; enterprises have **parallel, entangled** flows.
2. Prior utility metrics measure task completion, not the **precision** of separating essential from sensitive.
3. Prior contexts are short; real enterprise data is a dense "needle in a corporate haystack" (avg context length ~1007 tokens vs 55–106 in prior benchmarks).

## 3. Formal risk model (their §3 — we extend this)

- User `u` owns a private unstructured store `D`.
- Agent `A` gets instruction `I`, uses toolkit `T`, produces trajectory `H = {(a_t, o_t)}`.
- Cumulative retrieved entries `E = ∪ o_t`, partitioned into:
  - **Essential set `E_ess`** — needed to fulfill `I`
  - **Sensitive set `E_sens`** — violates privacy norms if disclosed to the recipient
- Risk = final action `a_fin` discloses any `E_sens` while conveying `E_ess`.

CI is described by 5 parameters: **data subject, sender, recipient, data type, transmission principle**.

Five organizational **flow directions**:
- **Downward** (management → staff)
- **Upward** (report to superior) — *highest leakage/violation in their results*
- **Lateral** (peers)
- **Diagonal** (cross-org)
- **External** (stakeholders/outsiders)

## 4. Metrics (we reuse these verbatim)

Binary judge `F_disc(a_T, e) ∈ {0,1}` = "did the final action disclose entry `e`?" (LLM-as-a-Judge, 83–91% agreement with humans).

- **Leakage Rate (LR)** = `Σ_{e∈E_sens} F_disc / |E_sens|` — proportion of sensitive entries disclosed
- **Violation Rate (VR)** = `max_{e∈E_sens} F_disc` — binary: any sensitive disclosure in the case
- **Conveyance Rate (CR)** = `Σ_{e∈E_ess} F_disc / |E_ess|` — proportion of essential entries transmitted

Goal: LR↓ VR↓ CR↑.

## 5. Construction pipeline (4 stages)

1. **Task-oriented seed generation** — sender + recipient + task; human-in-the-loop with Gemini-3-Pro; 25 manual + 100 synthetic = **125 seeds**, 20% per direction.
2. **Contextual entries generation** — LLM synthesizes atomic essential/sensitive entries; **Self-Iterative Refinement** (Algorithm 1): blind-classify each entry, if perceived label ≠ intended label, critique + rewrite. 9 sensitive data-type categories.
3. **Case episode generation** — assign each entry to a source tool, build a realistic vignette + instruction.
4. **Trajectory simulation & evaluation** — ToolEmu/PrivacyLens-style sandbox; LLM simulates tool observations; sensitive atoms are woven into mixed artifacts (realistic entanglement). Default 4 essential + 4 sensitive per seed → 1000 entries.

## 6. Findings we quote and attack

- **Violation 15.8% (DeepSeek-R1) – 50.9% (Grok-3)**; leakage up to **26.7%**; leakage mostly >10%.
- **Privacy–utility trade-off**: CR correlates positively with LR (Pearson r=0.40, p=0.006) and VR (r=0.39, p=0.008). Better conveyance ⇒ more leakage.
- **Direction effects**: Upward leaks more than Downward (VR p=0.006); External leaks less than within-company.
- **Entry quantity**: more entries → VR↑ monotonically, CR↓, but LR *proportion* drops (dilution effect).
- **Entry length**: longer → CR↑ but LR↑ and VR↑.
- **User pressure**: implicit ("be thorough") raises LR/VR; explicit (lists sources) ~doubles VR baseline; CR *also* drops — a lose–lose collapse.
- **Inverse scaling**: bigger GPT-4.1 variants convey more *and* leak more; they attribute it to (a) small models miss sensitive needles, (b) big models are more sycophantic to user instructions over implicit norms.
- **Reasoning effort**: marginal help only.
- **Defense prompts (Table 2)**: Prompt Defense → LR 8.96/VR 21.31/CR 81.01; CI-CoT → LR 8.95/VR 22.13/CR 84.90 (vs undefended 11.21/27.83/93.04). Both leave **VR > 20%** and **cut CR by ~9–12 points**.

**Their conclusion (our opening):** *"safeguarding enterprise workflows requires a paradigm shift, moving beyond model-centric scaling toward context-centric architectures."*

## 7. The gap we exploit

CI-Work's essential-vs-sensitive axis is **confidentiality / appropriateness-of-disclosure** only. It never asks the **integrity** question: *may low-trust retrieved content (Slack gossip, unverified chat "tactics", user-pressure dumps) contaminate a high-integrity outbound artifact?* That is **Biba**, not CI.

Evidence it matters is already in their own qualitative examples (Appendix I):
- **Software renewal (Fig 20)**: the sensitive "Procurement Chat Log: Negotiation Tactics" says *plan to present competitor quotes as $90/seat (actual received: $95/seat)*. If an agent repeats that fabricated $90 number to the vendor, that is not (only) a leak — it is a **low-integrity source polluting a high-integrity external negotiation**. CI-Work scores the leak; it does not score the contamination.
- **Lease negotiation (Fig 21)**: walk-away threshold and headcount-reduction plan are **high-C AND high-integrity**; the after-hours security-incident Slack is low-integrity chatter. Different labels on different axes.

**Takeaway:** `E_sens ≠ low-integrity`. Sensitivity (C) and provenance-trust (I) are independent axes. Adding the I axis is the paper's novelty.

## 8. Provenance / status of source

- Full text obtained from the arXiv HTML (2604.21308), including all appendices, Table 1/2, Algorithm 1, and the two qualitative examples. Stored understanding is complete.
- Repo **cloned** (sparse) from `aka.ms/ci-work-code` → `github.com/microsoft/ACV`, subdir `misc/CI-Work`, at `data/ACV/misc/CI-Work`.
- Judge/generation models in the paper: GPT-5.2 for generation+judging; evaluated 9 models (GPT-4o/4.1/5, o3, Grok-3, Qwen-2.5-32B, Kimi-K2, DeepSeek-V3/R1).

## 9. Repo interface facts (confirmed from code — this is what the PEP hooks into)

The pipeline: `generate_trajectory.py` → `format_trajectory.py` → `evaluate_trajectory.py`.

**Final-action tools** (the write boundary; `format_trajectory.py::process_trajectory`):
`GmailSendEmail`, `SlackSendMessage`, `FacebookManagerCreatePost`, `GoogleFormFillerSubmitForm`, `NotionManagerSharePage`, `MessengerShareFile`, `MessengerSendMessage`. The trajectory is split at the first such tool call — everything before is *retrieval*, the call itself is the *final action*.

**`formatted_trajectory.json`** — list of entries, each with:
- `final_action` — e.g. `"Action: GmailSendEmail\nAction Input: {...}"`
- `retrieval_trajectory` — string of all pre-write Action/Observation steps
- `retrieval_entries` — dict `{id -> observation-object}` parsed from the trajectory (this is the pool of what the agent actually saw)
- `case.sensitive_data` / `case.essential_data` — ground-truth entries; each item has `Content` (renamed from `Input Abstract`), `Source` (the tool it lives in), and a category
- `sensitive_entries` / `essential_entries` — the retrieval entries matched to ground-truth items
- `case.detailed_plot` — the `outline` passed to the judge

**Judge** (`evaluate_trajectory.py::identify_usage_of_entry`, templates `identify_usage_{sensitive,essential}.j2`): inputs `(outline, action, entry, data)` → strict JSON `{reasoning, answer: yes/no}`. This is `F_disc`.
- **Leakage** = usage rate over `sensitive_entries`
- **Conveyance** = usage rate over `essential_entries`
- Violation = max over sensitive (any leak).

**Model access**: `helper/models/OpenAI.py` (`OpenAIModel`); `.env` needs `OPENAI_API_KEY` / `OPENAI_API_BASE` (Azure). Default judge engine in code: `gpt-5.2-20251211` / `gpt-5.1`.

**Design consequence:** our PEP can run **post-hoc** on `formatted_trajectory.json` — take `retrieval_entries` (label each with C and I), take the proposed `final_action`, decide allow/redact/deny per entry, emit a sanitized action, then feed the sanitized action to the *same* judge. This gives LR/VR/CR + new integrity metrics without re-running the expensive generation stage. An inline variant would wrap the final tool call in `agent_executor_builder.py`.
