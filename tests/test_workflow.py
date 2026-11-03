from copy import deepcopy
from pathlib import Path
import pytest
from aegis_nhi.workflow import ToolLedger, load_case, run_case

FIXTURE = Path(__file__).resolve().parents[1] / "data/scenarios/unauthorized_ai_agent.json"

@pytest.fixture
def case():
    return load_case(FIXTURE)

def test_complete_deterministic_case(case):
    r = run_case(case)
    assert r == run_case(case)
    assert r["status"] == "PENDING_HUMAN_REVIEW"
    assert r["executive_brief"]["denied_count"] == 3
    assert r["executive_brief"]["policy_control_failures"] == 0
    assert r["runtime_metrics"]["synthetic_tool_cost_usd"] == 0.016
    assert len(r["tool_trace"]) == 4
    assert len(r["agent_roles"]) == 3
    assert len(r["report_id"]) == 24
    assert len(r["executive_brief"]["evidence_ids"]) == 4

def test_budget_fails_closed(case):
    with pytest.raises(RuntimeError, match="budget exhausted"):
        run_case(case, tool_budget=3)

def test_mutating_tool_never_invoked():
    ledger = ToolLedger()
    touched = []
    with pytest.raises(PermissionError, match="Non-allowlisted"):
        ledger.invoke("FinOps Auditor", "send_payment", lambda: touched.append(True))
    assert not touched
    assert ledger.calls == []

def test_unresolved_evidence_reference_rejected(case):
    broken = deepcopy(case)
    broken["events"][0]["evidence_ids"] = ["FAKE"]
    with pytest.raises(ValueError, match="Unknown event evidence"):
        run_case(broken)

def test_nonsynthetic_and_negative_costs_rejected(case):
    broken = deepcopy(case)
    broken["synthetic"] = False
    with pytest.raises(ValueError, match="explicitly synthetic"):
        run_case(broken)
    broken = deepcopy(case)
    broken["events"][0]["synthetic_tool_cost_usd"] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        run_case(broken)

def test_model_sensitivity_preserves_source_evidence(case):
    baseline = run_case(case)
    changed = run_case(case, hypothetical_control_effectiveness=0.5)
    assert baseline["report_id"] != changed["report_id"]
    assert baseline["authorization_decisions"] == changed["authorization_decisions"]
    assert baseline["runtime_metrics"] == changed["runtime_metrics"]

def test_observed_vs_hypothetical_are_not_added(case):
    report = run_case(case)
    assert report["runtime_metrics"]["basis"] == "synthetic_observed_fixture"
    assert report["financial_risk"]["basis"].startswith("hypothetical")
    assert "combined_total" not in report
