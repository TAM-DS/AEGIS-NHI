"""Bounded and reproducible autonomous-agent forensic incident analysis."""

from copy import deepcopy
from pathlib import Path

import pytest

from aegis_nhi.forensics import analyze_forensics, load_forensics_case, validate_forensics

CASE_PATH = Path(__file__).resolve().parents[1] / "data/scenarios/runaway_agent.json"


@pytest.fixture
def case():
    return load_forensics_case(CASE_PATH)


def test_runaway_incident_triggers_three_evidence_linked_findings(case):
    r = analyze_forensics(case)
    assert r["case_id"] == "BANK-FINOPS-002"
    assert r["tool_calls"] == 600
    assert r["baseline_calls_per_workflow"] == 12
    assert r["amplification_factor"] == 50
    assert r["peak_calls_per_minute"] == 170
    assert r["repeated_signature_share_pct"] == 95.0
    assert r["status"] == "ANOMALOUS_SYNTHETIC_ACTIVITY"
    assert r["first_burst_alert_minute"] == 1
    assert r["first_budget_alert_minute"] == 2
    assert [a["rule"] for a in r["alerts"]] == [
        "SUSTAINED_TOOL_CALL_BURST",
        "WORKFLOW_CALL_BUDGET_EXCEEDED",
        "REPEATED_TOOL_SIGNATURE_CONCENTRATION",
    ]
    assert all(a["evidence_ids"] for a in r["alerts"])
    assert r["recorded_authorization_failures"] == 0


def test_counts_and_cost_estimates_reconcile_without_double_count(case):
    report = analyze_forensics(case)
    assert sum(p["tool_calls"] for p in report["timeline"]) == 600
    assert report["synthetic_metered_input_tokens"] == 1000000
    assert report["synthetic_metered_output_tokens"] == 441000
    assert report["hypothetical_incurred_token_cost_usd"] == pytest.approx(5.528)
    assert report["hypothetical_incurred_gpu_cost_usd"] == pytest.approx(1.2)
    assert "MUST NOT be added" in report["economics_basis"]
    assert "combined_total" not in report
    assert "total_charges" not in report


def test_forecast_is_incremental_and_sensitivity_changes_only_prices(case):
    base = analyze_forensics(case, projection_hours=1, token_rate_multiplier=1)
    higher = analyze_forensics(case, projection_hours=2, token_rate_multiplier=2)
    assert base["projection"]["additional_tool_calls"] == 6000
    assert higher["projection"]["additional_tool_calls"] == 12000
    assert higher["projection"]["additional_token_cost_usd"] == pytest.approx(
        base["projection"]["additional_token_cost_usd"] * 4
    )
    assert higher["projection"]["additional_gpu_cost_usd"] == pytest.approx(
        base["projection"]["additional_gpu_cost_usd"] * 2
    )
    assert base["tool_calls"] == higher["tool_calls"]
    assert base["alerts"] == higher["alerts"]
    assert base["report_id"] != higher["report_id"]


def test_hypothetical_budget_override_changes_detection_but_not_event_data(case):
    permissive = analyze_forensics(case, workflow_call_limit=650)
    restrictive = analyze_forensics(case, workflow_call_limit=50)
    assert permissive["first_budget_alert_minute"] is None
    assert restrictive["first_budget_alert_minute"] == 1
    assert permissive["tool_calls"] == restrictive["tool_calls"] == 600
    assert "SUSTAINED_TOOL_CALL_BURST" in [a["rule"] for a in permissive["alerts"]]


def test_normal_workflow_produces_no_anomaly_alert(case):
    normal = deepcopy(case)
    for row in normal["minute_buckets"]:
        row["tool_calls"] = 2
        row["repeated_signature_calls"] = 0
        row["input_tokens"] = 1500
        row["output_tokens"] = 500
    r = analyze_forensics(normal)
    assert r["tool_calls"] == 12
    assert r["status"] == "NO_RULE_TRIGGER"
    assert r["alerts"] == []
    assert r["recorded_authorization_failures"] == 0


def test_synthetic_unauthorized_tool_execution_is_separate_alert(case):
    modified = deepcopy(case)
    modified["grant"]["allowed_actions"] = ["something_else"]
    result = analyze_forensics(modified)
    assert result["recorded_authorization_failures"] == 6
    assert any(a["rule"] == "RECORDED_UNAUTHORIZED_EXECUTION" for a in result["alerts"])
    assert "No automatic" in result["human_decision"] or "NO automatic" in result["human_decision"]


@pytest.mark.parametrize("hours,multiplier,limit", [
    (0, 1, None), (25, 1, None), (True, 1, None),
    (1, -1, None), (1, float("nan"), None),
    (1, 1, 0), (1, 1, True),
])
def test_out_of_range_settings_fail_closed(case, hours, multiplier, limit):
    with pytest.raises(ValueError):
        analyze_forensics(case, projection_hours=hours,
                         token_rate_multiplier=multiplier, workflow_call_limit=limit)


def test_non_synthetic_case_rejected(case):
    case["synthetic"] = False
    with pytest.raises(ValueError, match="Only synthetic"):
        analyze_forensics(case)


def test_unknown_evidence_and_reversed_minute_order_rejected(case):
    modified = deepcopy(case)
    modified["minute_buckets"][3]["evidence_ids"] = ["MISSING"]
    with pytest.raises(ValueError, match="unknown evidence"):
        validate_forensics(modified)
    modified = deepcopy(case)
    modified["minute_buckets"][3]["minute"] = 2
    with pytest.raises(ValueError, match="contiguous"):
        validate_forensics(modified)


def test_invalid_metering_and_duplicate_evidence_rejected(case):
    modified = deepcopy(case)
    modified["minute_buckets"][0]["repeated_signature_calls"] = 19
    with pytest.raises(ValueError, match="Repeated calls"):
        analyze_forensics(modified)
    modified = deepcopy(case)
    modified["minute_buckets"][1]["input_tokens"] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        analyze_forensics(modified)
    modified = deepcopy(case)
    modified["evidence"].append(modified["evidence"][0])
    with pytest.raises(ValueError, match="duplicated"):
        analyze_forensics(modified)


def test_result_is_deterministic_and_identity_policy_traced(case):
    report_a = analyze_forensics(case)
    report_b = analyze_forensics(case)
    assert report_a == report_b
    assert len(report_a["timeline"]) == 6
    assert all(bucket["policy_authorized"] for bucket in report_a["timeline"])
    assert all(bucket["evidence_ids"] for bucket in report_a["timeline"])
    assert report_a["execution_boundary"] == "OFFLINE_SYNTHETIC_READ_ONLY"
