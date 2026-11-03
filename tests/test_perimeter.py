"""Truth-preserving synthetic ledger and sovereign-policy boundary tests."""

from copy import deepcopy
from pathlib import Path

import pytest

from aegis_nhi.perimeter import reconcile_synthetic_ledger, replay_sovereign_routing
from aegis_nhi.workflow import load_case, run_case

CASE = Path(__file__).resolve().parents[1] / "data/scenarios/unauthorized_ai_agent.json"


@pytest.fixture
def scenario():
    return load_case(CASE)


def test_no_ledger_mutation_recorded_and_balances_reconcile(scenario):
    report = run_case(scenario)
    ledger = report["ledger_reconciliation"]
    assert ledger["basis"].startswith("synthetic")
    assert ledger["status"] == "RECONCILED"
    assert ledger["posting_count"] == 0
    assert ledger["posted_journal_value_usd"] == "0.00"
    assert ledger["opening_total_usd"] == ledger["closing_total_usd"]
    assert ledger["exception_count"] == 0
    assert len(ledger["consequential_action_requests"]) == 2


def test_detect_mismatch_between_opening_and_closing_balances(scenario):
    scenario = deepcopy(scenario)
    scenario["ledger"]["accounts"][0]["closing_balance_usd"] = "17999999.00"
    result = reconcile_synthetic_ledger(
        scenario, run_case(scenario)["authorization_decisions"]
    )
    assert result["status"] == "EXCEPTION"
    assert any(x["type"] == "LEDGER_ROLL_FORWARD_MISMATCH" for x in result["exceptions"])
    assert any(x["type"] == "LEDGER_TRIAL_BALANCE_MISMATCH" for x in result["exceptions"])


def test_blocked_transfer_cannot_be_silently_posted(scenario):
    scenario = deepcopy(scenario)
    scenario["ledger"]["postings"].append({
        "journal_id": "JRN-TEST-1",
        "event_id": "EVT-002",
        "debit_account": "clearing_reserve",
        "credit_account": "settlement_cash",
        "amount_usd": "100.00",
    })
    scenario["ledger"]["accounts"][0]["closing_balance_usd"] = "17999900.00"
    scenario["ledger"]["accounts"][1]["closing_balance_usd"] = "2100100.00"
    result = reconcile_synthetic_ledger(
        scenario, run_case(scenario)["authorization_decisions"]
    )
    assert result["status"] == "EXCEPTION"
    assert any(
        x["type"] == "UNAUTHORIZED_OR_BLOCKED_EVENT_POSTED"
        for x in result["exceptions"]
    )


def test_malformed_amount_and_duplicate_account_are_rejected(scenario):
    bad = deepcopy(scenario)
    bad["ledger"]["accounts"][0]["opening_balance_usd"] = "NaN"
    with pytest.raises(ValueError):
        reconcile_synthetic_ledger(bad, run_case(scenario)["authorization_decisions"])
    bad = deepcopy(scenario)
    bad["ledger"]["accounts"][1]["account_id"] = "settlement_cash"
    with pytest.raises(ValueError):
        reconcile_synthetic_ledger(bad, run_case(scenario)["authorization_decisions"])


def test_policy_replay_flags_nonapproved_export_destination(scenario):
    policy = replay_sovereign_routing(scenario)
    assert policy["approved_regions"] == ["US"]
    assert policy["outside_declared_boundary_count"] == 1
    assert policy["executed_outside_boundary_count"] == 0
    export = next(item for item in policy["events"] if item["event_id"] == "EVT-003")
    assert export["policy_replay"] == "DENY_REGION"
    assert export["observed_outcome"] == "blocked"


def test_declared_out_of_region_execution_is_detected(scenario):
    bad = deepcopy(scenario)
    bad["events"][2]["observed_outcome"] = "executed"
    policy = replay_sovereign_routing(bad)
    assert policy["executed_outside_boundary_count"] == 1
    assert policy["events"][2]["recorded_routing_control_failure"]


def test_missing_region_denied_in_synthetic_policy_replay(scenario):
    bad = deepcopy(scenario)
    del bad["events"][0]["declared_destination_region"]
    policy = replay_sovereign_routing(bad)
    assert policy["events"][0]["policy_replay"] == "DENY_REGION"


def test_no_real_ledger_or_route_is_claimed(scenario):
    result = run_case(scenario)
    assert "fictional" in result["ledger_reconciliation"]["limitations"]
    assert "Offline" in result["sovereign_routing"]["limitations"]
    assert all(item["read_only"] for item in result["tool_trace"])
    assert len(result["tool_trace"]) == 6
