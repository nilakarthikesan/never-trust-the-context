"""Strict offline scoring of externally supplied correction-scope judgments.

Reference labels must come from the separate finite-record oracle. This module
neither calls a model nor infers truth, scope, or textual entailment. Evidence-set
agreement is agreement with this fixture oracle, not proof of model reliance.
"""
from __future__ import annotations

import json
from collections import Counter

SCOPES = ("historical_assertion", "current_endorsement", "current_support")
STATUSES = ("supported", "opposed", "conflicted", "unsupported")
CLAIM_FIELDS = {"claim_id", "scope", "status", "supporting_records", "opposing_records"}


def response_schema():
    """Public output schema; enumerates labels without revealing any claim's gold scope."""
    return {
        "type": "object", "additionalProperties": False,
        "required": ["packet_id", "claims"],
        "properties": {
            "packet_id": {"type": "string"},
            "claims": {"type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "required": sorted(CLAIM_FIELDS),
                "properties": {
                    "claim_id": {"type": "string"},
                    "scope": {"type": "string", "enum": list(SCOPES)},
                    "status": {"type": "string", "enum": list(STATUSES)},
                    "supporting_records": {"type": "array", "items": {"type": "string"},
                                           "uniqueItems": True},
                    "opposing_records": {"type": "array", "items": {"type": "string"},
                                         "uniqueItems": True},
                },
            }},
        },
    }


def _identifier(value):
    return isinstance(value, str) and bool(value.strip())


def validate_prediction(value):
    if not isinstance(value, dict) or set(value) != {"packet_id", "claims"}:
        raise ValueError("prediction must contain exactly packet_id and claims")
    if not _identifier(value["packet_id"]) or not isinstance(value["claims"], list):
        raise ValueError("packet_id must be a string and claims must be a list")
    seen = set()
    for claim in value["claims"]:
        if not isinstance(claim, dict) or set(claim) != CLAIM_FIELDS:
            raise ValueError("claim has missing or unexpected output fields")
        if not _identifier(claim["claim_id"]) or claim["claim_id"] in seen:
            raise ValueError("empty or duplicate claim id")
        seen.add(claim["claim_id"])
        if claim["scope"] not in SCOPES or claim["status"] not in STATUSES:
            raise ValueError("unknown scope or evidence status; world-truth labels are not statuses")
        for field in ("supporting_records", "opposing_records"):
            records = claim[field]
            if not isinstance(records, list) or any(not _identifier(r) for r in records):
                raise ValueError("evidence references must be lists of nonempty record ids")
            if len(set(records)) != len(records):
                raise ValueError("duplicate evidence reference")
        if set(claim["supporting_records"]) & set(claim["opposing_records"]):
            raise ValueError("one record cannot be both supporting and opposing")
    return value


def parse_predictions(text):
    """One complete response object per nonblank JSONL line; never repair malformed output."""
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    predictions = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line, object_pairs_hook=unique_object)
            predictions.append(validate_prediction(value))
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            raise ValueError(f"invalid prediction on line {line_number}: {error}") from error
    return predictions


def evaluate(reference, predictions, allowed_records):
    """Score complete packets; reject missing/duplicate/unknown observations.

    reference is keyed by public (packet_id, claim_id), with oracle scope/status
    and supporting/opposing record lists. Unknown citations remain measurable
    mistakes rather than disappearing as schema failures.
    """
    if not reference:
        raise ValueError("cannot score an empty reference")
    expected = set(reference)
    index = {}
    seen_packets = set()
    known_packets = {p for p, _ in expected}
    for prediction in predictions:
        validate_prediction(prediction)
        packet_id = prediction["packet_id"]
        if packet_id not in known_packets or packet_id in seen_packets:
            raise ValueError("unknown or duplicate prediction packet")
        seen_packets.add(packet_id)
        for claim in prediction["claims"]:
            key = (packet_id, claim["claim_id"])
            if key not in expected:
                raise ValueError("unknown prediction claim")
            index[key] = claim
    missing = expected - set(index)
    if missing:
        raise ValueError(f"missing {len(missing)} claim predictions; incomplete runs are not scored")

    totals = Counter()
    by_scope = {scope: Counter() for scope in SCOPES}
    confusion = {status: {p: 0 for p in STATUSES} for status in STATUSES}
    detail = []
    for key in sorted(expected):
        gold = reference[key]
        prediction = index[key]
        scope_ok = prediction["scope"] == gold["scope"]
        status_ok = prediction["status"] == gold["status"]
        support_ok = set(prediction["supporting_records"]) == set(gold["supporting_records"])
        opposition_ok = set(prediction["opposing_records"]) == set(gold["opposing_records"])
        evidence_ok = support_ok and opposition_ok
        unknown = sorted((set(prediction["supporting_records"]) |
                          set(prediction["opposing_records"])) - set(allowed_records[key[0]]))
        flags = {"scope_correct": scope_ok, "status_correct": status_ok,
                 "scope_status_correct": scope_ok and status_ok,
                 "evidence_sets_exact": evidence_ok,
                 "all_fields_correct": scope_ok and status_ok and evidence_ok}
        totals["n_claims"] += 1
        by_scope[gold["scope"]]["n_claims"] += 1
        for field, passed in flags.items():
            totals[field] += passed
            by_scope[gold["scope"]][field] += passed
        totals["claims_with_unknown_citations"] += bool(unknown)
        confusion[gold["status"]][prediction["status"]] += 1
        detail.append({"packet_id": key[0], "claim_id": key[1],
                       "oracle": dict(gold), "prediction": dict(prediction),
                       **flags, "unknown_record_ids": unknown})

    def rates(counts):
        n = counts["n_claims"]
        return {"n_claims": n, **{
            field + "_rate": counts[field] / n if n else None
            for field in ("scope_correct", "status_correct", "scope_status_correct",
                          "evidence_sets_exact", "all_fields_correct")
        }}

    return {
        "artifact_kind": "offline correction-scope scoring; no model runner or action evaluation",
        "scope_source": "externally supplied claim scopes; gold scopes withheld from prompts",
        "summary": {"n_packets": len(known_packets), **rates(totals),
                    "claims_with_unknown_citations": totals["claims_with_unknown_citations"]},
        "by_gold_scope": {scope: rates(counts) for scope, counts in by_scope.items()},
        "status_confusion": confusion,
        "per_claim": detail,
        "limitations": [
            "Scores concern authored synthetic development packets, not a held-out benchmark or generalization estimate.",
            "Scope correctness and evidence-status correctness are separate; joint metrics expose masking.",
            "Evidence-set agreement uses authored finite semantics, not natural-language entailment or world truth.",
            "Proposition identity, value, and attribution target remain authored oracle ASTs; only scope/status/citations are judged here.",
            "External prediction origin/model identity is not independently verified.",
            "No verification tool, approval action, regeneration audit, or causal reliance is evaluated.",
        ],
    }
