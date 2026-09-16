# Reading Note 2 — Tian & Song (Zero Trust via BLP + Biba)

**Xiaopeng Tian, Haohao Song. "A zero trust method based on BLP and BIBA model." 14th Int'l Symposium on Computational Intelligence and Design (ISCID 2021), Hangzhou, pp. 96–100. IEEE.**
DOI: [10.1109/ISCID52796.2021.00031](https://doi.org/10.1109/iscid52796.2021.00031) · IEEE Xplore doc 9679285

> **Status of source:** the full IEEE PDF is paywalled and **not yet obtained** (action item). This note is reconstructed from the published abstract plus three secondary sources that describe the method in detail:
> - He et al., "A Survey on Zero Trust Architecture," *Wireless Comm. & Mobile Computing* 2022, [10.1155/2022/6476274](https://onlinelibrary.wiley.com/doi/10.1155/2022/6476274)
> - Sultana et al. review, PMC 2024, [PMC10892953](https://pmc.ncbi.nlm.nih.gov/articles/PMC10892953/)
> - "Zero Trust Score-based Network-level Access Control in Enterprise Networks," [arXiv:2402.08299](https://arxiv.org/abs/2402.08299) (cites Tian–Song's entity set)
>
> The exact trust-score formula and weight tables live in the PDF; get them before writing the method section.

---

## 1. One-sentence summary

A **control method** (not an agent paper) that reframes zero trust as *dynamic, dual-label BLP + Biba*: compute continuous trust scores for system components and gate every access on a weighted combination of confidentiality and integrity requirements.

## 2. The two classical models it builds on

- **Bell–LaPadula (BLP) — confidentiality.** Simple Security Property = **no read up**; ⋆-property = **no write down**. Goal: keep secrets from leaking to lower classifications.
- **Biba — integrity.** Simple Integrity Axiom = **no read down**; ⋆-Integrity Axiom = **no write up**. Goal: keep low-integrity (untrusted) data from corrupting high-integrity data.

Mnemonic: *BLP keeps secrets from leaking down; Biba keeps garbage from flowing up.*

The two are duals and are the canonical MLS pair (NIST IR 7316). Enforcing both simultaneously is known to be restrictive — a key design tension we inherit.

## 3. Tian–Song's contribution

- **Expand** the notions of *subject*, *object*, and *security label* beyond static MLS levels.
- Assign **comprehensive trust scores** to five component types:
  - **users**
  - **terminals**
  - **channels**
  - **files**
  - **applications**
- Set **different weights** for confidentiality vs integrity requirements, so access decisions balance both goals per object.
- Operate under zero-trust "never trust, always verify": trust is continuous and re-evaluated, not granted by location/ownership.

Entity set per arXiv:2402.08299: Tian–Song use **user, terminal, file, channel** as trust entities.

## 4. Weaknesses the literature already flags (our contributions answer these)

From He 2022 and PMC 2024 reviews, verbatim gist:
- **No principled initial-trust assignment** for users/terminals/environments/objects → "cannot effectively avoid human-factor errors in initial trust."
- **Weight distribution is ad hoc / not reasonable enough**; completeness and rationality of the weight list "for further study."
- Still a **network/OS access-control** paper — never applied to LLM agents or to information-flow inside a model's context window.

## 5. How this connects to NIST zero trust (for background section)

- **NIST SP 800-207**: ZTA = Policy Engine (PE) + Policy Administrator (PA) + Policy Enforcement Point (PEP). No implicit trust by network location. PEP can be a device agent + resource gateway.
- **NIST SP 800-207A**: cloud-native ZT uses sidecar proxies as distributed PEPs enforcing identity-based policy (SPIFFE/SVID).
- SP 800-207 explicitly warns about **AI/software agents** authenticating to ZT management components and being **coerced into acting on an attacker's behalf** — which is exactly the CI-Work user-pressure result, seen from the ZT side.

## 6. What we take vs what we change

| We take from Tian–Song | We change / add |
| --- | --- |
| Dual BLP + Biba labels on every object | Objects are **retrieved context entries**, not files on disk |
| Continuous trust scores per component | Components are user, **LLM agent (application)**, tool/channel, entry, recipient |
| Weighted confidentiality/integrity decision | State an **explicit initial-trust rule** (fixes their published weakness) |
| "Never trust, always verify" per request | Verify at the **agent's final write action**, inside the CI-Work loop |
| — | Evaluate on a **real benchmark (CI-Work)** with quantitative metrics — they had none |

## 7. Why the professor's ordering "Biba → CI-Work → Zero Trust" is right

1. **CI-Work** supplies the enterprise-agent *problem* + the *eval harness*.
2. **Biba** supplies the *integrity* rule CI-Work never measures (no-write-up = don't let low-trust context contaminate a high-integrity artifact).
3. **Zero Trust** (Tian–Song + NIST) is the *architecture* that makes both BLP-style disclosure control and Biba-style contamination control happen **per request**, replacing the "prompt and hope" defenses CI-Work showed to be insufficient.
