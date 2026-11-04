"""Deterministic synthetic investigations: sensitive-data exposure and shadow AI.

All evaluations replay user-supplied synthetic fixture events and metadata. This is
not live DLP, shadow-AI discovery, or a real-world enforcement system.
"""

from __future__ import annotations

from typing import Any


def _nonempty_set(value: object, label: str) -> set[str]:
    if (not isinstance(value, list) or not value or
        any(not isinstance(v, str) or not v.strip() for v in value) or
        len(value) != len(set(value))):
        raise ValueError(f"{label} must be unique nonempty strings")
    return set(value)


def analyze_specialized_case(
    case: dict[str, Any], decisions: list[dict[str, Any]]
) -> dict[str, Any]:
    scenario = case.get("scenario_type")
    if scenario not in {"sensitive_data_exposure", "shadow_ai"}:
        raise ValueError("Unsupported specialized scenario type")
    if len(decisions) != len(case["events"]):
        raise ValueError("Policy replay must cover all events")
    by_id = {d["event_id"]: d for d in decisions}
    if len(by_id) != len(decisions):
        raise ValueError("Duplicate policy event ID")
    evidence = {e["evidence_id"] for e in case["evidence"]}
    if scenario == "sensitive_data_exposure":
        policy = case.get("data_controls")
        if not isinstance(policy, dict):
            raise ValueError("Missing data controls")
        classes = policy.get("resource_classifications")
        if not isinstance(classes, dict):
            raise ValueError("Missing resource classification map")
        protected = _nonempty_set(policy.get("sensitive_classes"), "Sensitive classes")
        guarded = _nonempty_set(policy.get("sensitive_actions"), "Sensitive actions")
        regions = _nonempty_set(
            policy.get("approved_processing_regions"), "Approved processing regions"
        )
    else:
        registry = case.get("ai_registry")
        if not isinstance(registry, dict):
            raise ValueError("Missing AI registry")
        identities = _nonempty_set(registry.get("approved_identity_ids"), "Approved identities")
        tools = _nonempty_set(registry.get("registered_tool_ids"), "Registered tools")
    findings: list[dict[str, Any]] = []
    for event in case["events"]:
        decision = by_id.get(event["event_id"])
        if decision is None:
            raise ValueError("Missing policy event decision")
        refs = event["evidence_ids"]
        if not refs or not set(refs).issubset(evidence):
            raise ValueError("Unknown finding evidence")
        rules: list[str] = []
        if scenario == "sensitive_data_exposure":
            classification = classes.get(event["resource_id"])
            if not isinstance(classification, str) or not classification.strip():
                raise ValueError("Unclassified resource in data scenario")
            if classification in protected:
                if event["requested_action"] in guarded:
                    rules.append("SENSITIVE_ACTION_ATTEMPT")
                if event.get("declared_destination_region") not in regions:
                    rules.append("SENSITIVE_REGION_OUT_OF_POLICY")
        else:
            tool_id = event.get("tool_id")
            if not isinstance(tool_id, str) or not tool_id.strip():
                raise ValueError("Shadow AI event lacks explicit tool ID")
            if event["identity_id"] not in identities:
                rules.append("UNREGISTERED_AI_IDENTITY")
            if tool_id not in tools:
                rules.append("UNREGISTERED_AI_TOOL")
        for rule in rules:
            executed = event["observed_outcome"] == "executed"
            findings.append({
                "finding_id": f"{event['event_id']}:{rule}",
                "rule": rule,
                "event_id": event["event_id"],
                "identity_id": event["identity_id"],
                "resource_id": event["resource_id"],
                "observed_outcome": event["observed_outcome"],
                "policy_authorized": decision["authorized"],
                "observed_executed": executed,
                "severity": "HIGH" if executed else "REVIEW",
                "evidence_ids": list(refs),
                "basis": "synthetic_offline_policy_and_metadata_replay",
            })
    return {
        "scenario_type": scenario,
        "basis": "synthetic_offline_policy_and_metadata_replay",
        "status": "REVIEW_REQUIRED" if findings else "NO_SPECIALIZED_FINDINGS",
        "flagged_event_count": len({f["event_id"] for f in findings}),
        "executed_flagged_event_count": len({
            f["event_id"] for f in findings if f["observed_executed"]
        }),
        "rule_finding_count": len(findings),
        "policy_control_failure_count": sum(d["control_failure"] for d in decisions),
        "findings": findings,
        "evidence_ids": sorted({e for f in findings for e in f["evidence_ids"]}),
        "human_decision": "PENDING_HUMAN_REVIEW",
        "limitations": (
            "Declared metadata and fictional event traces only; no deployed detection, "
            "real data exfiltration proof, actual financial loss, or prevented harm."
        ),
    }
