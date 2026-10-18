# Context, provenance and agent evaluation: reading map

Checked October 18, 2026. This is a focused reading map, not a systematic review or a claim of exhaustive coverage. Claims below follow the linked primary records. Preprints are identified as such; benchmark numbers from different environments should not be treated as matched comparisons. Read complete methods and inspect artifacts before finalizing the related-work section.

## The research question worth keeping

Can an agent use third-party context as a clue without promoting that source into authority for a consequential decision? Measure the decision itself, not only whether the agent repeats the source's words. Separate incorrect but non-adversarial accounts, explicit malicious steering, helpful hints, and harmless background.

The existing prototype supplies a useful implementation starting point: independently labeled confidentiality and integrity, an outbound policy check, and inline context admission. Its small deterministic fixtures do not establish live-model effectiveness. Biba-inspired language describes a design lineage, not a new invention of information-flow control.

## First reading session: the closest work

### CI-Work — Fu et al., ACL 2026 Industry

[Primary paper](https://arxiv.org/abs/2604.21308) · [ACL paper](https://aclanthology.org/2026.acl-industry.103.pdf)

Enterprise workflows across five information-flow directions test whether agents convey necessary information without disclosing sensitive context. This motivates the repository's confidentiality/conveyance evaluation. Its aggregate results are not a baseline score for our three original fixtures. The extension to test is whether a model can reach a wrong verdict without repeating misleading material, which the repository's disclosure-based integrity proxies can miss.

Before reuse, pin the artifact version, document how trajectories are constructed, and preserve the original metrics alongside new outcome measurements. The bibliography's original first four author names were incorrect; the primary record gives Wenjie Fu, Xiaoting Qin, Jue Zhang and Qingwei Lin.

### Defeating Prompt Injections by Design / CaMeL — Debenedetti et al., 2025

[Primary paper, revised June 2025](https://arxiv.org/abs/2503.18813) · [Official artifact](https://github.com/google-research/camel-prompt-injection)

CaMeL separates trusted control flow from untrusted data and uses capabilities to constrain information flows at tool calls. This is essential prior work for a security layer outside the model. Our project cannot claim novelty merely because it inserts a policy at an action boundary. A comparison should state which tasks need their actions determined by newly retrieved evidence, what policy guarantees apply, and how confidentiality and decision utility are scored.

### ARGUS — Weng et al., May 2026; revised July 2026 preprint

[Primary paper](https://arxiv.org/abs/2605.03378)

ARGUS audits causal support from runtime evidence to proposed actions, using an influence/provenance graph and task invariants. Its AgentLure benchmark deliberately includes context-dependent decisions. This substantially overlaps a generic proposal to verify that actions are grounded in trustworthy evidence. Read its threat model and action-grounding rules before claiming a new defense. A useful extension would distinguish non-adversarial unreliability from explicit attacks and report false suppression on genuinely useful context.

### Blocking at the Boundary / PAA — Liu et al., October 4, 2026 preprint

[Primary paper](https://arxiv.org/abs/2610.05163)

This work evaluates pending consequential actions using trajectory prefixes and matched attacked/benign executions. Path-Aligned Attribution traces which sources materially supplied action elements. It directly overlaps both paired evaluation and boundary auditing. Therefore, paired verdict corruption is an important repair to this repository's evaluation, not by itself a demonstrated novel research contribution. A fair comparison requires matching the supported action types, backend, failure handling and false-block accounting.

## Second reading session: benchmark design and measurement

### AgentDojo — Debenedetti et al., NeurIPS 2024

[Primary paper](https://arxiv.org/abs/2406.13352) · [Official project](https://agentdojo.spylab.ai/)

An extensible tool-agent environment for adaptive attacks and defenses, with task utility evaluated alongside security. Use it to move beyond isolated classification of suspicious text. Our new closed-context pilot should not be described as an AgentDojo reproduction. The next step is an actual adapter with verified environment state and action outcomes, rather than simply borrowing task descriptions.

### AgentDyn — Li et al., February 2026; revised May 2026 preprint

[Primary paper](https://arxiv.org/abs/2602.03117)

AgentDyn stresses dynamic open-ended tasks and helpful third-party instructions. It challenges a defense that wins by discarding all external material. This motivates our helpful-hint and null controls, but the current pilot is still static and supplies the authoritative evidence directly. Do not infer successful dynamic planning or evidence acquisition from that easier setting.

### AgentCIScope — Guo et al., October 13, 2026 preprint

[Primary paper](https://arxiv.org/abs/2610.19158)

A newly posted multi-application contextual-integrity benchmark with executable tasks and disclosure constraints grounded in policies, persona agreement and sensitive-attribute categories. It evaluates repeated attempts as well as single runs. This is a reason to include repetition, judge validation and policy-source documentation. Its focus on disclosure is adjacent to the proposed wrong-verdict endpoint; neither endpoint subsumes the other.

### Capable but Careless / AgentCIBench — Goel and Gurevych, EMNLP 2026

[Primary paper, revised September 2026](https://arxiv.org/abs/2606.23189) · [Official project](https://ukplab.github.io/emnlp2026-agentcibench/)

Computer-use scenarios make cross-context disclosure executable and deterministically scored. The described failure modes include visual co-location, ambiguous tasks and recipient misalignment. This supplies a complementary evaluation modality to text-only retrieval. Preserve refusal and utility measurements: a system that declines everything does not demonstrate successful privacy-preserving assistance.

## Third reading session: the conceptual bridge

### AI Agents May Always Fall for Prompt Injections — Abdelnabi and Bagdasarian, May 2026 preprint

[Primary paper](https://arxiv.org/abs/2605.17634)

This paper argues that contextual manipulation can evade simple data/instruction separation and that tightening norms can suppress legitimate behavior. It motivates explicit benign counterexamples and organization-specific policy assumptions. Its impossibility argument should be read with its assumptions; it does not mean every bounded control is useless, nor does our pilot refute it by removing untrusted text.

### Classifying Unreliable Narrators with Large Language Models — Brei et al., ACL 2025

[Primary paper](https://arxiv.org/abs/2506.10231)

TUNa uses a narratological taxonomy and human annotations to study unintentional misrepresentation, including within-account and cross-account inconsistencies. This offers an intellectually substantive bridge to source reliability rather than a claim that all unreliable sources are attackers. A possible shared project would adapt that distinction to agent evidence, annotate the source of disagreement, and test how an agent verifies or qualifies a claim before acting. The transfer from narratives to tool-agent decisions remains a hypothesis.

## Candidate contribution and limits

A defensible candidate is **evidence-status-aware agent evaluation across malicious steering, mistaken accounts and useful hints**, with separate outcome, disclosure and utility measurements under label uncertainty. Novelty is not established. First compare the precise labels, interventions and endpoints with ARGUS, PAA, AgentDyn and the latest contextual-integrity benchmarks; narrow or abandon any already-covered component.

Classical BLP/Biba and zero trust remain background. The full Tian–Song paper has not been obtained in this repository, so its exact scoring formulas and evaluation must not be reconstructed from summaries. Keep that uncertainty explicit.

The next useful artifact is not a larger collection of untested claims: it is a versioned pilot with matched inputs, a validated scorer, independent annotations, a small real-model run and failure analysis. See [paired study protocol](../design/paired-outcome-study.md).
