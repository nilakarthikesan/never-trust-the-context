# An opt-in collaboration around evidence reliability

Discussion draft, October 18, 2026. These are possible work packages, not assignments, promises of authorship or statements about anyone's personal motivations. No outreach has been sent and no collaborator has been added to a manuscript.

## A shared intellectual question

An agent can misunderstand a mistaken account without being explicitly told to ignore instructions. Can we describe that failure precisely, distinguish it from malicious steering, and test whether the agent verifies the evidence before acting?

There is a substantive bridge to [Brei et al., *Classifying Unreliable Narrators with Large Language Models*, ACL 2025](https://arxiv.org/abs/2506.10231): that paper distinguishes types of unintentional misrepresentation using annotated narratives. Anneliese Brei is a listed author of that public paper. This establishes topical overlap, not her interest in this new project or an agreement to join it. Source reliability in agent workflows is a different task and the transfer must be tested.

The identity and research interests of the second proposed collaborator should be confirmed before tailoring a named role. Do not infer expertise or preferences from a first name, a referral relationship or a different person's profile.

## Offer ownership rather than a request to “help”

Let each person choose or decline one bounded package after seeing the question, current limitations and expected time. Possible packages:

- **Evidence taxonomy and annotation:** compare narratological unreliability with stale evidence, mistaken claims, conflicting sources and deliberate attacks. Deliver an annotation guide, independently label a small pilot, and analyze disagreement. This is central intellectual work, not clerical labeling.
- **Agent evaluation and causal design:** own clean/perturbed matching, benign and helpful controls, endpoint definitions and judge validation. Deliver a prespecified protocol and failure taxonomy, including cases where the intervention makes the agent worse.
- **Systems and reproducibility:** own the writer adapter, source metadata boundary, intervention baselines, run manifests and artifact. Deliver a reproducible real-model pilot with costs, logs and a candid analysis.

The project initiator can take the engineering package, leaving genuine choice over the research framing and analysis. Do not preassign the first two packages to particular people without asking what they want to own. A short review-only contribution is also a legitimate option.

## A concrete first meeting

Share the [reading map](../notes/context-provenance-literature-2026-10-18.md) and [pilot protocol](paired-outcome-study.md). Ask each participant which question they would change, which related paper challenges the proposed contribution, and what a useful two-week outcome would be for them. Agree on a small deliverable, time budget and check-in, then let participants decide whether to continue.

A draft invitation for the user to adapt and send personally:

> I narrowed Never Trust the Context to a question we can test: when an agent reads a mistaken or manipulative account, can we prevent it from changing a correct decision without suppressing useful context? The current prototype is small and has no real-model result yet. I see a connection to research on unreliable narrators, but I want us to decide together whether that transfer is interesting. Would you like to review the ten-case pilot and choose a bounded part to own—taxonomy/annotation, evaluation design, or the agent implementation? We can agree on scope first and decide after a short pilot whether to pursue a paper.

## Credit and decision rights

Record contributions and decisions as work happens. Discuss authorship criteria and order early, revisit them based on actual intellectual and implementation contributions, and obtain every author's agreement before submission. Do not add names because somebody attended a meeting or because collaboration was proposed. All human authors need to inspect and take responsibility for the work; AI assistance is disclosed as appropriate and is not authorship.

For the project initiator's research-engineering goal, the strongest near-term evidence is a rigorous implemented evaluation with a clear failure analysis and successful collaboration. That can demonstrate relevant skills; it does not imply a hiring outcome. A narrow study that changes its hypothesis when evidence demands it is a stronger research artifact than several unrelated grand claims.
