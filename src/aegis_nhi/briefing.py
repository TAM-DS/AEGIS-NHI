"""Express modeled control economics in concise executive decision language."""

from __future__ import annotations

import math
from typing import Any


def money(value: float, signed: bool = False) -> str:
    """USD formatter; no special treatment of financial losses as observed."""
    if not math.isfinite(value):
        raise ValueError("Only finite financial values can be presented")
    sign = "-" if value < 0 else ("+" if signed and value > 0 else "")
    return sign + "$" + format(abs(value), ",.0f")


def interpret_control_case(
    comparison: dict[str, Any],
    *,
    assumed_effectiveness_pct: int,
    reviewer_decision: str | None,
) -> dict[str, str]:
    """Explain synthetic financial assumptions, never authorize operations."""
    if isinstance(assumed_effectiveness_pct, bool) or not 0 <= assumed_effectiveness_pct <= 100:
        raise ValueError("Effectiveness must be 0–100 percent")
    if reviewer_decision not in (None, "APPROVED", "REJECTED"):
        raise ValueError("Invalid human recommendation-review status")
    baseline = float(comparison["modeled_baseline_annual_loss_usd"])
    residual = float(comparison["modeled_residual_annual_loss_usd"])
    reduction = float(comparison["modeled_annual_risk_reduction_usd"])
    year_one = float(comparison["year_one_net_modeled_value_usd"])
    three_year = float(comparison["discounted_net_modeled_value_usd"])
    if not all(math.isfinite(x) for x in (baseline, residual, reduction, year_one, three_year)):
        raise ValueError("Scenario model values must be finite")
    if three_year > 0:
        signal = "CONDITIONAL POSITIVE"
        rationale = "The modeled three-year discounted case is favorable"
    elif three_year < 0:
        signal = "CONDITIONAL NEGATIVE"
        rationale = "The modeled three-year discounted case is unfavorable"
    else:
        signal = "MODELED BREAK-EVEN"
        rationale = "The modeled three-year discounted case is approximately break-even"
    first_year_label = "negative" if year_one < 0 else ("positive" if year_one > 0 else "break-even")
    review_status = (
        "PENDING HUMAN REVIEW" if reviewer_decision is None
        else "RECOMMENDATION REVIEWED — " + reviewer_decision
    )
    return {
        "investment_signal": signal,
        "decision_status": review_status,
        "economic_interpretation": (
            f"At the current assumption of {assumed_effectiveness_pct}% added control "
            f"effectiveness, annual modeled loss changes from {money(baseline)} "
            f"to {money(residual)} — an illustrative reduction of {money(reduction)} "
            f"per year. Year-one net modeled value is {money(year_one, signed=True)} "
            f"({first_year_label}), while three-year discounted net modeled value is "
            f"{money(three_year, signed=True)}. {rationale}, but this is "
            "**not a measured return or an execution approval**."
        ),
        "next_action": (
            "Executive decision: review and challenge the assumptions, approve or "
            "reject the recommendation for further evaluation, or redesign the "
            "proposed control. Deployment needs separate enterprise authorization."
        ),
        "basis": "hypothetical_control_investment_and_synthetic_risk_scenario",
    }
