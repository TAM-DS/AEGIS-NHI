"""Five-view synthetic and read-only AEGIS-NHI executive risk dashboard."""

import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from aegis_nhi.review import add_review, get_reviews
from aegis_nhi.workflow import load_case, run_case

ROOT = Path(__file__).resolve().parent
CASE = load_case(ROOT / "data/scenarios/unauthorized_ai_agent.json")
REVIEWS = ROOT / ".aegis/reviews.sqlite3"


def money(value):
    return "$" + format(value, ",.0f")


st.set_page_config(page_title="AEGIS-NHI · Executive Risk", page_icon="🛡️", layout="wide")
st.markdown(
    """
<style>
.stApp {background:linear-gradient(155deg,#0e1729,#182e4c 60%,#101b32);}
[data-testid="stMetric"] {background:#213851;border:1px solid #476481;padding:16px;border-radius:14px;}
[data-testid="stMetricLabel"] {color:#b6d1ee;}
[data-testid="stMetricValue"] {color:#eff8ff;}
</style>
    """, unsafe_allow_html=True
)

with st.sidebar:
    st.title("🛡️ AEGIS-NHI")
    st.caption("THE BEAST · RESEARCH BUILD")
    st.divider()
    st.markdown("**Hypothetical risk sensitivity**")
    freq = st.slider("Assumed frequency multiplier", 0.5, 2.0, 1.0, 0.1)
    control = st.slider("Assumed added control effectiveness (%)", 0, 80, 0, 5)
    st.caption("Inputs affect modeled risk, not source evidence.")
    st.divider()
    st.caption("SYNTHETIC · READ-ONLY · NO LIVE BANK ACCESS")

report = run_case(CASE, frequency_multiplier=freq, hypothetical_control_effectiveness=control / 100)
rows = report["authorization_decisions"]
risk = report["financial_risk"]
runtime = report["runtime_metrics"]
brief = report["executive_brief"]

st.caption("AUTONOMOUS CHIEF RISK OFFICER / GOVERNED DECISION INTELLIGENCE")
st.title("AEGIS-NHI · Executive Risk Command Center")
st.markdown("**Identity. Authority. Exposure. Evidence.**")
st.warning(
    "SYNTHETIC PORTFOLIO DEMO. All events, grants and costs are fictional. "
    "Financial risk is hypothetical and conditional; no actual or prevented loss is claimed.",
    icon="🧪",
)

overview, nhi, finops, quant, decisions = st.tabs(
    ["🏛️ Executive Overview", "🔐 NHI & Agent Controls", "⚡ FinOps & Agents",
     "📈 Cyber Risk Quantification", "📋 Decision & Evidence"]
)
with overview:
    st.subheader(CASE["title"])
    st.caption(CASE["scenario_context"])
    a, b, c, d = st.columns(4)
    a.metric("Tool requests", len(rows))
    b.metric("Policy denials", sum(not r["authorized"] for r in rows))
    c.metric("Control failures", sum(r["control_failure"] for r in rows))
    d.metric("Hypothetical annual exposure", money(risk["expected_annual_loss_usd"]))
    st.markdown("### Executive finding")
    st.info(brief["finding"], icon="🛡️")
    st.markdown("### Recommendation pending human review")
    st.write(brief["recommendation"])
    st.caption(
        "An approval is review of a recommendation only; it grants no permission "
        "to transfer funds, modify bank IAM or perform remediation."
    )
    with st.expander("Interpretation limitations"):
        st.write(
            "The fixture records one authorized read and three blocked requests. "
            "The annual loss model is a counterfactual future scenario if controls fail, "
            "NOT a dollar estimate of these blocked attempts."
        )

with nhi:
    st.subheader("Scoped non-human identity authorization replay")
    st.dataframe(
        [
            {
                "Event": r["event_id"], "Identity": r["identity_id"],
                "Resource": r["resource_id"], "Action": r["requested_action"],
                "Recorded outcome": r["observed_outcome"].upper(),
                "Policy decision": "ALLOW" if r["authorized"] else "DENY",
                "Reason": r["reason"], "Control failure": r["control_failure"],
                "Evidence": ", ".join(r["evidence_ids"]),
            }
            for r in rows
        ], use_container_width=True, hide_index=True
    )
    x, y = st.columns(2)
    with x:
        st.markdown("**Synthetic scoped grant**")
        st.json(CASE["grants"], expanded=False)
    with y:
        st.markdown("**Control rule**")
        st.write(
            "Identity, resource, requested action, active event-time interval "
            "and grant approver must match. Capability alone does not confer authority."
        )
    st.caption("Retrospective fixture replay; not a production access-control gate.")

