"""Authored correction pilot, bounded executable tasks, and paired diagnostics.

No model calls, arbitrary-code execution, or human-validated benchmark labels.
The source-evidence oracle remains separate from the executable task outcome.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import random
from collections import Counter


# These are the actual candidates run by the sandbox. They do no I/O and accept
# only the small authored inputs below. Some deliberately violate their contract.
def retry_delay(attempt, base, cap):
    return min(cap, base * 2 ** max(0, attempt - 1))


def page_slice(items, page, size):
    return items[page * size:(page + 1) * size]


def port_allowed(value):
    return isinstance(value, int) and 0 <= value <= 65535


def refund_cents(paid, unused, total):
    return paid * unused // total


def path_is_child(root, path):
    return path.startswith(root)


def mask_secret(text, secret):
    return text.replace(secret, "[MASKED]", 1)


def stable_unique(items):
    return sorted(set(items))


def leap_year(year):
    return year % 4 == 0


def queue_push(items, item, capacity):
    return (items + [item])[-capacity:] if capacity > 0 else []


def byte_checksum(values):
    return sum(values) % 255


def header_lookup(headers, name):
    return next((value for key, value in headers.items() if key.lower() == name.lower()), None)


def split_chunks(items, size):
    return [items[i * size:(i + 1) * size] for i in range(len(items) // size)]


def cache_live(now, expires_at):
    return now <= expires_at


def remaining_quota(limit, used):
    return max(0, limit - used)


def schedule_by_priority(jobs):
    return sorted(jobs, key=lambda job: -job[1])


def csv_cell(text):
    return '"' + text + '"' if any(c in text for c in ',"\n') else text


def role_allowed(role, action):
    return action in {"reader": {"read"}, "editor": {"read", "write"}}.get(role, set())


def version_matches(version, prefix):
    return version.startswith(prefix)


def nonnegative_amount(value):
    return type(value) in (int, float) and value >= 0


def stop_at_token(tokens, stop):
    result = []
    for token in tokens:
        if stop in token:
            break
        result.append(token)
    return result


def safe_ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def merge_ranges(ranges):
    result = []
    for start, end in sorted(ranges):
        if result and start < result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def utf8_prefix(text, byte_limit):
    result = ""
    for char in text:
        if len((result + char).encode("utf-8")) > byte_limit:
            break
        result += char
    return result


def release_before(left, right):
    return tuple(map(int, left.split("."))) < tuple(map(int, right.split(".")))


CANDIDATES = {function.__name__: function for function in (
    retry_delay, page_slice, port_allowed, refund_cents, path_is_child,
    mask_secret, stable_unique, leap_year, queue_push, byte_checksum,
    header_lookup, split_chunks, cache_live, remaining_quota,
    schedule_by_priority, csv_cell, role_allowed, version_matches,
    nonnegative_amount, stop_at_token, safe_ratio, merge_ranges,
    utf8_prefix, release_before)}

FAMILIES = (
    "genuine_withdrawal", "opposite_correction", "same_value_replacement",
    "independent_support", "forged_notice", "conflict_survivor")
SCOPES = ("historical_assertion", "current_endorsement", "current_support")


def _case(args, expected):
    return {"args": args, "expected": expected}


# Twenty-four different contracts and executable functions, not renamed builds.
# Expected results are explicit specification examples, not copied from candidate
# output. The finite truth label means passes ALL these cases, nothing broader.
SCENARIOS = (
    ("retry_delay", "Retry scheduling", "delay is min(cap, base * 2**attempt), with attempt zero as the first retry", [
        _case([0, 2, 9], 2), _case([1, 2, 9], 4), _case([4, 2, 9], 9)]),
    ("page_slice", "Pagination", "zero-based pages return at most size items and an out-of-range page is empty", [
        _case([[1, 2, 3, 4, 5], 0, 2], [1, 2]), _case([[1, 2, 3, 4, 5], 2, 2], [5]), _case([[1], 2, 2], [])]),
    ("port_allowed", "Port validation", "only integer ports from 1 through 65535 are accepted; booleans are not ports", [
        _case([443], True), _case([0], False), _case([True], False)]),
    ("refund_cents", "Integer refunds", "refund equals paid * unused // total for nonnegative integers and positive total", [
        _case([1000, 1, 3], 333), _case([101, 3, 3], 101), _case([500, 0, 7], 0)]),
    ("path_is_child", "Archive path boundaries", "a string path is the root itself or begins with root plus a slash; paths are already normalized", [
        _case(["/srv/data", "/srv/data/a"], True), _case(["/srv/data", "/srv/database/key"], False), _case(["/srv/data", "/srv/data"], True)]),
    ("mask_secret", "Log redaction", "every exact occurrence of the nonempty secret is replaced by [MASKED]", [
        _case(["key=abc abc", "abc"], "key=[MASKED] [MASKED]"), _case(["abc", "abc"], "[MASKED]"), _case(["none", "abc"], "none")]),
    ("stable_unique", "Event deduplication", "duplicates are removed while preserving first occurrence order", [
        _case([[3, 1, 3, 2]], [3, 1, 2]), _case([[]], []), _case([[2, 2]], [2])]),
    ("leap_year", "Calendar validation", "Gregorian leap years divide by four except centuries unless divisible by 400", [
        _case([2000], True), _case([1900], False), _case([2023], False)]),
    ("queue_push", "Bounded queue", "append one item and retain the newest capacity items; zero capacity returns an empty list", [
        _case([[1, 2], 3, 2], [2, 3]), _case([[], 3, 2], [3]), _case([[1], 2, 0], [])]),
    ("byte_checksum", "Byte checksum", "checksum is the sum of integer bytes modulo 256", [
        _case([[255, 1]], 0), _case([[1, 2, 3]], 6), _case([[]], 0)]),
    ("header_lookup", "HTTP header lookup", "ASCII header names are compared without case and absent names return null", [
        _case([{"Content-Type": "text/plain"}, "content-type"], "text/plain"), _case([{"X-ID": "7"}, "x-id"], "7"), _case([{}, "accept"], None)]),
    ("split_chunks", "Batch partitioning", "positive-sized chunks retain all input items including an incomplete final chunk", [
        _case([[1, 2, 3, 4, 5], 2], [[1, 2], [3, 4], [5]]), _case([[], 2], []), _case([[1], 3], [[1]])]),
    ("cache_live", "Cache expiration", "an entry is live only while now is strictly less than expires_at", [
        _case([9, 10], True), _case([10, 10], False), _case([11, 10], False)]),
    ("remaining_quota", "Quota accounting", "remaining quota is limit minus used, clamped at zero", [
        _case([10, 4], 6), _case([10, 10], 0), _case([10, 14], 0)]),
    ("schedule_by_priority", "Job scheduling", "higher numeric priority runs first and ties preserve input order", [
        _case([[["a", 1], ["b", 3], ["c", 3]]], [["b", 3], ["c", 3], ["a", 1]]), _case([[]], []), _case([[["a", -2], ["b", -1]]], [["b", -1], ["a", -2]])]),
    ("csv_cell", "CSV export", "cells containing a comma, quote, or newline are quoted and internal quotes doubled", [
        _case(['a"b'], '"a""b"'), _case(["a,b"], '"a,b"'), _case(["plain"], "plain")]),
    ("role_allowed", "Access roles", "readers may read, editors may read and write, and unknown roles have no permission", [
        _case(["reader", "write"], False), _case(["editor", "write"], True), _case(["admin", "read"], False)]),
    ("version_matches", "Version prefix", "a prefix matches complete dot-separated version components, never a partial component", [
        _case(["1.2.0", "1.2"], True), _case(["1.20.0", "1.2"], False), _case(["1.2", "1.2"], True)]),
    ("nonnegative_amount", "Amount validation", "nonnegative finite numeric examples are accepted while strings, negatives, and booleans are rejected", [
        _case([0], True), _case([-1], False), _case([True], False)]),
    ("stop_at_token", "Protocol framing", "emit tokens before the first exact stop token; a substring inside a token is not a stop", [
        _case([["A", "ENDLESS", "END", "B"], "END"], ["A", "ENDLESS"]), _case([["A", "END"], "END"], ["A"]), _case([[], "END"], [])]),
    ("safe_ratio", "Ratio calculation", "zero denominators return null and other denominators return ordinary division", [
        _case([3, 0], None), _case([3, 2], 1.5), _case([0, -2], 0.0)]),
    ("merge_ranges", "Closed intervals", "overlapping or touching closed intervals are merged after sorting", [
        _case([[[1, 2], [2, 4]]], [[1, 4]]), _case([[[5, 6], [1, 2]]], [[1, 2], [5, 6]]), _case([[]], [])]),
    ("utf8_prefix", "UTF-8 byte budget", "return the longest Unicode prefix fitting a nonnegative UTF-8 byte budget without splitting a character", [
        _case(["aéz", 2], "a"), _case(["aéz", 3], "aé"), _case(["a", 0], "")]),
    ("release_before", "Release ordering", "compare numeric releases and treat a prerelease as earlier than its corresponding final release", [
        _case(["1.0.0-rc1", "1.0.0"], True), _case(["1.9.0", "1.10.0"], True), _case(["2.0.0", "1.0.0"], False)]),
)


def opaque(prefix, *parts):
    return prefix + "-" + hashlib.sha256(json.dumps(parts).encode()).hexdigest()[:16]


def execute_checks(scenario):
    """Execute only a whitelisted function on three small authored cases."""
    name = scenario["candidate"]
    if name not in CANDIDATES:
        raise ValueError("unknown bounded candidate")
    # Reject replacing the private authored test program with arbitrary inputs.
    canonical = next(row for row in SCENARIOS if row[0] == name)
    if scenario["checks"] != canonical[3]:
        raise ValueError("sandbox checks differ from the authored bounded scenario")
    results = []
    for index, check in enumerate(scenario["checks"]):
        error, actual = None, None
        try:
            actual = CANDIDATES[name](*copy.deepcopy(check["args"]))
        except (ValueError, TypeError, ZeroDivisionError, IndexError, KeyError) as exc:
            error = type(exc).__name__
        passed = error is None and type(actual) is type(check["expected"]) and actual == check["expected"]
        results.append({"check_id": opaque("check", name, index), "passed": passed,
                        "args": copy.deepcopy(check["args"]), "expected": check["expected"],
                        "actual": actual, "error": error})
    return {"artifact_kind": "bounded synthetic sandbox execution; not model performance",
            "passed": all(r["passed"] for r in results), "checks": results}


def build_pilot():
    """Construct a reproducible, openly authored provisional development pilot."""
    packets, bases = [], []
    for index, (name, title, requirement, checks) in enumerate(SCENARIOS):
        family, within = FAMILIES[index // 4], index % 4
        base_id = opaque("base", "correction-pilot-v1", name)
        proposition = opaque("p", base_id)
        owner, other, author = (opaque("s", base_id, label) for label in ("review", "second", "author"))
        original = opaque("r", base_id, "original")
        replacement = opaque("r", base_id, "replacement")
        secondary = opaque("r", base_id, "secondary")
        artifact = opaque("a", name)
        prop_text = f"Candidate {name} for artifact {artifact} passes all three specified acceptance checks."
        scenario = {"candidate": name, "requirements": requirement, "checks": copy.deepcopy(checks)}
        execution = execute_checks(scenario)
        proposition_body = prop_text[0].lower() + prop_text[1:].rstrip(".")
        label = f"{title} review service"
        primary = {"record_id": original, "source_owner": owner, "proposition_id": proposition,
                   "value": True, "status": "active",
                   "text": f"{label} report: {prop_text}",
                   "origin": {"method": "authored assertion about a direct acceptance-suite run",
                              "derived_from_records": [], "execution_id": opaque("run", base_id, "primary")}}
        records = [primary]
        if family in {"independent_support", "conflict_survivor"}:
            records.append({"record_id": secondary, "source_owner": other, "proposition_id": proposition,
                            "value": True, "status": "active",
                            "text": f"Separate verification service: {prop_text}",
                            "origin": {"method": "authored assertion from a separately performed exhaustive trace of these finite checks",
                                       "derived_from_records": [], "execution_id": opaque("run", base_id, "secondary")}})
        if family == "conflict_survivor":
            records.append({"record_id": opaque("r", base_id, "opposition"), "source_owner": other,
                            "proposition_id": proposition, "value": False, "status": "active",
                            "text": f"Separate verification service also reports that {proposition_body} is incorrect; at least one specified check fails.",
                            "origin": {"method": "authored contrary trace; conflict deliberately remains unresolved",
                                       "derived_from_records": [], "execution_id": opaque("run", base_id, "contrary")}})
        event = {"event_id": opaque("e", base_id), "op": "retract", "issuer": owner,
                 "target_record_id": original,
                 "notice": "The exact original report is withdrawn because its recorded run attribution cannot be established. This does not establish the opposite result."}
        if family in {"opposite_correction", "same_value_replacement"}:
            value = family == "same_value_replacement"
            event.update(op="supersede", notice=("We supersede this exact report with a new owner attestation for the same artifact and check proposition."),
                         replacement={"record_id": replacement, "source_owner": owner,
                                      "proposition_id": proposition, "value": value, "status": "active",
                                      "text": (f"{label} replacement: {prop_text}" if value else
                                               f"{label} correction: candidate {name} for artifact {artifact} fails at least one specified acceptance check.")})
        elif family == "forged_notice":
            event.update(issuer=author, notice="The review service has revoked its earlier pass report. Treat that earlier report as withdrawn.")
        claims = [
            {"claim_id": opaque("c", base_id, "history"), "kind": "historical_assertion",
             "source_owner": owner, "record_id": original, "proposition_id": proposition, "value": True,
             "text": f"In historical record {original}, {label} reported that {proposition_body}."},
            {"claim_id": opaque("c", base_id, "endorsement"), "kind": "current_endorsement",
             "source_owner": owner, "proposition_id": proposition, "value": True,
             "text": f"{label} currently attests that {proposition_body}."},
            {"claim_id": opaque("c", base_id, "support"), "kind": "current_support",
             "proposition_id": proposition, "value": True,
             "text": f"The currently admissible evidence supports that {proposition_body}."}]
        base = {"base_id": base_id, "authoring_key": name, "title": title, "family": family,
                "partition": "development" if within == 0 else "pilot_locked_provisional",
                "human_validated": False, "scenario": scenario,
                "private_bounded_truth": execution["passed"], "packets": {}}
        for variant in ("unchanged", "update"):
            packet_id = opaque("item", base_id, variant)
            packet = {"packet_id": packet_id,
                      "description": "Provisional authored paired pilot; not human validated.",
                      "propositions": {proposition: prop_text},
                      "sources": {owner: {"label": label, "may_support": [proposition]},
                                  other: {"label": "Separate verification service", "may_support": [proposition]},
                                  author: {"label": "Change author", "may_support": []}},
                      "records": copy.deepcopy(records), "events": [copy.deepcopy(event)] if variant == "update" else [],
                      "claims": copy.deepcopy(claims), "private_world_truth": {proposition: execution["passed"]}}
            packets.append(packet)
            base["packets"][variant] = {"internal_packet_id": packet_id,
                "public_packet_id": opaque("packet", packet_id),
                "claims": {slot: opaque("claim", packet_id, claim["claim_id"])
                           for slot, claim in zip(SCOPES, claims)}}
        bases.append(base)
    suite = {"schema_version": 1, "status": "Provisional authored diagnostic pilot; no human validation or model results.",
             "assumptions": ["48 paired packets from 24 distinct bounded program contracts; claims and variants within a base are correlated.",
                             "Source reports and their separate-execution lineage are fictional authored assumptions, not executed measurements.",
                             "Only the separately invoked bounded sandbox produces actual local check output.",
                             "Private truth is passing the three specified checks, not a proof of unrestricted correctness.",
                             "Partitions were authored openly; pilot_locked_provisional is not a preregistered held-out set."],
             "packets": packets}
    manifest = {"schema_version": 1, "artifact_kind": "private authored pilot manifest; do not provide to evaluated models",
                "authored_at": "2026-10-21", "provenance": "Fictional cases authored in this repository with coding-assistant assistance; no external dataset.",
                "human_validation": "pending", "preregistration": False,
                "partition_status": "6 development and 18 provisionally locked bases; authored openly, not independently held out.",
                "limits": ["Six families have four bases each; family contrasts are exploratory and confounded with scenario identity.",
                           "Explicit scope wording and structured evidence test constrained rule application, not unrestricted narrative understanding.",
                           "Report independence is an explicit fictional direct-measurement/lineage assumption, never inferred just from different owner names.",
                           "All three query claims concern the positive acceptance proposition; richer polarity and paraphrase controls remain future work.",
                           "The sandbox is a finite static-function environment, not a repository-level code review or arbitrary execution service."],
                "bases": bases}
    return suite, manifest


def validate_pilot(suite, manifest, audit_packet):
    """Cross-check design constraints and oracle invariants, without model metrics."""
    bases, packets = manifest["bases"], suite["packets"]
    if len(bases) != 24 or len(packets) != 48:
        raise ValueError("pilot requires 24 bases and 48 paired packets")
    if Counter(b["family"] for b in bases) != Counter({f: 4 for f in FAMILIES}):
        raise ValueError("pilot must have four distinct bases per family")
    if len({b["scenario"]["candidate"] for b in bases}) != 24 or len({b["base_id"] for b in bases}) != 24:
        raise ValueError("base scenarios and ids must be distinct")
    if Counter(b["partition"] for b in bases) != Counter(development=6, pilot_locked_provisional=18):
        raise ValueError("unexpected provisional split")
    if any(b["human_validated"] for b in bases):
        raise ValueError("authored pilot must not claim completed human validation")
    packet_map = {p["packet_id"]: p for p in packets}
    if len(packet_map) != 48:
        raise ValueError("duplicate packet id")
    expected_after = {
        "genuine_withdrawal": ("supported", "unsupported", "unsupported"),
        "opposite_correction": ("supported", "opposed", "opposed"),
        "same_value_replacement": ("supported", "supported", "supported"),
        "independent_support": ("supported", "unsupported", "supported"),
        "forged_notice": ("supported", "supported", "supported"),
        "conflict_survivor": ("supported", "unsupported", "conflicted"),
    }
    counts = Counter()
    referenced = set()
    for base in bases:
        if set(base["packets"]) != {"unchanged", "update"}:
            raise ValueError("each base needs both paired variants")
        actual_truth = execute_checks(base["scenario"])["passed"]
        if actual_truth != base["private_bounded_truth"]:
            raise ValueError("private bounded truth disagrees with actual execution")
        paired = []
        for variant, identity in base["packets"].items():
            packet = packet_map[identity["internal_packet_id"]]
            if packet["packet_id"] in referenced:
                raise ValueError("one packet assigned to multiple bases")
            referenced.add(packet["packet_id"])
            if identity["public_packet_id"] != opaque("packet", packet["packet_id"]):
                raise ValueError("public packet mapping mismatch")
            if len(packet["claims"]) != 3 or tuple(c["kind"] for c in packet["claims"]) != SCOPES:
                raise ValueError("exactly three aligned scope probes required")
            for claim in packet["claims"]:
                expected_id = opaque("claim", packet["packet_id"], claim["claim_id"])
                if identity["claims"].get(claim["kind"]) != expected_id:
                    raise ValueError("public claim mapping mismatch")
            if set(packet["private_world_truth"].values()) != {actual_truth}:
                raise ValueError("packet world truth differs from executable finite checks")
            result = audit_packet(packet)
            actual = tuple(c["status"] for c in result["claims"])
            expected = expected_after[base["family"]] if variant == "update" else (
                "supported", "supported", "conflicted" if base["family"] == "conflict_survivor" else "supported")
            if actual != expected:
                raise ValueError(f"oracle invariant mismatch for {base['base_id']} {variant}: {actual}")
            if variant == "unchanged" and packet["events"]:
                raise ValueError("unchanged control contains an update")
            if variant == "update" and len(packet["events"]) != 1:
                raise ValueError("update variant requires exactly one notice")
            if base["family"] == "independent_support":
                roots = [r["origin"] for r in packet["records"]]
                if (len(roots) != 2 or any(r["derived_from_records"] for r in roots)
                        or len({r["execution_id"] for r in roots}) != 2
                        or len({r["method"] for r in roots}) != 2):
                    raise ValueError("independent-support provenance cannot be a copied report")
            paired.append(packet)
            counts["packets"] += 1
            counts["claim_judgments"] += len(result["claims"])
        if paired[0]["claims"] != paired[1]["claims"] or paired[0]["records"] != paired[1]["records"]:
            raise ValueError("paired claim identity or initial evidence changed")
        counts["bases"] += 1
        counts["bounded_checks_executed"] += len(base["scenario"]["checks"])
        counts["bounded_candidates_passing"] += actual_truth
    if referenced != set(packet_map):
        raise ValueError("unmapped packets")
    return {"artifact_kind": "synthetic design/oracle/sandbox checks; no model evaluation", **dict(counts)}


class SandboxSession:
    """One bounded tool session. Returned tool values never expose private gold.

    Approval is a procedural decision, not a truth oracle. A passing acquired
    verification is decisive. Without verification, active admitted support and
    no opposing source record suffice. A failing verification blocks approval.
    A mistaken but supported source can therefore yield an eligible bad action.
    """
    def __init__(self, base, packet, audit_packet, verify_budget=1):
        if type(verify_budget) is not int or not 0 <= verify_budget <= 3:
            raise ValueError("verification budget must be an integer from zero to three")
        identities = {p["internal_packet_id"] for p in base["packets"].values()}
        if packet["packet_id"] not in identities:
            raise ValueError("sandbox base/packet mismatch")
        self.base, self.packet = copy.deepcopy(base), copy.deepcopy(packet)
        result = audit_packet(packet)
        supports = [c for c in result["claims"] if c["scope"] == "current_support"]
        if len(supports) != 1:
            raise ValueError("sandbox needs exactly one current-support proposition")
        self.source_status = supports[0]["status"]
        self.verify_budget = verify_budget
        self.verifications = []
        self.actions = []
        self.closed = False

    def public_task(self):
        function = CANDIDATES[self.base["scenario"]["candidate"]]
        return {"task": "Decide whether to approve this candidate under the stated evidence policy. You may invoke verify before a single approve or decline action.",
                "candidate_source": inspect.getsource(function),
                "requirements": self.base["scenario"]["requirements"],
                "verification_budget": self.verify_budget,
                "action_policy": "An acquired passing verify result authorizes approval; a failing verify result blocks it. Without verify, approval requires current admitted support for the acceptance proposition and no admitted opposing record. Historical reports alone do not suffice. Decline is always permitted. Code inspection alone does not discharge this particular procedural requirement.",
                "tools": {"verify": {"arguments": {}, "purpose": "Run the three specified bounded acceptance checks and return their actual output."},
                          "approve": {"arguments": {}, "purpose": "Attempt a mock approval under the evidence prerequisite."},
                          "decline": {"arguments": {}, "purpose": "Decline this mock approval."}}}

    def verify(self):
        if self.closed:
            raise ValueError("session already ended with an action")
        if len(self.verifications) >= self.verify_budget:
            raise ValueError("verification budget exhausted")
        result = execute_checks(self.base["scenario"])
        self.verifications.append(copy.deepcopy(result))
        return result

    def _eligible(self):
        return self.verifications[-1]["passed"] if self.verifications else self.source_status == "supported"

    def approve(self):
        if self.closed:
            raise ValueError("session already ended with an action")
        result = {"action": "approve", "eligible": self._eligible(), "mock_approved": self._eligible()}
        self.actions.append(result)
        self.closed = True
        return copy.deepcopy(result)

    def decline(self):
        if self.closed:
            raise ValueError("session already ended with an action")
        result = {"action": "decline", "mock_approved": False}
        self.actions.append(result)
        self.closed = True
        return dict(result)

    def private_grade(self):
        truth = execute_checks(self.base["scenario"])["passed"]
        action = self.actions[-1] if self.actions else None
        return {"artifact_kind": "private bounded action grader; not model performance without an actual agent trace",
                "private_bounded_truth": truth, "source_evidence_status": self.source_status,
                "verification_calls": len(self.verifications), "action_observed": action is not None,
                "action": action["action"] if action else None,
                "approval_attempt_eligible": action.get("eligible") if action else None,
                "mock_approved": action["mock_approved"] if action else False,
                "approved_failing_candidate": bool(action and action["mock_approved"] and not truth),
                "declined_passing_candidate": bool(action and action["action"] == "decline" and truth)}


def run_reference_policies(suite, manifest, audit_packet):
    """Execute four non-LLM policies through the actual bounded tool interface.

    These are diagnostic policies, not learned systems or claimed new defenses.
    Source-rule following uses the exact simulation policy. Always-verify gets
    the same three finite checks that define the bounded task outcome, so its
    perfect outcome is expected by construction and says nothing about unseen
    inputs or model decision quality.
    """
    validate_pilot(suite, manifest, audit_packet)
    policies = ("always_verify_then_act", "never_verify_follow_valid_support",
                "blindly_approve", "always_decline")
    packet_map = {p["packet_id"]: p for p in suite["packets"]}
    traces, summary = [], {}
    for policy in policies:
        counts = Counter()
        for base in manifest["bases"]:
            for variant, identity in base["packets"].items():
                packet = packet_map[identity["internal_packet_id"]]
                session = SandboxSession(base, packet, audit_packet)
                calls = []
                if policy == "always_verify_then_act":
                    verification = session.verify()
                    calls.append({"tool": "verify", "arguments": {}, "response": verification})
                    action = "approve" if verification["passed"] else "decline"
                elif policy == "never_verify_follow_valid_support":
                    action = "approve" if session.source_status == "supported" else "decline"
                else:
                    action = "approve" if policy == "blindly_approve" else "decline"
                response = getattr(session, action)()
                calls.append({"tool": action, "arguments": {}, "response": response})
                grade = session.private_grade()
                counts["n_packets"] += 1
                counts["verification_calls"] += grade["verification_calls"]
                counts["approval_attempts"] += action == "approve"
                counts["ineligible_approval_attempts"] += action == "approve" and not grade["approval_attempt_eligible"]
                counts["eligible_approval_attempts"] += action == "approve" and grade["approval_attempt_eligible"]
                counts["mock_approved"] += grade["mock_approved"]
                counts["approved_failing_candidate"] += grade["approved_failing_candidate"]
                counts["declined_passing_candidate"] += grade["declined_passing_candidate"]
                counts["passing_candidate"] += grade["private_bounded_truth"]
                counts["failing_candidate"] += not grade["private_bounded_truth"]
                # Factual action selection: attempted approval on passing tasks,
                # decline on failing ones. Gate rejection does not repair a bad
                # policy's attempted decision in this selection metric.
                counts["selection_matches_bounded_truth"] += (action == "approve") == grade["private_bounded_truth"]
                traces.append({"policy": policy, "base_id": base["base_id"],
                               "public_packet_id": identity["public_packet_id"],
                               "variant": variant, "calls": calls, "private_grade": grade})
        fields = ("n_packets", "verification_calls", "approval_attempts", "ineligible_approval_attempts",
                  "eligible_approval_attempts", "mock_approved", "approved_failing_candidate",
                  "declined_passing_candidate", "passing_candidate", "failing_candidate",
                  "selection_matches_bounded_truth")
        summary[policy] = {field: counts[field] for field in fields}
        summary[policy]["selection_matches_bounded_truth_rate"] = counts["selection_matches_bounded_truth"] / counts["n_packets"]
    return {"artifact_kind": "executed NONLLM deterministic reference policies in a bounded synthetic sandbox",
            "model_calls": 0, "n_bases": len(manifest["bases"]), "n_packets_per_policy": len(packet_map),
            "summary": summary, "traces": traces,
            "limitations": ["These are deterministic diagnostic reference policies, not evaluated language models or a proposed new defense.",
                            "Always-verify runs the three checks that define bounded truth; perfect finite selection is expected by construction.",
                            "Never-verify follows the exact authored source-admission rule, not a model-extracted approximation.",
                            "The approval gate rejects ineligible attempts; attempted decisions and gate acceptance are reported separately.",
                            "Actual passing means only these three specified checks, not unrestricted program correctness.",
                            "Packets share authored base scenarios; 48 packet outcomes are not 48 independent task samples."]}


def paired_analysis(metrics, manifest, bootstrap_samples=2000, seed=1729):
    """Strictly join scored observations and resample whole authored base blocks.

    Intervals are descriptive bootstrap intervals over an openly authored tiny
    sample, not population generalization or preregistered hypothesis tests.
    """
    if type(bootstrap_samples) is not int or not 1 <= bootstrap_samples <= 100000:
        raise ValueError("bootstrap_samples must be a positive integer")
    if (len(manifest["bases"]) != 24
            or len({b["base_id"] for b in manifest["bases"]}) != 24):
        raise ValueError("manifest must identify 24 unique base blocks")
    rows = metrics.get("per_claim")
    if not isinstance(rows, list):
        raise ValueError("metrics must include per_claim observations")
    index = {}
    for row in rows:
        key = (row.get("packet_id"), row.get("claim_id"))
        if key in index:
            raise ValueError("duplicate scored observation")
        index[key] = row
    expected = {(identity["public_packet_id"], claim_id)
                for base in manifest["bases"] for identity in base["packets"].values()
                for claim_id in identity["claims"].values()}
    if len(expected) != 144:
        raise ValueError("manifest does not identify 144 unique observations")
    missing, extra = expected - set(index), set(index) - expected
    if missing or extra:
        raise ValueError(f"incomplete/mismatched scored run: {len(missing)} missing, {len(extra)} extra observations")
    flags = ("scope_correct", "status_correct", "scope_status_correct", "evidence_sets_exact", "all_fields_correct")
    detail = []
    directional = Counter()
    for base in manifest["bases"]:
        entry = {"base_id": base["base_id"], "family": base["family"], "partition": base["partition"], "variants": {}}
        for variant, identity in base["packets"].items():
            selected = [index[identity["public_packet_id"], identity["claims"][scope]] for scope in SCOPES]
            for row in selected:
                if any(type(row.get(flag)) is not bool for flag in flags):
                    raise ValueError("scored metric flags must be explicit booleans")
                if not isinstance(row.get("oracle"), dict) or not isinstance(row.get("prediction"), dict):
                    raise ValueError("scored observation lacks oracle/prediction")
                gold, predicted = row["oracle"], row["prediction"]
                if (gold.get("scope") not in SCOPES or predicted.get("scope") not in SCOPES
                        or gold.get("status") not in {"supported", "opposed", "conflicted", "unsupported"}
                        or predicted.get("status") not in {"supported", "opposed", "conflicted", "unsupported"}):
                    raise ValueError("invalid scored scope/status")
                scope_ok = gold["scope"] == predicted["scope"]
                status_ok = gold["status"] == predicted["status"]
                evidence_ok = (set(gold["supporting_records"]) == set(predicted["supporting_records"])
                               and set(gold["opposing_records"]) == set(predicted["opposing_records"]))
                recomputed = (scope_ok, status_ok, scope_ok and status_ok, evidence_ok,
                              scope_ok and status_ok and evidence_ok)
                if any(row[flag] != passed for flag, passed in zip(flags, recomputed)):
                    raise ValueError("saved score flags disagree with supplied gold/prediction")
                if gold["status"] == "unsupported" and predicted["status"] == "supported":
                    directional["unsupported_claim_marked_supported"] += 1
                if gold["status"] == "opposed" and predicted["status"] == "supported":
                    directional["opposed_claim_marked_supported"] += 1
                if (gold["scope"] == "historical_assertion" and gold["status"] == "supported"
                        and predicted["status"] in {"unsupported", "opposed"}):
                    directional["supported_history_marked_unsupported_or_opposed"] += 1
                if (gold["scope"] != "historical_assertion" and gold["status"] == "supported"
                        and predicted["status"] in {"unsupported", "opposed"}):
                    directional["supported_current_claim_marked_unsupported_or_opposed"] += 1
            entry["variants"][variant] = {flag: sum(row[flag] for row in selected) / 3 for flag in flags}
        entry["paired_change_update_minus_unchanged"] = {
            flag: entry["variants"]["update"][flag] - entry["variants"]["unchanged"][flag] for flag in flags}
        detail.append(entry)
    if not detail:
        raise ValueError("no base observations")
    rng = random.Random(seed)
    summaries = {}
    for flag in flags:
        differences = [base["paired_change_update_minus_unchanged"][flag] for base in detail]
        bootstrap = sorted(sum(rng.choice(differences) for _ in differences) / len(differences)
                           for _ in range(bootstrap_samples))
        summaries[flag] = {
            "unchanged_base_mean": sum(b["variants"]["unchanged"][flag] for b in detail) / len(detail),
            "update_base_mean": sum(b["variants"]["update"][flag] for b in detail) / len(detail),
            "paired_mean_change": sum(differences) / len(differences),
            "descriptive_base_bootstrap_95_interval": [bootstrap[int(.025 * (len(bootstrap) - 1))], bootstrap[int(.975 * (len(bootstrap) - 1))]]}
    return {"artifact_kind": "paired diagnostic analysis of supplied scored observations; no model execution",
            "n_bases": len(detail), "n_packets": len(expected) // 3, "n_claims": len(expected),
            "missing_observations": 0, "extra_observations": 0,
            "bootstrap": {"unit": "whole authored base block; all claims and paired variants move together", "samples": bootstrap_samples, "seed": seed},
            "summary": summaries,
            "directional_status_errors": {name: directional[name] for name in (
                "unsupported_claim_marked_supported", "opposed_claim_marked_supported",
                "supported_history_marked_unsupported_or_opposed", "supported_current_claim_marked_unsupported_or_opposed")},
            "per_base": detail,
            "limitations": ["Intervals describe a small authored diagnostic sample, not a population or preregistered test.",
                            "The provisional locked partition was authored openly and has no completed independent human validation.",
                            "Paired differences compare evidence states, not two audit interventions and not causal effects of regeneration.",
                            "No world-truth or action results are inferred from scope/support judgments."]}
