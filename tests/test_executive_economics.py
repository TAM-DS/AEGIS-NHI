"""Tests for the executive layer's reproducible, separated model evidence."""

from copy import deepcopy
from pathlib import Path

import pytest

from aegis_nhi.economics import compare_control_investment
from aegis_nhi.risk import quantify_annual_loss
from aegis_nhi.workflow import load_case

CASE = Path(__file__).resolve().parents[1] / "data/scenarios/unauthorized_ai_agent.json"


def test_histogram_reconciles_to_simulations_and_is_reproducible():
    inputs = load_case(CASE)["annual_loss_model"]
    a = quantify_annual_loss(inputs)
    b = quantify_annual_loss(inputs)
    hist = a["annual_loss_histogram"]
    assert hist == b["annual_loss_histogram"]
    assert len(hist["bins"]) == 16
    assert hist["zero_loss_years"] + hist["tail_years_above_cutoff"] + sum(
        item["count"] for item in hist["bins"]
    ) == a["simulations"]
    assert hist["zero_loss_years"] > 0
    assert hist["unit"] == "simulated_years"


def test_zero_risk_is_all_zero_loss_years():
    inputs = deepcopy(load_case(CASE)["annual_loss_model"])
    r = quantify_annual_loss(inputs, hypothetical_control_effectiveness=1)
    hist = r["annual_loss_histogram"]
    assert hist["zero_loss_years"] == inputs["simulations"]
    assert sum(x["count"] for x in hist["bins"]) == 0
    assert hist["tail_years_above_cutoff"] == 0


def test_economics_analytical_risk_reduction_and_npv():
    model = load_case(CASE)["annual_loss_model"]
    baseline = quantify_annual_loss(model)["expected_annual_loss_usd"]
    residual = quantify_annual_loss(
        model, hypothetical_control_effectiveness=0.35
    )["expected_annual_loss_usd"]
    result = compare_control_investment(
        baseline_expected_annual_loss_usd=baseline,
        residual_expected_annual_loss_usd=residual,
        one_time_cost_usd=75000,
        annual_operating_cost_usd=20000,
        years=3,
        discount_rate=0.1,
    )
    assert result["modeled_annual_risk_reduction_usd"] == pytest.approx(
        0.35 * baseline, abs=0.02
    )
    annual_net = baseline - residual - 20000
    assert result["annual_net_modeled_value_usd"] == pytest.approx(annual_net, abs=0.01)
    expected_npv = annual_net * sum(1 / 1.1**n for n in range(1, 4)) - 75000
    assert result["discounted_net_modeled_value_usd"] == pytest.approx(expected_npv, abs=0.01)
    assert result["simple_payback_months"] is not None
    assert result["basis"].startswith("hypothetical")


def test_zero_effectiveness_never_creates_positive_model_value():
    result = compare_control_investment(
        baseline_expected_annual_loss_usd=100000,
        residual_expected_annual_loss_usd=100000,
        one_time_cost_usd=25000,
        annual_operating_cost_usd=5000,
    )
    assert result["modeled_annual_risk_reduction_usd"] == 0
    assert result["discounted_net_modeled_value_usd"] < 0
    assert result["simple_payback_months"] is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"baseline_expected_annual_loss_usd": float("nan")},
        {"residual_expected_annual_loss_usd": 1000000},
        {"one_time_cost_usd": -1},
        {"annual_operating_cost_usd": float("inf")},
        {"years": 0},
        {"years": 20},
        {"discount_rate": -0.01},
    ],
)
def test_bad_comparison_parameters_are_rejected(kwargs):
    inputs = dict(
        baseline_expected_annual_loss_usd=100000,
        residual_expected_annual_loss_usd=50000,
        one_time_cost_usd=15000,
        annual_operating_cost_usd=5000,
    )
    inputs.update(kwargs)
    with pytest.raises(ValueError):
        compare_control_investment(**inputs)
