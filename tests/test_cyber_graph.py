"""Verified fixture relationships; no invented cross-case joins."""
from copy import deepcopy
from pathlib import Path
import pytest

from aegis_nhi.cyber_graph import build_case_graph, verify_case_graph
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


@pytest.mark.parametrize("filename", [
    "unauthorized_ai_agent.json", "sensitive_data_exposure.json", "shadow_ai.json",
])
def test_export_verifies_against_selected_source(filename):
    case = load_case(ROOT / filename)
    verify_case_graph(case, build_case_graph(case))


@pytest.mark.parametrize("mutation", ["edge", "source", "authority", "count", "extra"])
def test_tampered_export_rejected_even_if_hash_recomputed(mutation):
    import hashlib
    import json
    case = load_case(ROOT / "shadow_ai.json")
    graph = build_case_graph(case)
    if mutation == "edge":
        graph["edges"].pop()
    elif mutation == "source":
        graph["source_case_sha256"] = "0" * 64
    elif mutation == "authority":
        graph["approval_status"] = "AUTHORIZED"
    elif mutation == "count":
        graph["counts"]["recorded_blocks"] = True
    else:
        graph["unverified_claim"] = "real incident"
    graph.pop("graph_sha256")
    graph["graph_sha256"] = hashlib.sha256(
        json.dumps(graph, sort_keys=True).encode("utf-8")
    ).hexdigest()
    with pytest.raises(ValueError, match="does not match"):
        verify_case_graph(case, graph)


def test_export_from_other_case_rejected():
    case = load_case(ROOT / "shadow_ai.json")
    other = load_case(ROOT / "sensitive_data_exposure.json")
    with pytest.raises(ValueError, match="does not match"):
        verify_case_graph(case, build_case_graph(other))


@pytest.mark.parametrize("bad", [None, [], {"counts": float("nan")}])
def test_invalid_graph_export_rejected(bad):
    case = load_case(ROOT / "shadow_ai.json")
    with pytest.raises(ValueError):
        verify_case_graph(case, bad)


def test_forensics_fixture_requires_explicit_adapter():
    import json
    case = json.loads((ROOT / "runaway_agent.json").read_text())
    with pytest.raises(ValueError, match="required evidence"):
        build_case_graph(case)


def test_cli_verifies_export_and_rejects_modified_export(tmp_path):
    import json
    import subprocess
    import sys
    target = tmp_path / "graph.json"
    command = [
        sys.executable, "-m", "aegis_nhi.cyber_graph",
        "--scenario", str(ROOT / "shadow_ai.json"),
    ]
    exported = subprocess.run(
        command + ["--output", str(target)], capture_output=True, text=True
    )
    assert exported.returncode == 0, exported.stderr
    verified = subprocess.run(
        command + ["--verify", str(target)], capture_output=True, text=True
    )
    assert verified.returncode == 0, verified.stderr
    assert "no action authorized" in verified.stdout
    graph = json.loads(target.read_text())
    graph["edges"].pop()
    target.write_text(json.dumps(graph))
    rejected = subprocess.run(
        command + ["--verify", str(target)], capture_output=True, text=True
    )
    assert rejected.returncode != 0
    assert "does not match" in rejected.stderr
