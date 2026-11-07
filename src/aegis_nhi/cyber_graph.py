"""Evidence-linked graph of one synthetic AEGIS-NHI investigation.

Graph topology is built ONLY from validated fixture events, policy replay and
registered source evidence. It does not infer relationships between distinct
cases, discover real threats, or authorize any action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .authorization import evaluate_events
from .investigations import analyze_specialized_case
from .workflow import load_case, validate_case


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def build_case_graph(case: dict[str, Any]) -> dict[str, Any]:
    """Produce a deterministic case-scoped node/edge graph with source references."""
    validate_case(case)
    case_id = case["case_id"]
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("A named synthetic case is required")
    decisions = evaluate_events(case["events"], case["grants"])
    by_event = {decision["event_id"]: decision for decision in decisions}
    specialized = (
        analyze_specialized_case(case, decisions)
        if case["scenario_type"] in {"sensitive_data_exposure", "shadow_ai"} else None
    )

    nodes: dict[str, dict[str, Any]] = {}
    edges: set[tuple[str, str, str]] = set()

    def node(category: str, original_id: str, **attrs: Any) -> str:
        if not isinstance(original_id, str) or not original_id:
            raise ValueError("Graph identifiers must be named")
        key = f"{case_id}/{category}/{original_id}"
        proposed = {"id": key, "type": category, "label": original_id, **attrs}
        if key in nodes and nodes[key] != proposed:
            raise ValueError("Conflicting graph node evidence")
        nodes[key] = proposed
        return key

    def link(source: str, target: str, relation: str) -> None:
        edges.add((source, target, relation))

    root = node("case", case_id, title=case["title"])
    evidence_keys = {}
    for item in case["evidence"]:
        eid = item["evidence_id"]
        evidence_keys[eid] = node("evidence", eid, kind=item["kind"])
        link(root, evidence_keys[eid], "HAS_SOURCE_EVIDENCE")

    for grant in case["grants"]:
        grant_key = node("grant", grant["grant_id"])
        principal = node("identity", grant["identity_id"])
        resource = node("resource", grant["resource_id"])
        link(principal, grant_key, "HAS_SYNTHETIC_GRANT")
        link(grant_key, resource, "GRANTS_SCOPED_ACCESS")
        link(root, grant_key, "DECLARES_GRANT")

    for event in case["events"]:
        decision = by_event[event["event_id"]]
        event_key = node(
            "event", event["event_id"],
            observed_outcome=event["observed_outcome"],
            action=event["requested_action"],
            occurred_at=event["occurred_at"],
            policy_authorized=decision["authorized"],
            control_failure=decision["control_failure"],
        )
        principal = node("identity", event["identity_id"])
        resource = node("resource", event["resource_id"])
        link(root, event_key, "CONTAINS_EVENT")
        link(principal, event_key, "REQUESTED")
        link(event_key, resource, "TARGETED_RESOURCE")
        for evidence_id in event["evidence_ids"]:
            link(event_key, evidence_keys[evidence_id], "SUPPORTED_BY")
        if decision["grant_id"]:
            link(event_key, node("grant", decision["grant_id"]), "MATCHED_SCOPED_GRANT")
        if event.get("tool_id"):
            tool_key = node("tool", event["tool_id"])
            link(event_key, tool_key, "DECLARED_TOOL")

    if specialized:
        for finding in specialized["findings"]:
            event_key = f"{case_id}/event/{finding['event_id']}"
            finding_key = node(
                "finding", finding["finding_id"],
                rule=finding["rule"],
                observed_executed=finding["observed_executed"],
                severity=finding["severity"],
            )
            link(root, finding_key, "CONTAINS_POLICY_FINDING")
            link(finding_key, event_key, "FLAGS_EVENT")
            for evidence_id in finding["evidence_ids"]:
                link(finding_key, evidence_keys[evidence_id], "SUPPORTED_BY")

    ordered_nodes = sorted(nodes.values(), key=lambda v: v["id"])
    ordered_edges = [
        {"source": a, "target": b, "relation": rel}
        for a, b, rel in sorted(edges)
    ]
    allowed = set(nodes)
    if not all(edge["source"] in allowed and edge["target"] in allowed for edge in ordered_edges):
        raise ValueError("A graph edge referenced an unknown node")
    result = {
        "case_id": case_id,
        "synthetic": True,
        "scope": "single_fictional_investigation_no_external_integrations",
        "approval_status": "NOT_AUTHORIZED_FOR_ACTION",
        "source_case_sha256": _hash(case),
        "nodes": ordered_nodes,
        "edges": ordered_edges,
        "counts": {
            "nodes": len(ordered_nodes),
            "edges": len(ordered_edges),
            "recorded_executions": sum(x["observed_outcome"] == "executed" for x in case["events"]),
            "recorded_blocks": sum(x["observed_outcome"] == "blocked" for x in case["events"]),
            "policy_findings": len(specialized["findings"]) if specialized else 0,
        },
    }
    result["graph_sha256"] = _hash(result)
    return result



def verify_case_graph(case: dict[str, Any], graph: Any) -> None:
    """Require an export to match a fresh projection of a trusted local source.

    A self-consistent hash alone is not proof of source integrity. The caller
    must select the trusted case independently of the export being verified.
    This comparison is not a digital signature or permission to act.
    """
    expected = build_case_graph(case)
    try:
        supplied = json.dumps(graph, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError):
        raise ValueError("Graph export is not valid JSON data") from None
    if supplied != json.dumps(expected, sort_keys=True, allow_nan=False):
        raise ValueError("Graph export does not match the selected source case")


def main() -> None:
    parser = argparse.ArgumentParser(description="AEGIS-NHI synthetic cyber graph export")
    parser.add_argument("--scenario", default="data/scenarios/sensitive_data_exposure.json")
    parser.add_argument("--output", help="Optional JSON export path")
    parser.add_argument("--verify", help="Verify a JSON export against the selected source scenario")
    options = parser.parse_args()
    if options.verify and options.output:
        parser.error("--verify and --output cannot be combined")
    case = load_case(options.scenario)
    if options.verify:
        exported = json.loads(Path(options.verify).read_text(encoding="utf-8"))
        verify_case_graph(case, exported)
        print("Verified graph matches selected synthetic source; no action authorized.")
        return
    graph = build_case_graph(case)
    output = json.dumps(graph, indent=2, sort_keys=True) + "\n"
    if options.output:
        target = Path(options.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output, encoding="utf-8")
        print(f"Exported synthetic graph: {target}")
    else:
        print(output)


if __name__ == "__main__":
    main()
