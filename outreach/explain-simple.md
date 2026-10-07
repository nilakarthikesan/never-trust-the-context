# Confidentiality and Integrity at a Write Boundary

Consider an agent preparing a lease-renewal email. Its context may contain a shareable floor-area requirement, a restricted walk-away price, and an unverified suggestion from a chat thread.

Two questions apply to each entry: may the recipient receive it, and is it reliable enough to support the proposed action? Restricting disclosure addresses confidentiality. Preventing untrusted statements from determining a consequential action addresses integrity.

The prototype checks these labels at a write boundary. Post-hoc mode edits a supplied draft; inline mode admits context before a writer generates the artifact. Restricted content can be withheld or replaced by an approved abstract when one is available. Those abstracts require independent validation because removing distinctive tokens alone does not establish safety against reconstruction.

The offline fixtures illustrate this distinction with fixed labels and deterministic writers/judges. Live-model experiments are needed to test utility, paraphrase handling, reliance on misleading context, and false suppression.

SafeLattice, the related evaluation project, studies severity and information-flow detection in agent traces. This project studies a policy prototype at the write boundary. Neither project provides a general guarantee of agent safety.

See [the project README](../README.md), [policy design](../design/pep-design.md), and [enforcement mechanics](../design/enforcement-mechanics.md).
