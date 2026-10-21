"""Package a curated research starter, excluding internal outreach/planning notes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "evidence-revision-starter"
FILES = [
    "pyproject.toml", "config/correction-study.json", "config/policy.pr-review.yaml",
    "eval/correction_scope_demo.py", "eval/run_correction_eval.py",
    "eval/build_correction_pilot.py", "eval/analyze_correction_pilot.py",
    "eval/run_correction_models.py", "eval/run_correction_actions.py",
    "eval/summarize_correction_models.py", "eval/verify_walkthrough.py",
    "eval/fixtures/correction_scope_cases.json", "eval/fixtures/correction_pilot.json",
    "eval/fixtures/correction_pilot_manifest.json", "tests/test_pdp.py",
    "tests/test_legacy_integration.py", "paper/correction-grounding-draft.md",
] + [str(path.relative_to(ROOT)) for path in sorted((ROOT / "tests").glob("test_correction*.py"))
] + [str(path.relative_to(ROOT)) for path in sorted((ROOT / "research/correction-grounding").glob("*")) if path.is_file()
] + [str(path.relative_to(ROOT)) for path in sorted((ROOT / "results/correction-grounding").rglob("*")) if path.is_file()]
SOURCE_FILES = [path.name for path in sorted((ROOT / "src/zt_pep").glob("*.py"))]

START_HERE = """# Evidence revision before action

Research package prepared October 21, 2026, from Never Trust the Context.

Begin with [the research guide](research/correction-grounding/README.md),
[short review brief](research/correction-grounding/review-brief.md), and
[four review examples](research/correction-grounding/review-cases.md).

This snapshot includes 24 bounded program contracts, 48 paired evidence packets,
the evidence oracle, executable verification/approval tools, budgeted model and
action runners, analysis tools, the literature ledger, a first draft, and tests.
The saved model attempt produced ZERO predictions due to unavailable quota.
Executed deterministic controls are NONLLM harness checks, not model results.

Python 3.9 or later; PyYAML is needed for the older policy walkthrough:

```sh
python3 tests/test_pdp.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 eval/correction_scope_demo.py validate
python3 eval/build_correction_pilot.py validate
```

Only exported public prompts belong in evaluated model inputs. Fixtures,
private manifests, and scored analyses contain gold labels. These are openly
authored, unvalidated diagnostic tasks, not a held-out benchmark.

Source repository: https://github.com/nilakarthikesan/never-trust-the-context.
Internal correspondence, personal collaborator planning, credentials, Git
metadata, and unrelated workspace outputs are excluded. See MANIFEST.json for
SHA-256 hashes of all included files.
"""


def package(output: Path) -> dict:
    paths = FILES + [f"src/zt_pep/{name}" for name in SOURCE_FILES]
    contents = {path: (ROOT / path).read_bytes() for path in paths}
    contents["README.md"] = START_HERE.encode("utf-8")
    manifest = {
        "artifact": "correction-grounding implementation and explicitly NONLLM diagnostic records",
        "prepared_date": "2026-10-21",
        "model_results_included": False,
        "sha256": {name: hashlib.sha256(data).hexdigest()
                   for name, data in sorted(contents.items())},
    }
    contents["MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as archive:
        for name, data in sorted(contents.items()):
            entry = ZipInfo(f"{PREFIX}/{name}", date_time=(2026, 10, 21, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    with ZipFile(output) as archive:
        bad_entry = archive.testzip()
        if bad_entry:
            raise ValueError(f"Archive integrity check failed: {bad_entry}")
    return {"path": str(output.resolve()), "files": len(contents),
            "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
