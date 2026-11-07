"""Verified fixture relationships; no invented cross-case joins."""
from copy import deepcopy
from pathlib import Path
import pytest

from aegis_nhi.cyber_graph import build_case_graph
from aegis_nhi.workflow import load_case

ROOT = Path(__file__).resolve().parents[1] / "data" / "scenarios"


@pytest.mark.parametrize("filename", [
    "unauthorized_ai_agent.json", "sensitive_data_exposure.json", "shadow_ai.json",
])
def test_case_graph_is_deterministic_and_self_contained(filename):
    case = load_case(ROOT / filename)
    graph = build_case_graph(case)
    assert graph == build_case_graph(case)
    assert graph["synthetic"] is True
    assert graph["approval_status"] == "NOT_AUTHORIZED_FOR_ACTION"
    assert graph["counts"]["recorded_blocks"] + graph["counts"]["recorded_executions"] == len(case["events"])
    node_ids = {node["id"] for node in graph["nodes"]}
    assert len(node_ids) == len(graph["nodes"])
    assert all(key.startswith(case["case_id"] + "/") for key in node_ids)
    assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in graph["edges"])
    assert graph["graph_sha256"]


def test_sensitive_region_exception_is_not_mislabeled_as_exfiltration():
    case = load_case(ROOT / "sensitive_data_exposure.json")
    graph = build_case_graph(case)
    flagged = [node for node in graph["nodes"] if node["type"] == "finding"]
    assert any(
        x["rule"] == "SENSITIVE_REGION_OUT_OF_POLICY" and x["observed_executed"]
        for x in flagged
    )
    assert any(
        node["label"] == "DATA-002" and node["observed_outcome"] == "blocked"
        for node in graph["nodes"] if node["type"] == "event"
    )
    assert not any("real_breach" in node for node in graph["nodes"])


def test_shadow_tool_independent_of_grant_and_outcome():
    case = load_case(ROOT / "shadow_ai.json")
    graph = build_case_graph(case)
    findings = [node for node in graph["nodes"] if node["type"] == "finding"]
    assert any(x["rule"] == "UNREGISTERED_AI_TOOL" and x["observed_executed"] for x in findings)
    tools = [node for node in graph["nodes"] if node["type"] == "tool"]
    assert {x["label"] for x in tools} == {"internal.reporting", "unapproved.vendor-llm"}


def test_unknown_evidence_fails_before_graph_created():
    case = deepcopy(load_case(ROOT / "sensitive_data_exposure.json"))
    case["events"][0]["evidence_ids"] = ["MISSING"]
    with pytest.raises(ValueError, match="Unknown event evidence"):
        build_case_graph(case)


def test_duplicate_event_ids_fail_closed():
    case = deepcopy(load_case(ROOT / "shadow_ai.json"))
    case["events"][1]["event_id"] = case["events"][0]["event_id"]
    with pytest.raises(ValueError, match="Duplicate event"):
        build_case_graph(case)
