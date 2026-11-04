"""Evidence-based acceptance tests for AEGIS-NHI v0.5 synthetic investigations."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from aegis_nhi.investigations import analyze_specialized_case
from aegis_nhi.narration import (
    claim_cards, narrate_evidence, narrate_with_optional_model, select_claim_ids,
)
from aegis_nhi.workflow import load_case, run_case

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/scenarios/sensitive_data_exposure.json"
SHADOW = ROOT / "data/scenarios/shadow_ai.json"
BANK = ROOT / "data/scenarios/unauthorized_ai_agent.json"


def test_two_new_scenarios_run_with_deterministic_case_provenance():
    for path, case_id in [(DATA, "BANK-DATA-003"), (SHADOW, "BANK-SHADOW-004")]:
        case = load_case(path)
        result = run_case(case)
        assert result == run_case(case)
        assert result["case_id"] == case_id
        assert result["status"] == "PENDING_HUMAN_REVIEW"
        assert len(result["agent_roles"]) == 3
        assert len(result["tool_trace"]) == 7
        assert all(entry["read_only"] for entry in result["tool_trace"])
        assert len(result["report_id"]) == 24
        assert result["scenario_findings"]["human_decision"] == "PENDING_HUMAN_REVIEW"
        assert result["evidence_narration"]["approval_status"] == "PENDING_HUMAN_REVIEW"
        assert result["financial_risk"]["basis"].startswith("hypothetical")


def test_sensitive_case_distinguishes_attempt_from_recorded_execution():
    result = run_case(load_case(DATA))
    findings = result["scenario_findings"]
    assert findings["flagged_event_count"] == 2
    assert findings["executed_flagged_event_count"] == 1
    assert findings["rule_finding_count"] == 3
    assert findings["policy_control_failure_count"] == 0
    assert result["sovereign_routing"]["executed_outside_boundary_count"] == 1
    assert {f["rule"] for f in findings["findings"]} == {
        "SENSITIVE_ACTION_ATTEMPT", "SENSITIVE_REGION_OUT_OF_POLICY"
    }
    exported = [f for f in findings["findings"] if f["rule"] == "SENSITIVE_ACTION_ATTEMPT"]
    assert len(exported) == 1 and exported[0]["observed_outcome"] == "blocked"
    assert exported[0]["evidence_ids"] == ["DE-002"]


def test_shadow_case_detects_unregistered_identity_and_tools_separately():
    result = run_case(load_case(SHADOW))
    findings = result["scenario_findings"]
    assert findings["flagged_event_count"] == 3
    assert findings["executed_flagged_event_count"] == 1
    assert findings["rule_finding_count"] == 5
    assert findings["policy_control_failure_count"] == 0
    assert {f["rule"] for f in findings["findings"]} == {
        "UNREGISTERED_AI_IDENTITY", "UNREGISTERED_AI_TOOL"
    }
    approved_but_unregistered = [
        f for f in findings["findings"] if f["event_id"] == "SHADOW-003"
    ]
    assert len(approved_but_unregistered) == 1
    assert approved_but_unregistered[0]["policy_authorized"]
    assert approved_but_unregistered[0]["observed_executed"]


def test_bad_data_policy_rejected_fail_closed():
    case = load_case(DATA)
    case["data_controls"]["resource_classifications"].pop("customers.restricted")
    with pytest.raises(ValueError, match="Unclassified resource"):
        run_case(case)
    case = load_case(DATA)
    case["data_controls"]["approved_processing_regions"] = ["US", "US"]
    with pytest.raises(ValueError, match="unique"):
        run_case(case)


def test_missing_shadow_tool_id_rejected():
    case = load_case(SHADOW)
    case["events"][1].pop("tool_id")
    with pytest.raises(ValueError, match="tool ID"):
        run_case(case)


def test_specialized_analysis_requires_authorization_replay():
    case = load_case(DATA)
    with pytest.raises(ValueError, match="cover all events"):
        analyze_specialized_case(case, [])


def test_control_sensitivity_never_mutates_recorded_events_or_findings():
    case = load_case(DATA)
    before = deepcopy(case)
    a = run_case(case)
    b = run_case(case, hypothetical_control_effectiveness=0.45)
    assert a["report_id"] != b["report_id"]
    assert a["authorization_decisions"] == b["authorization_decisions"]
    assert a["scenario_findings"] == b["scenario_findings"]
    assert case == before


def test_existing_banking_case_preserves_six_tool_invocations():
    result = run_case(load_case(BANK))
    assert result["scenario_findings"] is None
    assert len(result["tool_trace"]) == 6
    assert result["evidence_narration"]["selection_mode"] == "deterministic_claim_selection"


def test_claim_cards_separate_fixture_evidence_from_financial_assumptions():
    report = run_case(load_case(SHADOW))
    cards = claim_cards(report)
    by_id = {c["id"]: c for c in cards}
    assert by_id["specialized"]["evidence_ids"]
    assert by_id["risk"]["evidence_ids"] == []
    assert by_id["risk"]["assumption_source"] == report["provenance"]["case_sha256"]
    assert "not observed loss" in by_id["risk"]["text"].lower()
    assert "PENDING_HUMAN_REVIEW" == narrate_evidence(report)["approval_status"]


@pytest.mark.parametrize("bad", [
    "write a fake claim",
    json.dumps({"selected_claim_ids": ["risk"], "operational_approval": True}),
    json.dumps({"selected_claim_ids": ["unauthorized_action"]}),
    json.dumps({"selected_claim_ids": ["case", "case"]}),
    json.dumps({"selected_claim_ids": []}),
    json.dumps({"selected_claim_ids": [1]}),
])
def test_unverified_model_claims_fail_closed(bad):
    with pytest.raises(ValueError):
        select_claim_ids(bad, ["case", "risk"])


def test_bounded_model_can_only_choose_predefined_verified_text():
    report = run_case(load_case(DATA))
    calls = []
    def fake_create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps({
            "selected_claim_ids": ["case", "specialized", "disposition"]
        }))
    client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    narrative = narrate_with_optional_model(report, client=client)
    assert len(calls) == 1
    assert calls[0]["max_output_tokens"] == 180
    assert narrative["selection_mode"] == "bounded_model_claim_selection"
    assert narrative["claims"] == [
        c for c in claim_cards(report) if c["id"] in
        {"case", "specialized", "disposition"}
    ]
    assert all(c["text"] in narrative["narrative"] for c in narrative["claims"])
    assert "actual" not in narrative["limitations"].lower()


def test_tool_budget_and_mutations_remain_denied():
    with pytest.raises(RuntimeError, match="budget exhausted"):
        run_case(load_case(SHADOW), tool_budget=6)
