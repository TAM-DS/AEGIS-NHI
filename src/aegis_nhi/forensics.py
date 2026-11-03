"""Autonomous agent forensics: bounded synthetic tool telemetry and cost analysis.

This detects anomalous fixture behavior. It is not a production incident detection
service, network monitoring system, or automated containment control.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .authorization import evaluate_event, parse_timestamp

MAX_MINUTES = 1440
MAX_CALLS_PER_BUCKET = 1000000
MAX_PROJECTION_HOURS = 24


def positive_decimal(value: object, name: str, *, allow_zero: bool = False) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a decimal") from exc
    if not result.is_finite() or (result < 0 if allow_zero else result <= 0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.000001")))


def validate_forensics(case: dict[str, Any]) -> None:
    if not isinstance(case, dict) or case.get("synthetic") is not True:
        raise ValueError("Only synthetic agent telemetry cases are supported")
    required = (
        "case_id", "identity_id", "resource_id", "requested_action",
        "tool_signature", "occurred_at", "grant", "baseline", "pricing_assumptions",
        "minute_buckets", "evidence",
    )
    if any(key not in case for key in required):
        raise ValueError("Incomplete forensics case")
    start = parse_timestamp(case["occurred_at"])
    if not case["case_id"] or not case["identity_id"]:
        raise ValueError("Case and identity must be named")
    buckets = case["minute_buckets"]
    if not isinstance(buckets, list) or not 1 <= len(buckets) <= MAX_MINUTES:
        raise ValueError("Minute buckets outside bounded range")
    if not isinstance(case["evidence"], list):
        raise ValueError("Expected evidence list")
    evidence = [e["evidence_id"] for e in case["evidence"]]
    if not evidence or len(set(evidence)) != len(evidence):
        raise ValueError("Missing or duplicated evidence identifiers")
    maximum = int(case["baseline"]["max_calls_per_workflow"])
    normal = int(case["baseline"]["normal_calls_per_workflow"])
    normal_minute = int(case["baseline"]["normal_calls_per_minute"])
    if not 0 < normal <= maximum <= MAX_CALLS_PER_BUCKET:
        raise ValueError("Invalid workflow baseline and tool budget")
    if not 0 < normal_minute <= MAX_CALLS_PER_BUCKET:
        raise ValueError("Invalid normal per-minute call rate")
    burst = float(case["baseline"]["burst_multiplier"])
    if not math.isfinite(burst) or burst < 1:
        raise ValueError("Invalid burst multiplier")
    for field in ("input_usd_per_million", "output_usd_per_million", "gpu_usd_per_minute"):
        positive_decimal(case["pricing_assumptions"][field], field, allow_zero=True)
    grant = case["grant"]
    if parse_timestamp(grant["expires_at"]) <= parse_timestamp(grant["issued_at"]):
        raise ValueError("Invalid grant interval")
    total_calls = 0
    for index, bucket in enumerate(buckets):
        if bucket["minute"] != index or isinstance(bucket["minute"], bool):
            raise ValueError("Minute buckets must be contiguous starting at zero")
        calls = bucket["tool_calls"]
        repeated = bucket["repeated_signature_calls"]
        if any(
            isinstance(n, bool) or not isinstance(n, int)
            for n in (calls, repeated, bucket["input_tokens"], bucket["output_tokens"])
        ):
            raise ValueError("Call and token counts must be integers")
        if not 0 <= repeated <= calls <= MAX_CALLS_PER_BUCKET:
            raise ValueError("Repeated calls must be between zero and total tool calls")
        if min(bucket["input_tokens"], bucket["output_tokens"]) < 0:
            raise ValueError("Token counts must be nonnegative")
        if not bucket["evidence_ids"] or not set(bucket["evidence_ids"]) <= set(evidence):
            raise ValueError("Bucket references unknown evidence")
        positive_decimal(bucket["gpu_minutes"], "GPU minutes", allow_zero=True)
        total_calls += calls
        if total_calls > 5000000:
            raise ValueError("Synthetic call volume exceeds bounded input cap")
        # Every minute uses a single declared identity/action for this model.
        event_time = start + timedelta(minutes=index)
        if not case["resource_id"] or not case["requested_action"] or not event_time:
            raise ValueError("Missing requested tool resource or action")


def load_forensics_case(path: str | Path) -> dict[str, Any]:
    result = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_forensics(result)
    return result


def analyze_forensics(
    case: dict[str, Any],
    *,
    projection_hours: int = 1,
    token_rate_multiplier: float = 1.0,
    workflow_call_limit: int | None = None,
) -> dict[str, Any]:
    """Read-only analysis of synthetic observations with *hypothetical* charges.

    Synthetic counted tokens are not invoices. A token-price estimate and a
    GPU-meter estimate are separate cost bases that may overlap. Never add them.
    """
    validate_forensics(case)
    if isinstance(projection_hours, bool) or not isinstance(projection_hours, int):
        raise ValueError("Projection horizon must be integer hours")
    if not 1 <= projection_hours <= MAX_PROJECTION_HOURS:
        raise ValueError("Projection horizon must be between 1 and 24 hours")
    multiplier = float(token_rate_multiplier)
    if not math.isfinite(multiplier) or not 0.1 <= multiplier <= 5.0:
        raise ValueError("Token-rate multiplier outside bounded range")
    baseline = case["baseline"]
    limit = baseline["max_calls_per_workflow"] if workflow_call_limit is None else workflow_call_limit
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_CALLS_PER_BUCKET:
        raise ValueError("Workflow tool-call limit outside bounded range")
    price = case["pricing_assumptions"]
    million = Decimal("1000000")
    in_price = positive_decimal(price["input_usd_per_million"], "input price", allow_zero=True)
    out_price = positive_decimal(price["output_usd_per_million"], "output price", allow_zero=True)
    gpu_price = positive_decimal(price["gpu_usd_per_minute"], "GPU price", allow_zero=True)
    factor = Decimal(str(multiplier))
    total_calls, total_repeated, total_input, total_output = 0, 0, 0, 0
    total_gpu_minutes = Decimal("0")
    cumulative_token_estimate = Decimal("0")
    cumulative_gpu_estimate = Decimal("0")
    peak = 0
    findings: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    start = parse_timestamp(case["occurred_at"])
    burst_streak = 0
    first_burst_alert = None
    first_budget_alert = None
    auth_failures = 0
    for bucket in case["minute_buckets"]:
        minute = bucket["minute"]
        count = bucket["tool_calls"]
        total_calls += count
        total_repeated += bucket["repeated_signature_calls"]
        total_input += bucket["input_tokens"]
        total_output += bucket["output_tokens"]
        gpu = positive_decimal(bucket["gpu_minutes"], "GPU minutes", allow_zero=True)
        total_gpu_minutes += gpu
        minute_token_price = (
            (Decimal(bucket["input_tokens"]) * in_price / million)
            + (Decimal(bucket["output_tokens"]) * out_price / million)
        ) * factor
        cumulative_token_estimate += minute_token_price
        cumulative_gpu_estimate += gpu * gpu_price
        peak = max(peak, count)

        replay_event = {
            "event_id": f"FORENSICS-{minute:03d}",
            "occurred_at": (start + timedelta(minutes=minute)).isoformat(),
            "identity_id": case["identity_id"],
            "resource_id": case["resource_id"],
            "requested_action": case["requested_action"],
            "observed_outcome": "executed" if count > 0 else "blocked",
            "evidence_ids": list(bucket["evidence_ids"]),
        }
        authorized = evaluate_event(replay_event, [case["grant"]])
        if authorized["control_failure"]:
            auth_failures += 1

        if count >= baseline["normal_calls_per_minute"] * baseline["burst_multiplier"]:
            burst_streak += 1
        else:
            burst_streak = 0
        if burst_streak >= 2 and first_burst_alert is None:
            first_burst_alert = minute
        if total_calls > limit and first_budget_alert is None:
            first_budget_alert = minute

        timeline.append({
            "minute": minute,
            "tool_calls": count,
            "normal_calls_per_minute": baseline["normal_calls_per_minute"],
            "cumulative_calls": total_calls,
            "repeated_calls": bucket["repeated_signature_calls"],
            "input_tokens": bucket["input_tokens"],
            "output_tokens": bucket["output_tokens"],
            "cumulative_hypothetical_token_cost_usd": _money(cumulative_token_estimate),
            "cumulative_hypothetical_gpu_cost_usd": _money(cumulative_gpu_estimate),
            "policy_authorized": authorized["authorized"],
            "authorization_reason": authorized["reason"],
            "evidence_ids": list(bucket["evidence_ids"]),
        })
    if first_burst_alert is not None:
        findings.append({
            "rule": "SUSTAINED_TOOL_CALL_BURST",
            "severity": "HIGH",
            "detected_minute": first_burst_alert,
            "explanation": "Two consecutive minute buckets exceeded the configured normal-rate multiplier.",
            "evidence_ids": list(timeline[first_burst_alert]["evidence_ids"]),
        })
    if first_budget_alert is not None:
        findings.append({
            "rule": "WORKFLOW_CALL_BUDGET_EXCEEDED",
            "severity": "HIGH",
            "detected_minute": first_budget_alert,
            "explanation": "Observed synthetic cumulative calls exceeded the scenario tool-call budget.",
            "evidence_ids": list(timeline[first_budget_alert]["evidence_ids"]),
        })
    share = total_repeated / total_calls if total_calls else 0.0
    if total_calls >= baseline["normal_calls_per_workflow"] and share >= 0.9:
        findings.append({
            "rule": "REPEATED_TOOL_SIGNATURE_CONCENTRATION",
            "severity": "MEDIUM",
            "detected_minute": timeline[-1]["minute"],
            "explanation": "At least 90% of synthetic calls share one declared tool signature.",
            "evidence_ids": sorted(
                {item for bucket in case["minute_buckets"] for item in bucket["evidence_ids"]}
            ),
        })
    if auth_failures:
        findings.append({
            "rule": "RECORDED_UNAUTHORIZED_EXECUTION",
            "severity": "CRITICAL",
            "detected_minute": next(
                entry["minute"] for entry in timeline
                if entry["tool_calls"] > 0 and not entry["policy_authorized"]
            ),
            "explanation": "A synthetic executed tool call contradicted the scoped event-time grant.",
            "evidence_ids": sorted(
                {item for entry in timeline if not entry["policy_authorized"]
                 for item in entry["evidence_ids"]}
            ),
        })
    duration = len(timeline)
    continuation_minutes = projection_hours * 60
    # Purely linear *incremental future scenario* at the simulated observed rate.
    forecast_calls = total_calls / duration * continuation_minutes
    forecast_token_cost = cumulative_token_estimate / duration * continuation_minutes
    forecast_gpu_cost = cumulative_gpu_estimate / duration * continuation_minutes
    summary = {
        "case_id": case["case_id"],
        "scenario_type": "synthetic_runaway_agent_forensics",
        "identity_id": case["identity_id"],
        "tool_signature": case["tool_signature"],
        "status": "ANOMALOUS_SYNTHETIC_ACTIVITY" if findings else "NO_RULE_TRIGGER",
        "tool_calls": total_calls,
        "baseline_calls_per_workflow": baseline["normal_calls_per_workflow"],
        "amplification_factor": round(total_calls / baseline["normal_calls_per_workflow"], 2),
        "peak_calls_per_minute": peak,
        "repeated_signature_share_pct": round(share * 100, 2),
        "synthetic_metered_input_tokens": total_input,
        "synthetic_metered_output_tokens": total_output,
        "synthetic_metered_gpu_minutes": _money(total_gpu_minutes),
        "hypothetical_incurred_token_cost_usd": _money(cumulative_token_estimate),
        "hypothetical_incurred_gpu_cost_usd": _money(cumulative_gpu_estimate),
        "recorded_authorization_failures": auth_failures,
        "first_burst_alert_minute": first_burst_alert,
        "first_budget_alert_minute": first_budget_alert,
        "configured_call_limit": limit,
        "timeline": timeline,
        "alerts": findings,
        "projection": {
            "additional_hours": projection_hours,
            "basis": "hypothetical_linear_continuation_of_synthetic_minute_rate",
            "additional_tool_calls": round(forecast_calls),
            "additional_token_cost_usd": _money(forecast_token_cost),
            "additional_gpu_cost_usd": _money(forecast_gpu_cost),
        },
        "economics_basis": (
            "Synthetic metered token counts and GPU minutes, priced using configurable "
            "hypothetical unit rates. Not invoiced or realized charges. Token and GPU "
            "cost estimates may overlap and MUST NOT be added to each other."
        ),
        "human_decision": (
            "Human investigation recommended; review tool scope and enforced runtime call "
            "limits. NO automatic termination, cloud mutation, IAM changes, or bank action."
        ),
        "execution_boundary": "OFFLINE_SYNTHETIC_READ_ONLY",
        "review_status": "PENDING_HUMAN_REVIEW",
    }
    summary["report_id"] = hashlib.sha256(
        json.dumps({
            "source": case,
            "projection_hours": projection_hours,
            "token_rate_multiplier": multiplier,
            "workflow_call_limit": limit,
        }, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return summary
