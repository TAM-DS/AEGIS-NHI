"""A live Streamlit investigation view over synthetic, read-only agent telemetry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from .forensics import analyze_forensics, load_forensics_case
from .review import add_review, get_reviews


def _usd(value: float, digits: int = 2) -> str:
    return "$" + format(value, f",.{digits}f")


def _styling(figure: go.Figure, height: int = 365) -> go.Figure:
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e7f4ff", size=12),
        margin=dict(l=20, r=20, t=45, b=30),
        height=height,
        hovermode="x unified",
        legend=dict(orientation="h", y=1.18, x=0),
    )
    figure.update_xaxes(showgrid=False, linecolor="#44617a", title="Minute since start")
    figure.update_yaxes(gridcolor="rgba(120,162,200,.17)", title="Tool calls")
    return figure


def _call_chart(timeline: list[dict[str, Any]]) -> go.Figure:
    minutes = [t["minute"] for t in timeline]
    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=minutes,
        y=[t["cumulative_calls"] for t in timeline],
        name="Synthetic recorded cumulative calls",
        mode="lines+markers",
        line=dict(color="#53d4ef", width=4),
        marker=dict(size=10),
    ))
    figure.add_trace(go.Scatter(
        x=minutes,
        y=[(t["minute"] + 1) * t["normal_calls_per_minute"] for t in timeline],
        name="Normal baseline if sustained",
        mode="lines+markers",
        line=dict(color="#50c7ac", width=2, dash="dash"),
    ))
    return _styling(figure, 385)


def _repetition_chart(timeline: list[dict[str, Any]]) -> go.Figure:
    figure = go.Figure()
    figure.add_trace(go.Bar(
        x=[t["minute"] for t in timeline],
        y=[t["repeated_calls"] for t in timeline],
        name="Repeated tool signature",
        marker_color="#efb65a",
    ))
    figure.add_trace(go.Bar(
        x=[t["minute"] for t in timeline],
        y=[t["tool_calls"] - t["repeated_calls"] for t in timeline],
        name="Other calls",
        marker_color="#5395d3",
    ))
    figure.update_layout(barmode="stack")
    return _styling(figure, 355)


def render_forensics(case_path: Path, review_store: Path) -> dict[str, Any]:
    """Render a synthetic scenario plus its own non-operational review queue."""
    case = load_forensics_case(case_path)
    st.caption("SCENARIO BANK-FINOPS-002 / SYNTHETIC AGENT RUNTIME FORENSICS")
    st.subheader("Audit the behavior. Expose the cost. Govern the consequence.")
    st.write(
        "A fictional third-party agent repeatedly invoked a technically authorized "
        "research tool. The individual tool action was in scope, but overall call "
        "volume and repetition became abnormal. **An authorized tool is not an "
        "unlimited operating budget.**"
    )
    st.warning(
        "**Synthetic, retrospective detection only.** No agent was actually stopped, "
        "no API provider invoiced these amounts, and no banking system was contacted.",
        icon="🧪",
    )

    st.markdown("#### Challenge the operational assumptions")
    left, center, right = st.columns(3)
    with left:
        hour_window = st.select_slider(
            "Additional continuation forecast",
            options=[1, 3, 6, 12, 24],
            value=1,
            format_func=lambda value: f"{value} hour" if value == 1 else f"{value} hours",
            help="Hypothetical additional time beyond the six-minute fixture.",
            key="forensic_projection_horizon",
        )
    with center:
        token_rate = st.slider(
            "Hypothetical token-price multiplier",
            min_value=0.5, max_value=3.0, value=1.0, step=0.25,
            help="Changes modeled token price, not synthetic usage records or provider bills.",
            key="forensic_token_rate_multiplier",
        )
    with right:
        tool_limit = st.slider(
            "Proposed workflow call limit",
            min_value=50, max_value=700, value=100, step=50,
            help="A detection threshold in the offline replay; no real enforcement.",
            key="forensic_tool_limit",
        )

    report = analyze_forensics(
        case,
        projection_hours=hour_window,
        token_rate_multiplier=token_rate,
        workflow_call_limit=tool_limit,
    )
    st.caption(
        f"Detector: {report['status']} · "
        f"authorization replay failures: {report['recorded_authorization_failures']}"
    )
    a, b, c, d = st.columns(4)
    a.metric("Recorded synthetic tool calls", f"{report['tool_calls']:,}")
    b.metric("Normal-workflow amplification", f"{report['amplification_factor']:,.0f}×")
    c.metric("Peak calls / minute", f"{report['peak_calls_per_minute']:,}")
    d.metric("Repeated tool signature", f"{report['repeated_signature_share_pct']:,.1f}%")

    graph_left, graph_right = st.columns([1.1, 1], gap="large")
    with graph_left:
        st.markdown("#### Tool-call escalation versus normal")
        st.plotly_chart(_call_chart(report["timeline"]), width="stretch")
    with graph_right:
        st.markdown("#### Repetitive execution concentration")
        st.plotly_chart(_repetition_chart(report["timeline"]), width="stretch")

    st.markdown("### Forensic findings and first detection")
    alert_left, alert_right, alert_third = st.columns(3)
    alert_left.metric(
        "Sustained burst first detected",
        "Minute " + str(report["first_burst_alert_minute"])
        if report["first_burst_alert_minute"] is not None else "Not triggered",
    )
    alert_right.metric(
        "Workflow budget first exceeded",
        "Minute " + str(report["first_budget_alert_minute"])
        if report["first_budget_alert_minute"] is not None else "Not triggered",
    )
    alert_third.metric("Rule findings", len(report["alerts"]))
    if report["alerts"]:
        st.dataframe(
            [{
                "Severity": alert["severity"],
                "Rule": alert["rule"],
                "First detected": f"Minute {alert['detected_minute']}",
                "Why flagged": alert["explanation"],
                "Evidence": ", ".join(alert["evidence_ids"]),
            } for alert in report["alerts"]],
            width="stretch",
            hide_index=True,
        )
    else:
        st.success("No selected synthetic detection rules triggered.")

    st.markdown("### Synthetic usage economics")
    st.caption(
        "These are priced **estimates from fictional metered quantities** and "
        "hypothetical rate assumptions—not actual invoices or booked costs."
    )
    one, two, three, four = st.columns(4)
    one.metric("Synthetic input tokens", f"{report['synthetic_metered_input_tokens']:,}")
    two.metric("Synthetic output tokens", f"{report['synthetic_metered_output_tokens']:,}")
    three.metric(
        "Hypothetical token-rate estimate",
        _usd(report["hypothetical_incurred_token_cost_usd"]),
    )
    four.metric(
        "Hypothetical GPU-meter estimate",
        _usd(report["hypothetical_incurred_gpu_cost_usd"]),
    )
    st.info(
        "**Do not add the token and GPU estimates together.** Their billing scopes "
        "may overlap. Source rates are hypothetical and the fixture is not a vendor invoice."
    )
    st.markdown("#### What happens if the same rate continues?")
    forecast = report["projection"]
    forecast_left, forecast_center, forecast_right = st.columns(3)
    forecast_left.metric(
        f"Additional tool calls · next {hour_window}h",
        f"{forecast['additional_tool_calls']:,}",
    )
    forecast_center.metric(
        "Additional hypothetical token spend",
        _usd(forecast["additional_token_cost_usd"]),
    )
    forecast_right.metric(
        "Separate additional GPU-meter estimate",
        _usd(forecast["additional_gpu_cost_usd"]),
    )
    st.caption(
        "Linear extrapolation from a six-minute synthetic window, *additional time "
        "only*. It is not a prediction of actual workload duration or billing. "
        "It does not establish losses if any agent were stopped."
    )

    st.markdown("### Executive disposition")
    st.write(report["human_decision"])
    history = get_reviews(review_store, report["report_id"])
    if history:
        st.success(
            "Latest recommendation review: "
            + history[0]["decision"] + " by " + history[0]["reviewer"]
        )
    else:
        st.warning("PENDING HUMAN REVIEW for this exact forensics and pricing scenario.")
    with st.form("forensics_review_form"):
        reviewer = st.text_input("Named human reviewer", key="forensics_reviewer")
        rationale = st.text_area("Required decision rationale", key="forensics_rationale")
        approve, reject = st.columns(2)
        approved = approve.form_submit_button("Approve investigation recommendation")
        rejected = reject.form_submit_button("Reject investigation recommendation")
        if approved or rejected:
            try:
                add_review(
                    review_store,
                    report["report_id"],
                    "APPROVED" if approved else "REJECTED",
                    reviewer,
                    rationale,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("Review recorded. NO external agent or cloud action executed.")
                st.rerun()
    with st.expander("Source evidence and scoped authorization grant"):
        st.json({
            "identity_id": case["identity_id"],
            "tool_signature": case["tool_signature"],
            "synthetic_grant": case["grant"],
            "evidence": case["evidence"],
            "pricing_assumptions": case["pricing_assumptions"],
        }, expanded=False)
    with st.expander("Minute-level data and audit decision trace"):
        st.dataframe(report["timeline"], width="stretch", hide_index=True)
    st.download_button(
        "Export autonomous-agent forensic evidence JSON",
        data=json.dumps({
            "report": report,
            "original_synthetic_case": case,
            "human_review_history": history,
            "limitation": "Synthetic forensic demonstration only; no real agent control.",
        }, indent=2),
        file_name="bank-finops-002-agent-forensics.json",
        mime="application/json",
    )
    st.caption(
        "Audit outcome is only a reviewed recommendation. There is no termination "
        "command, IAM write, real banking operation, or deployed monitoring service."
    )
    return report
