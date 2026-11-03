"""Three bounded, deterministic investigation roles composing one evidence report.

This milestone implements rule-based agent roles, not an LLM autonomous system.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, TypeVar

from .authorization import evaluate_events, parse_timestamp
from .risk import quantify_annual_loss

T = TypeVar("T")
_ALLOWED_TOOLS = {
    "policy_evaluation",
    "runtime_summary",
    "loss_quantification",
    "executive_brief",
}


class ToolLedger:
    """Tool allowlist and overall per-case budget; no network or mutation tools."""

    def __init__(self, max_calls: int = 12) -> None:
        if max_calls < 1:
            raise ValueError("Tool budget must be positive")
        self.max_calls = max_calls
        self.calls: list[dict[str, Any]] = []

    def invoke(self, role: str, tool: str, implementation: Callable[[], T]) -> T:
        if tool not in _ALLOWED_TOOLS:
            raise PermissionError("Non-allowlisted tool denied")
        if len(self.calls) >= self.max_calls:
            raise RuntimeError("Tool budget exhausted: fail-closed")
        result = implementation()
        fingerprint = hashlib.sha256(
            json.dumps(result, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        self.calls.append(
            {"agent_role": role, "tool": tool, "output_sha256": fingerprint, "read_only": True}
        )
        return result


def load_case(path: str | Path) -> dict[str, Any]:
    case = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_case(case)
    return case


def validate_case(case: dict[str, Any]) -> None:
    required = ("case_id", "title", "scenario_type", "evidence", "events", "grants", "annual_loss_model")
    if not isinstance(case, dict) or any(field not in case for field in required):
        raise ValueError("Scenario lacks required evidence and risk fields")
    if not case.get("synthetic") is True:
        raise ValueError("Only explicitly synthetic scenarios may be processed")
    if not case["events"] or not case["evidence"]:
        raise ValueError("Scenario needs synthetic events and evidence")
    evidence_ids = {item["evidence_id"] for item in case["evidence"]}
    if len(evidence_ids) != len(case["evidence"]):
        raise ValueError("Duplicate evidence identifier")
    event_ids = [event["event_id"] for event in case["events"]]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("Duplicate event identifier")
    for event in case["events"]:
        parse_timestamp(event["occurred_at"])
        if event["observed_outcome"] not in {"blocked", "executed"}:
            raise ValueError("Invalid observed outcome")
        if not event["evidence_ids"] or not set(event["evidence_ids"]) <= evidence_ids:
            raise ValueError("Unknown event evidence reference")
        cost = Decimal(str(event["synthetic_tool_cost_usd"]))
        if not cost.is_finite() or cost < 0:
            raise ValueError("Synthetic event cost must be finite and nonnegative")
    for grant in case["grants"]:
        if parse_timestamp(grant["expires_at"]) <= parse_timestamp(grant["issued_at"]):
            raise ValueError("Invalid synthetic grant validity interval")


def summarize_runtime(events: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(
        (Decimal(str(e["synthetic_tool_cost_usd"])) for e in events), Decimal("0")
    )
    return {
        "basis": "synthetic_observed_fixture",
        "currency": "USD",
        "period": "incident_window",
        "tool_call_events": len(events),
        "recorded_executions": sum(e["observed_outcome"] == "executed" for e in events),
        "recorded_blocks": sum(e["observed_outcome"] == "blocked" for e in events),
        "synthetic_tool_cost_usd": float(total.quantize(Decimal("0.000001"))),
        "limitation": "Synthetic fixture charges, not an invoice, cloud bill, or realized savings",
    }


def draft_executive_brief(
    case: dict[str, Any],
    decisions: list[dict[str, Any]],
    loss: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    denials = [item for item in decisions if not item["authorized"]]
    control_failures = [item for item in decisions if item["control_failure"]]
    if control_failures:
        finding = "One or more recorded executions contradict deny-by-default policy."
        recommendation = "Escalate the synthetic control-failure evidence for human investigation."
    elif denials:
        finding = "The authorization replay denied out-of-scope or inactive agent tool requests."
        recommendation = (
            "Review the agent's scoped runtime grants and require human approval for "
            "consequential transfer or bulk-export actions."
        )
    else:
        finding = "All supplied synthetic events matched a scoped active runtime grant."
        recommendation = "Review the control evidence and maintain monitoring."
    return {
        "title": "Executive decision brief: " + case["title"],
        "finding": finding,
        "event_count": len(decisions),
        "denied_count": len(denials),
        "policy_control_failures": len(control_failures),
        "synthetic_runtime_tool_cost_usd": runtime["synthetic_tool_cost_usd"],
        "counterfactual_expected_annual_loss_usd": loss["expected_annual_loss_usd"],
        "recommendation": recommendation,
        "proposed_decision": "REVIEW_RECOMMENDATION_ONLY",
        "approval_status": "PENDING_HUMAN_REVIEW",
        "evidence_ids": sorted({e for item in decisions for e in item["evidence_ids"]}),
        "limitations": (
            "Risk figures are scenario model outputs and are not actual or prevented losses. "
            "Review approval records do not authorize bank operations."
        ),
    }


def run_case(
    case: dict[str, Any],
    *,
    frequency_multiplier: float = 1.0,
    hypothetical_control_effectiveness: float = 0.0,
    tool_budget: int = 12,
) -> dict[str, Any]:
    validate_case(case)
    ledger = ToolLedger(max_calls=tool_budget)
    decisions = ledger.invoke(
        "FinOps Auditor", "policy_evaluation", lambda: evaluate_events(case["events"], case["grants"])
    )
    runtime = ledger.invoke(
        "FinOps Auditor", "runtime_summary", lambda: summarize_runtime(case["events"])
    )
    loss = ledger.invoke(
        "Risk Actuary",
        "loss_quantification",
        lambda: quantify_annual_loss(
            case["annual_loss_model"],
            frequency_multiplier=frequency_multiplier,
            hypothetical_control_effectiveness=hypothetical_control_effectiveness,
        ),
    )
    brief = ledger.invoke(
        "Executive Reporter",
        "executive_brief",
        lambda: draft_executive_brief(case, decisions, loss, runtime),
    )
    report = {
        "case_id": case["case_id"],
        "title": case["title"],
        "scenario_type": case["scenario_type"],
        "synthetic": True,
        "status": "PENDING_HUMAN_REVIEW",
        "authorization_decisions": decisions,
        "runtime_metrics": runtime,
        "financial_risk": loss,
        "executive_brief": brief,
        "evidence": case["evidence"],
        "agent_roles": ["FinOps Auditor", "Risk Actuary", "Executive Reporter"],
        "tool_trace": ledger.calls,
        "tool_budget": ledger.max_calls,
        "provenance": {
            "case_sha256": hashlib.sha256(
                json.dumps(case, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "engine_version": "0.1.0",
            "model": "seeded-poisson-triangular-v1",
        },
    }
    report["report_id"] = hashlib.sha256(
        json.dumps(report, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return report
