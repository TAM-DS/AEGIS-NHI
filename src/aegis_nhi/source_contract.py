"""Bounded offline contract for explicitly linked synthetic observations.

Source IDs must be allowed independently by the caller. Evidence hashes are
declared provenance, not authenticated proof. Nothing here grants authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

MAX_RECORDS = 1000
MAX_LINKS = 1000
MAX_BYTES = 1048576


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError("Missing or unexpected contract fields")


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ValueError("Invalid scoped identifier")
    return value


def _reference(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("Record reference requires source and record ID")
    return tuple(_identifier(part) for part in value)


def build_source_report(bundle, *, allowed_sources):
    """Validate the entire bundle before returning any report.

    Explicit links mean two sources report the same event; source-local identity
    and resource IDs remain distinct. No timestamp/name-based joins are inferred.
    """
    _fields(bundle, "schema_version synthetic records links")
    if type(bundle["schema_version"]) is not int or bundle["schema_version"] != 1:
        raise ValueError("Unsupported schema version")
    if bundle["synthetic"] is not True:
        raise ValueError("Only synthetic observations are supported")
    if not isinstance(allowed_sources, (list, tuple, set, frozenset)) or not allowed_sources:
        raise ValueError("An independent source allowlist is required")
    sources = {_identifier(item) for item in allowed_sources}
    records, links = bundle["records"], bundle["links"]
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError("Record count outside bounds")
    if not isinstance(links, list) or len(links) > MAX_LINKS:
        raise ValueError("Link count outside bounds")
    if len(_canonical(bundle).encode()) > MAX_BYTES:
        raise ValueError("Bundle exceeds size limit")
    indexed, evidence = {}, set()
    for record in records:
        _fields(record, "source_id record_id institution_id case_id identity_id resource_id action outcome evidence")
        for field in ("source_id", "record_id", "institution_id", "case_id", "identity_id", "resource_id", "action"):
            _identifier(record[field])
        key = (record["source_id"], record["record_id"])
        if key[0] not in sources:
            raise ValueError("Source is not allowlisted")
        if key in indexed:
            raise ValueError("Duplicate source record")
        if record["outcome"] not in ("executed", "blocked"):
            raise ValueError("Unknown observed outcome")
        if not isinstance(record["evidence"], list) or not 1 <= len(record["evidence"]) <= 20:
            raise ValueError("Evidence count outside bounds")
        for item in record["evidence"]:
            _fields(item, "evidence_id sha256")
            eid = _identifier(item["evidence_id"])
            if not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                raise ValueError("Invalid evidence digest")
            evidence_key = (*key, eid)
            if evidence_key in evidence:
                raise ValueError("Duplicate record evidence")
            evidence.add(evidence_key)
        indexed[key] = record
    accepted, seen = [], set()
    for link in links:
        _fields(link, "left right relation basis_evidence")
        left, right = _reference(link["left"]), _reference(link["right"])
        if left not in indexed or right not in indexed:
            raise ValueError("Link references unknown record")
        if left[0] == right[0] or link["relation"] != "SAME_REPORTED_EVENT":
            raise ValueError("Only explicit cross-source event links are supported")
        pair = tuple(sorted((left, right)))
        if pair in seen:
            raise ValueError("Duplicate event link")
        seen.add(pair)
        a, b = indexed[left], indexed[right]
        if (a["institution_id"], a["case_id"]) != (b["institution_id"], b["case_id"]):
            raise ValueError("Cross-institution or cross-case link denied")
        if (a["action"], a["outcome"]) != (b["action"], b["outcome"]):
            raise ValueError("Conflicting event observations")
        basis = link["basis_evidence"]
        if not isinstance(basis, list) or not 2 <= len(basis) <= 40:
            raise ValueError("Link requires evidence from both records")
        refs = set()
        for ref in basis:
            if not isinstance(ref, list) or len(ref) != 3:
                raise ValueError("Evidence reference requires source, record and evidence ID")
            ref = tuple(_identifier(part) for part in ref)
            if ref not in evidence or ref[:2] not in (left, right):
                raise ValueError("Unrelated or missing link evidence")
            if ref in refs:
                raise ValueError("Duplicate link evidence")
            refs.add(ref)
        if {ref[:2] for ref in refs} != {left, right}:
            raise ValueError("Link requires evidence from both records")
        accepted.append({"left": list(pair[0]), "right": list(pair[1]),
                         "relation": link["relation"], "basis_evidence": sorted(map(list, refs))})
    observations = []
    for key, record in sorted(indexed.items()):
        normalized = dict(record)
        normalized["evidence"] = sorted(record["evidence"], key=lambda item: item["evidence_id"])
        observations.append(normalized)
    result = {
        "schema_version": 1, "synthetic": True,
        "approval_status": "NOT_AUTHORIZED_FOR_ACTION",
        "provenance_status": "DECLARED_NOT_AUTHENTICATED",
        "source_allowlist": sorted(sources),
        "observations": observations,
        "links": sorted(accepted, key=_canonical),
        "counts": {"records": len(records), "explicit_links": len(accepted)},
    }
    result["report_sha256"] = _digest(result)
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate synthetic cross-source evidence")
    parser.add_argument("bundle")
    parser.add_argument("--source", action="append", required=True, help="Independently allowed source ID")
    args = parser.parse_args()
    try:
        with Path(args.bundle).open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Bundle exceeds size limit")
        bundle = json.loads(raw, object_pairs_hook=_unique_object)
        report = build_source_report(bundle, allowed_sources=args.source)
    except (ValueError, TypeError, OSError, UnicodeError):
        print(json.dumps({"status": "rejected", "reason": "Source contract validation failed"}))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
