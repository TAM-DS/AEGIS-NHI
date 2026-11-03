"""Fail-closed, event-time non-human identity authorization evaluator."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_timestamp(value: str) -> datetime:
    """Parse an offset-aware ISO-8601 timestamp; fail closed on ambiguity."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, AttributeError, ValueError) as exc:
        raise ValueError("A valid ISO-8601 timestamp is required") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Naive timestamps are not authorized")
    return parsed


def evaluate_event(event: dict[str, Any], grants: list[dict[str, Any]]) -> dict[str, Any]:
    """A tool's technical capability never implies a scoped runtime grant.

    This is a synthetic policy replay, not a live access-control enforcement point.
    """
    when = parse_timestamp(event["occurred_at"])
    principal = event["identity_id"]
    resource = event["resource_id"]
    action = event["requested_action"]

    candidates = [g for g in grants if g["identity_id"] == principal]
    if not candidates:
        reason, matching = "DENY_NO_IDENTITY_GRANT", []
    else:
        on_resource = [g for g in candidates if g["resource_id"] == resource]
        if not on_resource:
            reason, matching = "DENY_RESOURCE_OUT_OF_SCOPE", []
        else:
            on_action = [g for g in on_resource if action in g.get("allowed_actions", [])]
            if not on_action:
                reason, matching = "DENY_ACTION_NOT_GRANTED", []
            else:
                valid_time = [
                    g
                    for g in on_action
                    if parse_timestamp(g["issued_at"]) <= when < parse_timestamp(g["expires_at"])
                ]
                if not valid_time:
                    reason, matching = "DENY_GRANT_NOT_ACTIVE", []
                else:
                    matching = [g for g in valid_time if g.get("approved_by", "").strip()]
                    reason = "ALLOW_SCOPED_RUNTIME_GRANT" if matching else "DENY_UNAPPROVED_GRANT"

    authorized = bool(matching)
    observed = event["observed_outcome"]
    if observed not in {"executed", "blocked"}:
        raise ValueError("Observed outcome must be executed or blocked")
    # An observed execution contrary to policy is an evidence-based control failure.
    control_failure = observed == "executed" and not authorized
    return {
        "event_id": event["event_id"],
        "identity_id": principal,
        "resource_id": resource,
        "requested_action": action,
        "observed_outcome": observed,
        "authorized": authorized,
        "reason": reason,
        "grant_id": matching[0]["grant_id"] if authorized else None,
        "control_failure": control_failure,
        "evidence_ids": list(event["evidence_ids"]),
        "basis": "synthetic_event_and_grant_replay",
    }


def evaluate_events(events: list[dict[str, Any]], grants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [evaluate_event(event, grants) for event in events]
