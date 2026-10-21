# Software and execution verification

Verified October 21, 2026 on Python 3.9.12. The full suite passes; exact counts and commands are recorded in [verification.json](../../results/correction-grounding/verification.json). Software checks and deterministic controls are not model-performance measurements.

```sh
python3 tests/test_pdp.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 eval/correction_scope_demo.py validate
python3 eval/build_correction_pilot.py validate
python3 eval/verify_walkthrough.py
```

## Checked behavior

- Authenticated owner-scoped withdrawal/replacement preserves history and changes only eligible current evidence; forged notices cannot mutate another owner's record.
- Scope correctness, evidence status, and citations are scored independently. Unknown citations remain errors. Missing/duplicate/unknown observations and modified inputs are rejected.
- Public prompts withhold private world labels, gold scope representations, and family/split metadata. Source records are evidence assertions, not truth guarantees.
- The pilot deterministically reproduces 24 distinct contracts/48 paired packets/144 queries. The sandbox actually executes 72 bounded checks; 10 candidate functions pass all three and 14 fail.
- Real sandbox verification, attempted approval, gate acceptance, and finite truth are separate. Invalid private programs fail before provider contact; no arbitrary code executes.
- Model collection requires explicit configuration and network authorization, reserves cost before each request, records exact synthetic payloads without authorization headers, and preserves failures. HTTP 401/403/429 open a circuit; resume does not silently repeat the blocked batch.
- Successful reported usage releases unused reservations, while failed or missing-usage requests retain their conservative reservation. These accounting values are not guaranteed provider charges.
- Replay checks request/response hashes; reconstruction analysis requires a saved, matching provider trace and a positive query for the same proposition. Empty coverage produces no model accuracy.
- The interactive action runner executes actual model-selected tools, enforces one verification/three transport attempts, and keeps private grades outside model context and public export directories.
- The older redactor interface works through the PEP caller using a fake client. The walkthrough now calls the production PDP; all 27 expected decisions agree, including hard-deny cases that the stale duplicate implementation allowed.

## Executed observations

The [saved results](../../results/correction-grounding/README.md) contain two NONLLM evidence controls through export → predictions → strict scoring → paired analysis, plus 192 actual scripted sandbox tool/action traces from four reference policies. The always-verify policy is perfect on the defining checks by construction; it is a diagnostic, not a new defense.

The attempted raw-history mini-model run returned 48 HTTP 429 failures and zero predictions. A minimal diagnostic reported insufficient quota. No model comparison, successful reconstruction observation, or live model action result is reported. The historical failed-run records predate the new circuit breaker and remain unchanged; their source hash differs from current code. The old vacuous `usage_complete: true` bug is documented in the results record.

## Reproducibility and remaining research validation

The curated package carries a SHA-256 file manifest. Its extracted files are checked independently of the original checkout. Gold-bearing fixtures are included for reproducibility; evaluated models must receive only public exports.

The current symbolic source identities/policies are trusted simulation inputs. Proposition identity and reference labels are authored. Explicit wording makes scope extraction constrained. No independent human validation, held-out benchmark, general entailment model, audit-caused action effect, or empirical method advantage is established. Ordinary grounding and matched-call comparators remain necessary.
