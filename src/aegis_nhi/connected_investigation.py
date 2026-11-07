"""Explicit synthetic session/host attachments to a source-verified case graph."""
from __future__ import annotations

import hashlib
import json

from .authorization import parse_timestamp
from .cyber_graph import build_case_graph
from .source_contract import build_source_report, _fields, _identifier
from .workflow import run_case


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def adapt_case_events(case):
    """Normalize existing event evidence; do not invent cross-source links."""
    build_case_graph(case)
    _identifier(case["case_id"])
    evidence = {item["evidence_id"]: item for item in case["evidence"]}
    records = []
    for event in case["events"]:
        records.append({
            "source_id": "aegis-nhi-case", "record_id": event["event_id"],
            "institution_id": "case-" + digest(case["institution"])[:24],
            "case_id": case["case_id"], "identity_id": event["identity_id"],
            "resource_id": event["resource_id"], "action": event["requested_action"],
            "outcome": event["observed_outcome"],
            "evidence": [{"evidence_id": eid, "sha256": digest(evidence[eid])}
                         for eid in event["evidence_ids"]],
        })
    return build_source_report(
        {"schema_version": 1, "synthetic": True, "records": records, "links": []},
        allowed_sources=["aegis-nhi-case"],
    )


def build_connected_investigation(case, telemetry):
    """All-or-nothing projection; links express fixture declarations, not causality."""
    normalized = adapt_case_events(case)
    graph = build_case_graph(case)
    _fields(telemetry, "schema_version synthetic source_id case_id institution case_sha256 sessions hosts")
    if type(telemetry["schema_version"]) is not int or telemetry["schema_version"] != 1:
        raise ValueError("Unsupported telemetry schema")
    if telemetry["synthetic"] is not True or telemetry["source_id"] != "fictional-session-host":
        raise ValueError("Only the declared fictional telemetry source is accepted")
    if (telemetry["case_id"], telemetry["institution"], telemetry["case_sha256"]) != (
        case["case_id"], case["institution"], digest(case)
    ):
        raise ValueError("Telemetry source case or institution mismatch")
    for name in ("sessions", "hosts"):
        if not isinstance(telemetry[name], list) or not 1 <= len(telemetry[name]) <= 100:
            raise ValueError("Telemetry count outside bounds")
    if len(json.dumps(telemetry, allow_nan=False)) > 262144:
        raise ValueError("Telemetry size outside bounds")
    events = {event["event_id"]: event for event in case["events"]}
    sessions, event_sessions = {}, {}
    nodes = list(graph["nodes"])
    edges = list(graph["edges"])
    prefix = case["case_id"] + "/fictional-session-host/"

    def attach(kind, identifier, payload):
        _identifier(identifier)
        key = prefix + kind + "/" + identifier
        evidence_key = prefix + "evidence/" + kind + "-" + identifier
        nodes.append({"id": key, "type": kind, "label": identifier,
                      "source_id": telemetry["source_id"], "payload": payload})
        nodes.append({"id": evidence_key, "type": "evidence", "label": kind + "-" + identifier,
                      "source_id": telemetry["source_id"], "payload_sha256": digest(payload)})
        edges.append({"source": key, "target": evidence_key, "relation": "SUPPORTED_BY"})
        return key

    for session in telemetry["sessions"]:
        _fields(session, "session_id identity_id started_at ended_at event_ids")
        sid = _identifier(session["session_id"])
        _identifier(session["identity_id"])
        if sid in sessions:
            raise ValueError("Duplicate session")
        start, end = parse_timestamp(session["started_at"]), parse_timestamp(session["ended_at"])
        if end <= start:
            raise ValueError("Invalid session interval")
        if not isinstance(session["event_ids"], list) or not 1 <= len(session["event_ids"]) <= 100:
            raise ValueError("Session requires bounded event references")
        key = attach("session", sid, session)
        sessions[sid] = (session, key, start, end)
        for eid in session["event_ids"]:
            _identifier(eid)
            if eid not in events or eid in event_sessions:
                raise ValueError("Unknown or ambiguously assigned session event")
            event = events[eid]
            if event["identity_id"] != session["identity_id"]:
                raise ValueError("Session identity mismatch")
            if not start <= parse_timestamp(event["occurred_at"]) < end:
                raise ValueError("Event outside declared session")
            event_sessions[eid] = sid
            edges.append({"source": key, "target": case["case_id"] + "/event/" + eid,
                          "relation": "CONTAINS_DECLARED_REQUEST"})
        edges.append({"source": case["case_id"] + "/identity/" + session["identity_id"],
                      "target": key, "relation": "HAS_DECLARED_SESSION"})

    host_ids = set()
    for host in telemetry["hosts"]:
        _fields(host, "observation_id host_id session_id event_id observed_at process_name")
        for field in ("observation_id", "host_id", "session_id", "event_id", "process_name"):
            _identifier(host[field])
        hid = host["observation_id"]
        if hid in host_ids:
            raise ValueError("Duplicate host observation")
        host_ids.add(hid)
        if event_sessions.get(host["event_id"]) != host["session_id"]:
            raise ValueError("Host reference does not match an assigned session event")
        _, session_key, start, end = sessions[host["session_id"]]
        if not start <= parse_timestamp(host["observed_at"]) < end:
            raise ValueError("Host observation outside session")
        key = attach("host_observation", hid, host)
        edges.extend([
            {"source": key, "target": session_key, "relation": "EXPLICIT_SESSION_REFERENCE"},
            {"source": key, "target": case["case_id"] + "/event/" + host["event_id"],
             "relation": "EXPLICIT_EVENT_REFERENCE"},
        ])
    ids = {node["id"] for node in nodes}
    if len(ids) != len(nodes) or any(e["source"] not in ids or e["target"] not in ids for e in edges):
        raise ValueError("Invalid connected graph topology")
    report = run_case(case)
    result = {
        "case_id": case["case_id"], "synthetic": True,
        "approval_status": "NOT_AUTHORIZED_FOR_ACTION",
        "case_sha256": digest(case), "telemetry_sha256": digest(telemetry),
        "nodes": sorted(nodes, key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: (e["source"], e["target"], e["relation"])),
        "normalized_source": normalized,
        "session_count": len(sessions), "host_observation_count": len(host_ids),
        "unassigned_event_ids": sorted(set(events) - set(event_sessions)),
        "authorization_decisions": report["authorization_decisions"],
        "scenario_findings": report["scenario_findings"],
        "fixture_runtime_cost": report["runtime_metrics"],
        "hypothetical_annual_exposure": report["financial_risk"],
        "limitations": "Fictional declared links, not causal proof or authenticated telemetry. No external adapters or remediation. Fixture costs and hypothetical annual exposure are separate quantities.",
    }
    result["report_sha256"] = digest(result)
    return result
