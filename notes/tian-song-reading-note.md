# Reading Note: Tian and Song, BLP, and Biba

Xiaopeng Tian and Haohao Song, “A zero trust method based on BLP and BIBA model,” ISCID 2021, pp. 96–100. [DOI: 10.1109/ISCID52796.2021.00031](https://doi.org/10.1109/ISCID52796.2021.00031).

## Source status

The full IEEE paper has not yet been obtained. This note records the abstract and secondary descriptions, so comparisons with its complete method remain provisional. The original trust-score formulas, entity definitions, weight tables, initial-trust treatment, and evaluation details need verification from the full paper.

Secondary reading leads:

- He et al., “A Survey on Zero Trust Architecture,” 2022, [DOI: 10.1155/2022/6476274](https://onlinelibrary.wiley.com/doi/10.1155/2022/6476274).
- [2024 review, PMC10892953](https://pmc.ncbi.nlm.nih.gov/articles/PMC10892953/).
- [Zero Trust Score-based Network-level Access Control in Enterprise Networks](https://arxiv.org/abs/2402.08299).

## Classical models

Bell–LaPadula addresses confidentiality through no-read-up and no-write-down rules. Strict Biba addresses integrity through no-read-down and no-write-up rules. Applying both can restrict information flow substantially, which motivates explicit decisions about admission, attribution, and action capability.

Available summaries describe component trust scores and weighted confidentiality/integrity requirements. They mention users, terminals, files, channels, and applications, but the exact entity set and scoring rules should be checked in the full paper.

## Questions informing this prototype

How are initial labels assigned? Which parameters follow from access policy, and which require empirical calibration? How are provenance and content signals combined? How sensitive are decisions to label error?

The prototype states explicit priors, provenance caps, thresholds, and weights so they can be inspected and tested. This is a design choice under evaluation, rather than evidence that the project fixes a verified defect in Tian and Song's complete method.

## Application to language model agents

This project treats retrieved entries as labeled objects and checks disclosure and integrity requirements at an outbound write boundary. The implementation has rule tests and selected CI-Work-derived fixtures. Wider CI-Work trajectory evaluation remains planned; this repository does not establish that Tian and Song lacked evaluation or quantitative metrics.

CI-Work provides the confidentiality/conveyance setting. Biba motivates a separate integrity requirement. The current `IL` and `IVR` metrics measure disclosure of low-integrity content; they do not directly measure a model's reliance on it. Paired verdict-corruption and grounding measurements are proposals requiring implementation and validation.

NIST zero-trust architecture is a related reference for policy decision and enforcement components. The prototype uses this vocabulary to organize its per-request pipeline; the terminology alone does not establish successful zero-trust deployment.
