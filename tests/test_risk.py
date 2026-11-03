from copy import deepcopy
from pathlib import Path
import pytest
from aegis_nhi.risk import quantify_annual_loss
from aegis_nhi.workflow import load_case

FIXTURE = Path(__file__).resolve().parents[1] / "data/scenarios/unauthorized_ai_agent.json"

@pytest.fixture
def params():
    return load_case(FIXTURE)["annual_loss_model"]

def test_seeded_model_is_repeatable(params):
    a = quantify_annual_loss(params)
    b = quantify_annual_loss(params)
    assert a == b
    assert a["p10_annual_loss_usd"] <= a["p50_annual_loss_usd"]
    assert a["p50_annual_loss_usd"] <= a["p90_annual_loss_usd"]
    assert a["seed"] == 1701
    assert a["simulations"] == 5000

def test_analytical_loss_is_hypothetical(params):
    result = quantify_annual_loss(params)
    assert result["expected_annual_loss_usd"] == round(1.7 * (80000 + 200000 + 900000) / 3, 2)
    assert result["basis"].startswith("hypothetical")
    assert result["currency"] == "USD"

def test_hypothetically_perfect_control_makes_zero_losses(params):
    result = quantify_annual_loss(params, hypothetical_control_effectiveness=1.0)
    assert result["expected_annual_loss_usd"] == 0
    assert result["p90_annual_loss_usd"] == 0

def test_invalid_inputs_fail(params):
    bad = deepcopy(params)
    bad["loss_mode_usd"] = bad["loss_max_usd"] + 1
    with pytest.raises(ValueError):
        quantify_annual_loss(bad)
    with pytest.raises(ValueError):
        quantify_annual_loss(params, frequency_multiplier=-1)
    with pytest.raises(ValueError):
        quantify_annual_loss(params, hypothetical_control_effectiveness=1.01)
    bad["loss_mode_usd"] = 200000
    bad["simulations"] = 100000
    with pytest.raises(ValueError):
        quantify_annual_loss(bad)

def test_sensitivity_does_not_mutate_input(params):
    original = deepcopy(params)
    result = quantify_annual_loss(params, frequency_multiplier=1.5, hypothetical_control_effectiveness=0.5)
    assert params == original
    assert result["annual_event_frequency_assumption"] == pytest.approx(1.275)
