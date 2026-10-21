"""Synthetic finite-record correction-scope oracle; no parser or LLM evaluation.

This demo separates historical assertion, current source endorsement, and current
admissible support. Neither support nor withdrawal determines world truth.
Issuer identity and support policies are trusted simulation metadata: this is not
an authentication implementation. Retraction archives records; nothing is erased.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

DEFAULT_SUITE = Path(__file__).resolve().parent / "fixtures/correction_scope_cases.json"
KINDS = {"historical_assertion", "current_endorsement", "current_support"}
IMMUTABLE_FIELDS = ("record_id", "source_owner", "proposition_id", "value", "text")


def _validate_record(record, packet):
    if not isinstance(record["record_id"], str) or not record["record_id"]:
        raise ValueError("record_id must be a nonempty string")
    if record["source_owner"] not in packet["sources"]:
        raise ValueError("record owner is not a declared source")
    if record["proposition_id"] not in packet["propositions"]:
        raise ValueError("unknown proposition")
    if type(record["value"]) is not bool:
        raise ValueError("this finite demo requires boolean proposition values")
    if record["status"] not in {"active", "archive"}:
        raise ValueError("unknown record status")
    if not isinstance(record["text"], str):
        raise ValueError("record text must be a string")


def validate_packet(packet):
    ids = [r["record_id"] for r in packet["records"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate initial record id")
    for policy in packet["sources"].values():
        if not set(policy["may_support"]) <= set(packet["propositions"]):
            raise ValueError("source policy names an unknown proposition")
    for record in packet["records"]:
        _validate_record(record, packet)
    event_ids = [e["event_id"] for e in packet["events"]]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("duplicate event id")
    for event in packet["events"]:
        if event["op"] not in {"retract", "supersede"}:
            raise ValueError("unknown update operation")
        if event["issuer"] not in packet["sources"]:
            raise ValueError("unknown event issuer")
        if event["op"] == "supersede":
            _validate_record(event["replacement"], packet)
    claim_ids = [c["claim_id"] for c in packet["claims"]]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("duplicate claim id")
    for claim in packet["claims"]:
        if claim["kind"] not in KINDS or type(claim["value"]) is not bool:
            raise ValueError("invalid claim AST")
        if claim["proposition_id"] not in packet["propositions"]:
            raise ValueError("claim names an unknown proposition")
        if claim["kind"] != "current_support" and claim["source_owner"] not in packet["sources"]:
            raise ValueError("claim names an unknown source")
        if claim["kind"] == "historical_assertion" and not claim.get("record_id"):
            raise ValueError("historical assertion requires an exact record id")


def replay(packet):
    """Apply only owner-authorized, exact-target updates; retain immutable history."""
    validate_packet(packet)
    records = {r["record_id"]: copy.deepcopy(r) for r in packet["records"]}
    audit = []
    for event in packet["events"]:
        target = records.get(event["target_record_id"])
        reason = None
        if target is None:
            reason = "unknown_target"
        elif event["issuer"] != target["source_owner"]:
            reason = "issuer_does_not_own_target"
        elif target["status"] != "active":
            reason = "target_not_active"
        elif event["op"] == "supersede":
            replacement = event["replacement"]
            if replacement["record_id"] in records:
                reason = "replacement_id_already_exists"
            elif (replacement["source_owner"] != target["source_owner"]
                  or replacement["proposition_id"] != target["proposition_id"]
                  or replacement["status"] != "active"):
                reason = "replacement_changes_scope_or_is_inactive"
        if reason is None:
            target["status"] = "archive"
            if event["op"] == "supersede":
                records[event["replacement"]["record_id"]] = copy.deepcopy(event["replacement"])
        audit.append({"event_id": event["event_id"], "accepted": reason is None,
                      "reason": reason or "owner_authorized_exact_target"})
    for original in packet["records"]:
        retained = records[original["record_id"]]
        if any(retained[k] != original[k] for k in IMMUTABLE_FIELDS):
            raise AssertionError("update altered immutable historical assertion")
    return records, audit


def classify_claim(packet, records, claim):
    """Return evidence status for a hand-authored AST; never inspect private world truth."""
    candidates = [r for r in records.values()
                  if r["proposition_id"] == claim["proposition_id"]]
    if claim["kind"] == "historical_assertion":
        candidates = [r for r in candidates if r["record_id"] == claim["record_id"]
                      and r["source_owner"] == claim["source_owner"]]
    else:
        candidates = [r for r in candidates if r["status"] == "active"]
        if claim["kind"] == "current_endorsement":
            candidates = [r for r in candidates if r["source_owner"] == claim["source_owner"]]
        else:
            candidates = [r for r in candidates if claim["proposition_id"]
                          in packet["sources"][r["source_owner"]]["may_support"]]
    supporting = sorted(r["record_id"] for r in candidates if r["value"] == claim["value"])
    opposing = sorted(r["record_id"] for r in candidates if r["value"] != claim["value"])
    if supporting and opposing:
        status = "conflicted"
    elif supporting:
        status = "supported"
    elif opposing:
        status = "opposed"
    else:
        status = "unsupported"
    return {"claim_id": claim["claim_id"], "scope": claim["kind"], "status": status,
            "supporting_records": supporting, "opposing_records": opposing}


def audit_packet(packet):
    records, events = replay(packet)
    return {"packet_id": packet["packet_id"], "records": records, "events": events,
            "claims": [classify_claim(packet, records, c) for c in packet["claims"]]}


def public_packet(packet):
    """Export narrative claims without the private world or hand-authored claim AST."""
    def opaque_id(prefix, *parts):
        digest = hashlib.sha256(json.dumps(parts).encode()).hexdigest()[:16]
        return f"{prefix}-{digest}"

    return {
        "artifact_kind": "synthetic correction-scope prompt; no LLM evaluation",
        "packet_id": opaque_id("packet", packet["packet_id"]),
        "task": ("Audit each claim's scope and current evidence support. Distinguish a historical "
                 "assertion, current source endorsement, and current admissible support. "
                 "Do not infer world truth from missing support."),
        "propositions": packet["propositions"],
        "sources": copy.deepcopy(packet["sources"]),
        "records": copy.deepcopy(packet["records"]),
        "events": copy.deepcopy(packet["events"]),
        "claims": [{"claim_id": opaque_id("claim", packet["packet_id"], c["claim_id"]),
                    "text": c["text"]} for c in packet["claims"]],
    }


def load_packets(path=DEFAULT_SUITE):
    packets = json.loads(Path(path).read_text())["packets"]
    ids = [p["packet_id"] for p in packets]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate packet id")
    for packet in packets:
        validate_packet(packet)
    return packets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="print synthetic oracle invariant counts, not model scores")
    export = commands.add_parser("export", help="export public packets without gold claim AST")
    export.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packets = load_packets(args.suite)
    if args.command == "export":
        # Validate/replay first so malformed packets cannot be silently exported.
        for packet in packets:
            audit_packet(packet)
        with args.output.open("w") as stream:
            for packet in packets:
                stream.write(json.dumps(public_packet(packet), sort_keys=True) + "\n")
        print(f"Synthetic oracle/demo: exported {len(packets)} packets; no LLM evaluation.")
        return
    counts = Counter()
    for packet in packets:
        result = audit_packet(packet)
        counts["packets_validated"] += 1
        counts["historical_record_preservation_checks"] += len(packet["records"])
        counts["hand_authored_claim_asts_checked"] += len(result["claims"])
        counts["owner_authorized_updates"] += sum(e["accepted"] for e in result["events"])
        counts["rejected_updates"] += sum(not e["accepted"] for e in result["events"])
    print(json.dumps({"artifact_kind": "synthetic oracle/demo; no LLM evaluation",
                      "invariant_counts": dict(counts)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
