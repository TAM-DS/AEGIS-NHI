"""Scenario-only control economics; modeled exposure is never a realized saving."""

from __future__ import annotations

import math
from typing import Any


def compare_control_investment(
    *,
    baseline_expected_annual_loss_usd: float,
    residual_expected_annual_loss_usd: float,
    one_time_cost_usd: float,
    annual_operating_cost_usd: float,
    years: int = 3,
    discount_rate: float = 0.1,
) -> dict[str, Any]:
    """Compare two *conditional model* outputs and hypothetical control costs.

    This is an analytical planning comparison, not observed cash flow, saved
    cloud spending, insurer pricing, or promised avoidance of future losses.
    """
    values = (
        baseline_expected_annual_loss_usd,
        residual_expected_annual_loss_usd,
        one_time_cost_usd,
        annual_operating_cost_usd,
        discount_rate,
    )
    if not all(math.isfinite(x) for x in values):
        raise ValueError("All scenario inputs must be finite")
    if any(x < 0 for x in values) or discount_rate > 1:
        raise ValueError("Costs, modeled loss, and discount rate must be nonnegative")
    if residual_expected_annual_loss_usd > baseline_expected_annual_loss_usd:
        raise ValueError("This comparison expects non-increasing modeled exposure")
    if isinstance(years, bool) or not isinstance(years, int) or not 1 <= years <= 10:
        raise ValueError("Planning horizon must be 1..10 whole years")

    annual_reduction = baseline_expected_annual_loss_usd - residual_expected_annual_loss_usd
    annual_net = annual_reduction - annual_operating_cost_usd
    discount_factor = sum(1 / ((1 + discount_rate) ** n) for n in range(1, years + 1))
    npv = annual_net * discount_factor - one_time_cost_usd
    payback = (one_time_cost_usd / annual_net * 12) if annual_net > 0 else None
    return {
        "basis": "hypothetical_control_cost_vs_modeled_future_risk",
        "currency": "USD",
        "horizon_years": years,
        "discount_rate_assumption": discount_rate,
        "modeled_baseline_annual_loss_usd": round(baseline_expected_annual_loss_usd, 2),
        "modeled_residual_annual_loss_usd": round(residual_expected_annual_loss_usd, 2),
        "modeled_annual_risk_reduction_usd": round(annual_reduction, 2),
        "one_time_control_cost_usd": round(one_time_cost_usd, 2),
        "annual_control_operating_cost_usd": round(annual_operating_cost_usd, 2),
        "annual_net_modeled_value_usd": round(annual_net, 2),
        "year_one_net_modeled_value_usd": round(annual_net - one_time_cost_usd, 2),
        "discounted_net_modeled_value_usd": round(npv, 2),
        "simple_payback_months": round(payback, 1) if payback is not None else None,
        "limitations": (
            "All controls and effectiveness assumptions are hypothetical. Estimated "
            "risk reduction is NOT booked savings, an insurance quote, or a realized "
            "security benefit. Simple payback excludes discounting; the NPV applies "
            "the selected annual discount rate to modeled net benefits."
        ),
    }
