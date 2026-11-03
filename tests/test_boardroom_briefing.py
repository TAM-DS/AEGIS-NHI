"""Executive economic summary preserves assumption and authority boundaries."""

from pathlib import Path

import pytest

from aegis_nhi.briefing import interpret_control_case
from aegis_nhi.economics import compare_control_investment
from aegis_nhi.risk import quantify_annual_loss
from aegis_nhi.workflow import load_case

FIXTURE = Path(__file__).resolve().parents[1] / "data/scenarios/unauthorized_ai_agent.json"


def model(eff: float, cost: float, ops: float):
    config = load_case(FIXTURE)["annual_loss_model"]
    baseline = quantify_annual_loss(config)["expected_annual_loss_usd"]
    residual = quantify_annual_loss(
        config, hypothetical_control_effectiveness=eff
    )["expected_annual_loss_usd"]
    return compare_control_investment(
        baseline_expected_annual_loss_usd=baseline,
        residual_expected_annual_loss_usd=residual,
        one_time_cost_usd=cost,
        annual_operating_cost_usd=ops,
    )


def test_favorable_three_year_and_negative_first_year_can_coexist():
    amounts = model(0.2, 120000, 20000)
    explanation = interpret_control_case(
        amounts, assumed_effectiveness_pct=20, reviewer_decision=None
    )
    assert amounts["year_one_net_modeled_value_usd"] < 0
    assert amounts["discounted_net_modeled_value_usd"] > 0
    assert explanation["investment_signal"] == "CONDITIONAL POSITIVE"
    assert explanation["decision_status"] == "PENDING HUMAN REVIEW"
    assert "(negative)" in explanation["economic_interpretation"]
    assert "not a measured return" in explanation["economic_interpretation"]


def test_no_effectiveness_is_negative_and_no_return_claimed():
    amounts = model(0, 120000, 20000)
    explanation = interpret_control_case(
        amounts, assumed_effectiveness_pct=0, reviewer_decision="REJECTED"
    )
    assert amounts["modeled_annual_risk_reduction_usd"] == 0
    assert explanation["investment_signal"] == "CONDITIONAL NEGATIVE"
    assert explanation["decision_status"] == "RECOMMENDATION REVIEWED — REJECTED"


def test_favorable_year_one_still_needs_separate_authorization():
    amounts = model(0.65, 15000, 5000)
    explanation = interpret_control_case(
        amounts, assumed_effectiveness_pct=65, reviewer_decision="APPROVED"
    )
    assert "(positive)" in explanation["economic_interpretation"]
    assert "separate enterprise authorization" in explanation["next_action"]


@pytest.mark.parametrize("percent", [-1, 101, True])
def test_effectiveness_out_of_range_rejected(percent):
    with pytest.raises(ValueError):
        interpret_control_case(model(0.2, 10000, 5000),
                               assumed_effectiveness_pct=percent, reviewer_decision=None)


def test_disallowed_review_state_rejected():
    with pytest.raises(ValueError):
        interpret_control_case(model(0.2, 10000, 5000),
                               assumed_effectiveness_pct=20, reviewer_decision="EXECUTE_TRANSFER")
