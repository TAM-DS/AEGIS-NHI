from copy import deepcopy
from pathlib import Path
import pytest
from aegis_nhi.authorization import evaluate_event, evaluate_events
from aegis_nhi.workflow import load_case

FIXTURE = Path(__file__).resolve().parents[1] / "data/scenarios/unauthorized_ai_agent.json"

@pytest.fixture
def case():
    return load_case(FIXTURE)

def test_expected_policy_decisions(case):
    results = evaluate_events(case["events"], case["grants"])
    assert [item["authorized"] for item in results] == [True, False, False, False]
    assert [item["reason"] for item in results] == [
        "ALLOW_SCOPED_RUNTIME_GRANT",
        "DENY_RESOURCE_OUT_OF_SCOPE",
        "DENY_ACTION_NOT_GRANTED",
        "DENY_GRANT_NOT_ACTIVE",
    ]
    assert all(not item["control_failure"] for item in results)

def test_missing_identity_denied(case):
    event = dict(case["events"][0], identity_id="unknown-agent")
    result = evaluate_event(event, case["grants"])
    assert result["reason"] == "DENY_NO_IDENTITY_GRANT"
    assert not result["authorized"]

def test_unapproved_grant_denied(case):
    grant = dict(case["grants"][0], approved_by="")
    assert evaluate_event(case["events"][0], [grant])["reason"] == "DENY_UNAPPROVED_GRANT"

def test_executed_denial_is_control_failure(case):
    event = dict(case["events"][1], observed_outcome="executed")
    result = evaluate_event(event, case["grants"])
    assert result["control_failure"] is True
    assert result["authorized"] is False

def test_naive_event_time_rejected(case):
    event = dict(case["events"][0], occurred_at="2026-10-22T14:02:00")
    with pytest.raises(ValueError, match="Naive"):
        evaluate_event(event, case["grants"])

def test_no_inferred_transfer_privilege(case):
    modified = deepcopy(case)
    event = dict(modified["events"][0], requested_action="initiate_transfer")
    assert not evaluate_event(event, modified["grants"])["authorized"]
