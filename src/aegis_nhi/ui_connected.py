"""Analyst-facing view of one fictional connected investigation."""
import json

import streamlit as st

from .connected_investigation import build_connected_investigation
from .workflow import load_case


def render_connected(root):
    st.subheader("Connected investigation · Shadow AI")
    st.caption("SYNTHETIC · READ ONLY · HUMAN DECISION REQUIRED")
    st.write("Follow an agent request through its declared session, host observation, policy result and original evidence.")
    try:
        case = load_case(root / "data/scenarios/shadow_ai.json")
        telemetry = json.loads((root / "data/connected/shadow_sessions.json").read_text())
        report = build_connected_investigation(case, telemetry)
    except (ValueError, KeyError, TypeError, OSError):
        st.error("Connected investigation rejected: source or relationship validation failed.")
        return
    a, b, c = st.columns(3)
    a.metric("Declared sessions", report["session_count"])
    b.metric("Host observations", report["host_observation_count"])
    c.metric("Events without a session", len(report["unassigned_event_ids"]))
    st.info("Connections are explicitly declared in fictional fixtures. Shared timing or labels do not establish causality. No live security feeds are connected.")
    event_id = st.selectbox("Trace an event", [e["event_id"] for e in case["events"]], key="connected_event")
    focus = case["case_id"] + "/event/" + event_id
    selected = {focus}
    for _ in range(2):
        neighbors = set(selected)
        for edge in report["edges"]:
            if edge["source"] in selected or edge["target"] in selected:
                neighbors.update((edge["source"], edge["target"]))
        selected = neighbors
    nodes = [n for n in report["nodes"] if n["id"] in selected]
    edges = [e for e in report["edges"] if e["source"] in selected and e["target"] in selected]
    st.caption("Two-hop evidence neighborhood. Neighboring events provide context, not proof of a causal chain.")
    dot = ["digraph investigation {", 'rankdir="TB";']
    for node in nodes:
        label = node["type"] + ": " + node["label"]
        dot.append(json.dumps(node["id"]) + " [label=" + json.dumps(label) + "];")
    for edge in edges:
        dot.append(json.dumps(edge["source"]) + " -> " + json.dumps(edge["target"]) + " [label=" + json.dumps(edge["relation"]) + "];")
    st.graphviz_chart("\n".join(dot + ["}"]))
    decision = next(d for d in report["authorization_decisions"] if d["event_id"] == event_id)
    st.markdown("#### Selected request · policy and recorded outcome")
    st.json(decision, expanded=True)
    findings = [f for f in report["scenario_findings"]["findings"] if f["event_id"] == event_id]
    st.write("Specialized policy findings", findings)
    st.dataframe(edges, hide_index=True, width="stretch")
    with st.expander("Inspect original evidence and declared telemetry"):
        event = next(e for e in case["events"] if e["event_id"] == event_id)
        st.json({"event": event, "source_evidence": [e for e in case["evidence"] if e["evidence_id"] in event["evidence_ids"]],
                 "telemetry": telemetry, "case_sha256": report["case_sha256"], "telemetry_sha256": report["telemetry_sha256"]})
    st.markdown("#### Financial context · whole case, not the selected event")
    cost, exposure = st.columns(2)
    cost.metric("Fictional fixture charges", f"${report['fixture_runtime_cost']['synthetic_tool_cost_usd']:.3f}")
    exposure.metric("Modeled annual exposure", f"${report['hypothetical_annual_exposure']['expected_annual_loss_usd']:,.0f}")
    st.caption("Fixture charges are invented incident-window costs. Annual exposure is a separate conditional model, not a bill, observed loss or prevented loss. Do not add these figures.")
    with st.expander("Inspect annual exposure assumptions"):
        st.json(report["hypothetical_annual_exposure"])
    st.warning("Human decision: evaluate the unregistered-tool evidence and source quality. This view cannot approve remediation or change a connected system.")
    st.download_button("Download connected investigation", json.dumps(report, indent=2),
                       file_name="shadow-connected-investigation.json", mime="application/json", key="connected_download")