with finops:
    st.subheader("Bounded agent workflow and synthetic runtime costs")
    a, b, c = st.columns(3)
    a.metric("Fixture executions", runtime["recorded_executions"])
    b.metric("Fixture blocks", runtime["recorded_blocks"])
    c.metric("Synthetic tool charges", "$" + format(runtime["synthetic_tool_cost_usd"], ",.3f"))
    st.caption(
        "Synthetic fixture charges are not billed cloud costs and must NOT be added "
        "to hypothetical annual loss exposure."
    )
    st.markdown("**Three deterministic workflow roles**")
    st.write("FinOps Auditor · Risk Actuary · Executive Reporter")
    st.dataframe(
        [
            {
                "Agent": t["agent_role"], "Read-only tool": t["tool"],
                "SHA-256 output": t["output_sha256"][:22] + "…",
            }
            for t in report["tool_trace"]
        ], use_container_width=True, hide_index=True
    )
    st.caption(
        str(len(report["tool_trace"])) + " / " + str(report["tool_budget"])
        + " permitted calls. No LLM, network, payments or remediation tools."
    )

with quant:
    st.subheader("Conditional annual loss modeling")
    a, b, c, d = st.columns(4)
    a.metric("Expected annual loss", money(risk["expected_annual_loss_usd"]))
    b.metric("P10 outcome", money(risk["p10_annual_loss_usd"]))
    c.metric("P50 outcome", money(risk["p50_annual_loss_usd"]))
    d.metric("P90 outcome", money(risk["p90_annual_loss_usd"]))
    values = [
        risk["p10_annual_loss_usd"],
        risk["p50_annual_loss_usd"],
        risk["p90_annual_loss_usd"],
    ]
    fig = go.Figure(go.Bar(
        x=["P10", "P50", "P90"], y=values,
        marker_color=["#3ba8e3", "#61c6b4", "#f7b465"],
        text=[money(v) for v in values], textposition="outside",
    ))
    fig.update_layout(
        title="Simulated annual outcome quantiles",
        yaxis_title="USD · hypothetical annual loss",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#dce9fc", height=390, showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Model assumptions and provenance", expanded=True):
        st.json({
            "annual_event_frequency_assumption": risk["annual_event_frequency_assumption"],
            "loss_min_usd": risk["loss_min_usd"], "loss_mode_usd": risk["loss_mode_usd"],
            "loss_max_usd": risk["loss_max_usd"], "simulations": risk["simulations"],
            "seed": risk["seed"], "model_version": risk["model_version"],
            "basis": risk["basis"],
        }, expanded=False)
        st.caption(risk["limitations"])
        st.caption("Quantiles describe outcomes, not statistical confidence intervals.")

with decisions:
    st.subheader("Evidence and human decision room")
    st.info(brief["recommendation"], icon="📌")
    st.caption("Report identity: " + report["report_id"])
    history = get_reviews(REVIEWS, report["report_id"])
    if history:
        st.success("Latest human review: " + history[0]["decision"] + " · " + history[0]["reviewer"])
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.warning("No review yet for this exact report and model sensitivity.")
    with st.form("review_form"):
        reviewer = st.text_input("Named human reviewer")
        reason = st.text_area("Required decision rationale")
        yes, no = st.columns(2)
        approved = yes.form_submit_button("Approve recommendation")
        rejected = no.form_submit_button("Reject recommendation")
        if approved or rejected:
            try:
                add_review(
                    REVIEWS, report["report_id"],
                    "APPROVED" if approved else "REJECTED", reviewer, reason
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("Review recorded locally; NO operational action executed.")
                st.rerun()
    st.markdown("#### Evidence cards")
    for item in report["evidence"]:
        with st.expander(item["evidence_id"] + " · " + item["kind"]):
            st.write(item["description"])
    st.download_button(
        "Download synthetic evidence report",
        json.dumps(report, indent=2),
        file_name="BANK-NHI-001-evidence.json", mime="application/json",
    )
    st.caption("Provenance and hashes are in the JSON. Human review ledger is separate.")

st.divider()
st.caption(
    "AEGIS-NHI v0.1.0 · Research prototype · Synthetic evidence and modeled financial "
    "risk · Not a deployed autonomous CRO or production bank control."
)
