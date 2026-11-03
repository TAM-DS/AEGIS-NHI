"""AEGIS-NHI executive command center · synthetic, read-only prototype.

All banking events and economic inputs are synthetic. Policy is retrospective
fixture analysis, and simulated loss distributions are scenario planning only.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from aegis_nhi.economics import compare_control_investment
from aegis_nhi.review import add_review, get_reviews
from aegis_nhi.risk import quantify_annual_loss
from aegis_nhi.workflow import load_case, run_case
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASE = load_case(ROOT / "data/scenarios/unauthorized_ai_agent.json")
REVIEWS = ROOT / ".aegis/reviews.sqlite3"

NAVY = "#0b1628"
WHITE = "#eaf4ff"
MUTED = "#9fb8d7"
CYAN = "#53d4ef"
TEAL = "#4fcbb0"
AMBER = "#efb65a"
RED = "#fa7984"


def dollars(amount: float) -> str:
    return "$" + format(amount, ",.0f")


def plot_style(fig: go.Figure, *, height: int = 340) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=WHITE, size=13),
        height=height,
        margin=dict(l=12, r=14, t=26, b=28),
        showlegend=False,
        hoverlabel=dict(bgcolor="#233a54", font_color=WHITE),
    )
    fig.update_xaxes(
        showgrid=False, zeroline=False, linecolor="#42607a", tickfont=dict(color=MUTED)
    )
    fig.update_yaxes(
        gridcolor="rgba(150,185,225,0.13)",
        zeroline=False,
        linecolor="#42607a",
        tickfont=dict(color=MUTED),
    )
    return fig


def section_title(eyebrow: str, heading: str, description: str) -> None:
    st.markdown(
        '<div class="section-kicker">' + eyebrow + "</div>",
        unsafe_allow_html=True,
    )
    st.subheader(heading)
    st.caption(description)


def outcome_label(row: dict) -> str:
    if row["control_failure"]:
        return "EXECUTED WITHOUT AUTHORITY"
    if row["observed_outcome"] == "blocked" and not row["authorized"]:
        return "BLOCKED / DENIED"
    if row["observed_outcome"] == "executed" and row["authorized"]:
        return "EXECUTED / AUTHORIZED"
    return "BLOCKED / POLICY ALLOWED"


def evidence_sankey(rows: list[dict]) -> go.Figure:
    identities = sorted({r["identity_id"] for r in rows})
    action_nodes = sorted(
        {r["resource_id"] + " · " + r["requested_action"] for r in rows}
    )
    statuses = sorted({outcome_label(r) for r in rows})
    labels = identities + action_nodes + statuses
    lookup = {label: index for index, label in enumerate(labels)}
    sources = []
    targets = []
    colors = []
    hover = []
    for row in rows:
        action = row["resource_id"] + " · " + row["requested_action"]
        destination = outcome_label(row)
        color = RED if row["control_failure"] else (TEAL if row["authorized"] else AMBER)
        event_hover = (
            row["event_id"] + " | " + row["requested_action"] + " | "
            + row["observed_outcome"] + " | " + row["reason"]
        )
        for start, end in ((row["identity_id"], action), (action, destination)):
            sources.append(lookup[start])
            targets.append(lookup[end])
            colors.append(color + "8c")
            hover.append(event_hover)
    node_colors = (
        [CYAN] * len(identities)
        + ["#6298dc"] * len(action_nodes)
        + [RED if "WITHOUT" in s else (TEAL if "AUTHORIZED" in s else AMBER) for s in statuses]
    )
    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=labels, color=node_colors, pad=23, thickness=17,
                line=dict(color="#14283c", width=0.9),
                hovertemplate="%{label}<extra></extra>",
            ),
            link=dict(
                source=sources, target=targets, value=[1] * len(sources),
                color=colors, customdata=hover,
                hovertemplate="%{customdata}<extra></extra>",
            ),
        )
    )
    return plot_style(fig, height=380)


def timeline_chart(case: dict, rows: list[dict]) -> go.Figure:
    by_id = {item["event_id"]: item for item in rows}
    ordered = sorted(case["events"], key=lambda e: e["occurred_at"])
    fig = go.Figure()
    for event in ordered:
        finding = by_id[event["event_id"]]
        color = (
            RED if finding["control_failure"]
            else (TEAL if finding["authorized"] else AMBER)
        )
        fig.add_trace(
            go.Scatter(
                x=[datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))],
                y=[event["requested_action"]],
                mode="markers+text",
                marker=dict(size=19, color=color, line=dict(width=2, color="#142439")),
                text=[event["event_id"]],
                textposition="top center",
                textfont=dict(color=WHITE, size=11),
                hovertemplate=(
                    "Event " + event["event_id"]
                    + "<br>Outcome: " + event["observed_outcome"].upper()
                    + "<br>Replay: " + finding["reason"]
                    + "<br>Evidence: " + ", ".join(event["evidence_ids"])
                    + "<extra></extra>"
                ),
            )
        )
    fig.update_layout(
        xaxis_title="Event time (UTC)", yaxis_title="Requested tool action"
    )
    fig.update_yaxes(categoryorder="array", categoryarray=[
        "read_summary", "initiate_transfer", "bulk_export"
    ])
    return plot_style(fig, height=320)


def loss_histogram(hist: dict) -> go.Figure:
    # Zero-loss simulated years and the >P99 tail are discrete, named buckets.
    buckets = hist["bins"]
    names = ["$0 loss"] + [
        dollars(b["from_usd"]) + "–" + dollars(b["to_usd"])
        for b in buckets
    ] + ["Above P99"]
    heights = [hist["zero_loss_years"]] + [b["count"] for b in buckets] + [
        hist["tail_years_above_cutoff"]
    ]
    colors = [TEAL] + [CYAN] * len(buckets) + [AMBER]
    fig = go.Figure(
        go.Bar(
            x=list(range(len(names))),
            y=heights,
            marker_color=colors,
            customdata=names,
            hovertemplate="%{customdata}<br>%{y:,} simulated years<extra></extra>",
        )
    )
    fig.update_xaxes(
        tickmode="array", tickvals=[0, 4, 8, 12, 16, 17],
        ticktext=["$0", "Lower", "Mid-low", "Middle", "High", "> P99"]
    )
    fig.update_yaxes(title_text="Simulated years (count)")
    return plot_style(fig, height=365)


def control_sensitivity_heatmap(config: dict) -> go.Figure:
    rate = float(config["annual_event_frequency"])
    severity = sum([
        float(config["loss_min_usd"]),
        float(config["loss_mode_usd"]),
        float(config["loss_max_usd"]),
    ]) / 3
    frequencies = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    effectiveness = [0, 10, 20, 35, 50, 65, 80]
    losses = [
        [round(rate * multiple * (1 - control / 100) * severity, 2)
         for control in effectiveness]
        for multiple in frequencies
    ]
    fig = go.Figure(
        go.Heatmap(
            x=[str(x) + "%" for x in effectiveness],
            y=[str(x) + "×" for x in frequencies],
            z=losses,
            colorscale=[
                [0.0, "#103f43"], [0.3, "#287c94"],
                [0.65, "#b58b3d"], [1.0, "#b24c58"]
            ],
            colorbar=dict(title="USD/year", tickprefix="$"),
            hovertemplate=(
                "Assumed frequency: %{y}<br>Assumed effectiveness: %{x}"
                "<br>Modeled annual exposure: $%{z:,.0f}<extra></extra>"
            ),
        )
    )
    fig.update_xaxes(title="Assumed control effectiveness")
    fig.update_yaxes(title="Frequency multiplier", autorange="reversed")
    return plot_style(fig, height=410)


st.set_page_config(
    page_title="AEGIS-NHI | Executive Risk Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
<style>
:root {--aegis-cyan:#53d4ef;--aegis-mute:#a5bad6;}
.stApp {
  background: radial-gradient(ellipse at 68% 0%, #203b58 0%, #101f36 38%, #091423 90%);
  color:#ebf3ff;
}
[data-testid="stHeader"] {background:rgba(9,19,33,.45);}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#101f34,#0b1626);}
.block-container {max-width:1640px;padding-top:1.6rem;padding-bottom:3.2rem;}
.aegis-hero {
  border:1px solid #335874; border-radius:20px;
  padding:30px 37px 26px;
  background:linear-gradient(110deg,rgba(33,82,109,.65),rgba(18,32,59,.78));
  box-shadow:0px 13px 44px rgba(0,0,0,.17);
  margin:2px 0 20px;
}
.hero-kicker,.section-kicker {
 color:#72e1ed;font-size:.77rem;letter-spacing:.17em;font-weight:800;
 text-transform:uppercase;margin-bottom:9px;
}
.hero-title {color:#f4f8ff;font-size:clamp(2rem,3.2vw,3.45rem);line-height:1.08;
 font-weight:800;letter-spacing:-.035em;margin:0 0 12px;}
.hero-sub {color:#c2d5e8;font-size:1.12rem;max-width:950px;line-height:1.6;}
.hero-tag {
 display:inline-block;border:1px solid #436e7a;border-radius:30px;
 background:rgba(19,91,99,.35);color:#8ef2de;font-weight:700;
 letter-spacing:.07em;font-size:.75rem;padding:6px 12px;margin-bottom:17px;
}
[data-testid="stMetric"] {
 background:linear-gradient(145deg,#213954,#172b42);
 border:1px solid #405e7e;padding:17px 18px;border-radius:15px;
 box-shadow:0px 10px 24px rgba(0,0,0,.11);min-height:132px;
}
[data-testid="stMetricLabel"] {color:#bad0e8;font-size:1rem;}
[data-testid="stMetricValue"] {color:#fff;letter-spacing:-.03em;}
div[data-baseweb="tab-list"] {gap:11px;flex-wrap:wrap;}
button[data-baseweb="tab"] {border-radius:11px 11px 0 0;
 font-size:.97rem;font-weight:650;padding:13px 19px;}
.stAlert {border-radius:13px;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:14px;}
h2 {font-size:1.62rem!important;letter-spacing:-.025em;}
h3 {font-size:1.32rem!important;}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🛡️ AEGIS-NHI")
    st.caption("THE BEAST · ENGINEERING BUILD v0.2")
    st.divider()
    st.markdown("### Scenario controls")
    freq = st.slider(
        "Future event-frequency multiplier", min_value=0.5,
        max_value=2.0, value=1.0, step=0.1,
        help="Assumed annual frequency, not a bank's measured incident rate.",
    )
    control = st.slider(
        "Hypothetical additional control effectiveness (%)",
        min_value=0, max_value=80, value=35, step=5,
        help="Assumed proportional reduction in future loss-event frequency.",
    )
    st.markdown("### Proposed control investment")
    installation_cost = st.number_input(
        "One-time implementation cost (USD)",
        min_value=0, max_value=500000, value=75000, step=5000,
    )
    operating_cost = st.number_input(
        "Annual operating cost (USD)",
        min_value=0, max_value=250000, value=20000, step=5000,
    )
    st.caption("All costs are user-defined planning assumptions.")
    st.divider()
    st.caption("🧪 SYNTHETIC FIXTURE · NO LIVE BANK ACCESS")
    st.caption("BANK-NHI-001 · READ-ONLY EXECUTION")

report = run_case(
    CASE, frequency_multiplier=freq,
    hypothetical_control_effectiveness=control / 100,
)
baseline = quantify_annual_loss(
    CASE["annual_loss_model"], frequency_multiplier=freq,
    hypothetical_control_effectiveness=0,
)
risk = report["financial_risk"]
rows = report["authorization_decisions"]
runtime = report["runtime_metrics"]
brief = report["executive_brief"]
comparison = compare_control_investment(
    baseline_expected_annual_loss_usd=baseline["expected_annual_loss_usd"],
    residual_expected_annual_loss_usd=risk["expected_annual_loss_usd"],
    one_time_cost_usd=float(installation_cost),
    annual_operating_cost_usd=float(operating_cost),
    years=3,
    discount_rate=0.10,
)

# A recommendation review must be tied to its full economic what-if scenario,
# not merely the authorization report whose ID excludes control-cost settings.
economic_snapshot = json.dumps(
    {"report_id": report["report_id"], "one_time_usd": installation_cost,
     "annual_usd": operating_cost, "horizon": 3, "discount": 0.10},
    sort_keys=True,
)
decision_snapshot_id = hashlib.sha256(
    economic_snapshot.encode("utf-8")
).hexdigest()[:24]
history = get_reviews(REVIEWS, decision_snapshot_id)
latest = history[0]["decision"] if history else "PENDING HUMAN REVIEW"
denied = [r for r in rows if not r["authorized"]]
violations = [r for r in rows if r["control_failure"]]

st.markdown(
    """
<div class="aegis-hero">
 <div class="hero-tag">SYNTHETIC PORTFOLIO DEMONSTRATION · READ ONLY</div>
 <div class="hero-kicker">AEGIS-NHI / Chief Risk Officer Intelligence</div>
 <div class="hero-title">Control the authority.<br>Quantify the exposure.</div>
 <div class="hero-sub">From non-human identity decisions to board-level economics:
 every finding linked to evidence, every financial number labeled by basis,
 and every consequential recommendation retained for human review.</div>
</div>
""",
    unsafe_allow_html=True,
)

overview, identity, economics, cyber, evidence = st.tabs(
    [
        "🏛️ Executive Command",
        "🔐 NHI & Authorization",
        "⚡ Agent / FinOps",
        "📊 Cyber Risk Economics",
        "📁 Decision & Evidence",
    ]
)

with overview:
    section_title(
        "01 / Board-level briefing", "Thirty-second executive assessment",
        "Synthetic case BANK-NHI-001 · event evidence versus counterfactual future loss.",
    )
    a, b, c, d = st.columns(4)
    a.metric("Recorded agent requests", len(rows))
    b.metric("Blocked, unauthorized requests", sum(
        not r["authorized"] and r["observed_outcome"] == "blocked" for r in rows
    ))
    c.metric("Recorded unauthorized executions", len(violations))
    d.metric("Modeled baseline annual exposure", dollars(baseline["expected_annual_loss_usd"]))
    st.caption(
        "The exposure metric is a hypothetical annual scenario if controls fail; "
        "it is NOT a loss caused by blocked tool calls."
    )
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("#### What happened")
            st.write(
                "A fictional third-party agent executed **one authorized account-summary read**. "
                "Three additional simulated requests were blocked: a transfer, "
                "a bulk export, and a read after grant expiry."
            )
            if violations:
                st.error("Control failure: at least one synthetic unauthorized execution was recorded.")
            else:
                st.success(
                    "Control finding: no unauthorized executions are recorded in this fixture."
                )
            st.caption("Evidence: EV-001 through EV-004 · event-time policy replay")
        with st.container(border=True):
            st.markdown("#### What could it cost?")
            st.write(
                "Modeled residual annual exposure under the **assumed** additional control: "
                + "**" + dollars(risk["expected_annual_loss_usd"]) + "**."
            )
            st.write(
                "The assumed control changes modeled annual exposure by "
                + "**" + dollars(comparison["modeled_annual_risk_reduction_usd"])
                + "**. This is not realized or prevented loss."
            )
            st.caption("Frequency × severity assumptions; control effectiveness is not measured.")
    with right:
        with st.container(border=True):
            st.markdown("#### Executive decision required")
            st.markdown("**Review scoped runtime grants and consequential-tool approvals.**")
            st.write(brief["recommendation"])
            if history:
                st.success("Review status: " + latest)
            else:
                st.warning("Review status: PENDING HUMAN REVIEW")
            st.caption(
                "Approval reviews advice only. No transaction, IAM change or remediation executes."
            )
        with st.container(border=True):
            st.markdown("#### Proposed-control economics")
            x, y = st.columns(2)
            x.metric("Modeled annual risk reduction", dollars(comparison["modeled_annual_risk_reduction_usd"]))
            y.metric("Modeled 3-year net present value", dollars(comparison["discounted_net_modeled_value_usd"]))
            st.caption(
                "Entirely hypothetical: assumes actual control effectiveness and "
                "the entered implementation/operating costs."
            )
    section_title(
        "02 / Incident evidence", "Authorization event timeline",
        "Time-ordered synthetic tool requests; orange indicates blocked requests.",
    )
    st.plotly_chart(timeline_chart(CASE, rows), use_container_width=True)
    st.caption(
        "The events occurred in a simulated 2026-10-22 UTC window. "
        "Only the authorized summary read executed."
    )

with identity:
    section_title(
        "01 / Trust boundary", "Identity-to-action authority map",
        "Each line represents a synthetic tool request, not a bank network connection.",
    )
    st.plotly_chart(evidence_sankey(rows), use_container_width=True)
    st.caption(
        "Blue nodes identify the agent and requested resource/action. "
        "Green paths were authorized; amber paths were blocked. "
        "A red path would indicate an observed policy control failure."
    )
    section_title(
        "02 / Evidence chain", "Why each request was allowed or denied",
        "Capability, identity, requested resource, action, time scope and approval are distinct.",
    )
    st.dataframe(
        [
            {
                "Event": r["event_id"],
                "Identity": r["identity_id"],
                "Resource": r["resource_id"],
                "Requested action": r["requested_action"],
                "Fixture outcome": r["observed_outcome"].upper(),
                "Policy replay": "ALLOW" if r["authorized"] else "DENY",
                "Reason": r["reason"],
                "Control failure": "YES" if r["control_failure"] else "NO",
                "Evidence": ", ".join(r["evidence_ids"]),
            }
            for r in rows
        ],
        use_container_width=True, hide_index=True,
    )
    x, y = st.columns([1, 1])
    with x:
        with st.expander("Inspect the source-grant fixture"):
            st.json(CASE["grants"], expanded=False)
    with y:
        st.info(
            "A tool can be technically callable and still lack permission. "
            "The engine denies wrong-resource, wrong-action, expired or unapproved grants."
        )
    st.caption("This is retrospective synthetic policy evaluation, NOT live IAM enforcement.")

with economics:
    section_title(
        "01 / Operational footprint", "Agent runtime and cost evidence",
        "Charges come directly from fixture telemetry, not from a cloud invoice.",
    )
    a, b, c, d = st.columns(4)
    a.metric("Simulated tool calls", runtime["tool_call_events"])
    b.metric("Fixture executions", runtime["recorded_executions"])
    c.metric("Fixture blocks", runtime["recorded_blocks"])
    d.metric("Synthetic tool charges", "$" + format(runtime["synthetic_tool_cost_usd"], ",.3f"))
    st.caption(
        "The synthetic tool-call costs are NOT billable cloud charges, and "
        "are never added to modeled cyber-loss exposure."
    )
    section_title(
        "02 / Governed orchestration", "Three agents, four bounded read-only tools",
        "Deterministic orchestration today; LLM-driven narrative reasoning is not implemented.",
    )
    st.dataframe(
        [
            {"Agent role": t["agent_role"], "Tool": t["tool"],
             "Output hash": t["output_sha256"][:22] + "…", "Read only": t["read_only"]}
            for t in report["tool_trace"]
        ],
        use_container_width=True, hide_index=True,
    )
    st.progress(len(report["tool_trace"]) / report["tool_budget"])
    st.caption(
        str(len(report["tool_trace"])) + " of " + str(report["tool_budget"])
        + " budgeted tool calls; no network, IAM mutation, transfer, or remediation tool."
    )
    with st.container(border=True):
        st.markdown("#### Where the FinOps auditor goes next")
        st.write(
            "Runaway tool loops, cloud/GPU spend drift and token routing "
            "require distinct future synthetic telemetry. Those detectors are "
            "**not yet implemented**; this tab currently reports incident tool calls "
            "and synthetic per-call costs."
        )

with cyber:
    section_title(
        "01 / Financial decision support", "Model the downside, challenge the assumptions",
        "The model assumes future failures; blocked requests in this fixture produced no such loss.",
    )
    a, b, c, d = st.columns(4)
    a.metric("Expected annual loss: no added control", dollars(baseline["expected_annual_loss_usd"]))
    b.metric("Expected annual loss: assumed control", dollars(risk["expected_annual_loss_usd"]))
    c.metric("P50 modeled annual outcome", dollars(risk["p50_annual_loss_usd"]))
    d.metric("P90 modeled annual outcome", dollars(risk["p90_annual_loss_usd"]))
    l, r = st.columns([1.55, 1], gap="large")
    with l:
        st.markdown("#### Distribution across 5,000 simulated annual outcomes")
        st.plotly_chart(loss_histogram(risk["annual_loss_histogram"]), use_container_width=True)
        st.caption(
            "These are *annual outcome* frequencies from the seeded model, "
            "not observed incidents or statistical confidence intervals."
        )
    with r:
        st.markdown("#### Before and after a hypothetical control")
        bar = go.Figure(
            go.Bar(
                x=["No added control", "Assumed added control"],
                y=[baseline["expected_annual_loss_usd"], risk["expected_annual_loss_usd"]],
                marker_color=[AMBER, TEAL],
                text=[dollars(baseline["expected_annual_loss_usd"]),
                      dollars(risk["expected_annual_loss_usd"])],
                textposition="outside",
            )
        )
        bar.update_yaxes(title="USD / hypothetical year")
        st.plotly_chart(plot_style(bar, height=365), use_container_width=True)
        st.caption("Controls are not deployed; effectiveness is an editable assumption.")
    st.markdown("### Hypothetical control-investment economics")
    a, b, c, d = st.columns(4)
    a.metric("One-time assumed cost", dollars(comparison["one_time_control_cost_usd"]))
    b.metric("Annual assumed operations", dollars(comparison["annual_control_operating_cost_usd"]))
    c.metric("Year-one net modeled value", dollars(comparison["year_one_net_modeled_value_usd"]))
    d.metric("3-year discounted net modeled value", dollars(comparison["discounted_net_modeled_value_usd"]))
    st.caption(
        "At a 10% annual discount rate. 'Value' means a scenario-only risk-reduction "
        "comparison minus hypothetical control spending; no realized return is asserted."
    )
    if comparison["simple_payback_months"] is None:
        st.warning(
            "No positive simple payback under these assumptions: "
            "annual modeled reduction does not cover annual operating cost."
        )
    else:
        st.info(
            "Illustrative simple payback: "
            + str(comparison["simple_payback_months"])
            + " months, conditional on the entered control-effectiveness assumption."
        )
    section_title(
        "02 / Assumption stress test", "Risk exposure sensitivity heatmap",
        "Every cell is calculated from synthetic frequency × severity assumptions, "
        "NOT measured bank risk.",
    )
    st.plotly_chart(control_sensitivity_heatmap(CASE["annual_loss_model"]), use_container_width=True)
    with st.expander("Inspect all assumptions and model limitations", expanded=False):
        st.json(
            {
                "model": risk,
                "hypothetical_control_investment": comparison,
                "source_case": CASE["case_id"],
            }, expanded=False
        )
    st.caption(
        "The scenario uses a Poisson event-frequency assumption and triangular "
        "loss severity. P10/P50/P90 are simulated outcome quantiles, not confidence intervals."
    )

with evidence:
    section_title(
        "01 / Accountability", "Human decision & evidence room",
        "This queue approves or rejects a recommendation, never a bank operation.",
    )
    a, b = st.columns([1.3, 1], gap="large")
    with a:
        with st.container(border=True):
            st.markdown("#### Decision awaiting human judgment")
            st.write(brief["recommendation"])
            st.caption("Full hypothetical planning snapshot ID: " + decision_snapshot_id)
            if history:
                st.success(
                    "Latest human review: " + history[0]["decision"] + " · "
                    + history[0]["reviewer"]
                )
            else:
                st.warning("No review recorded for this specific economic scenario.")
            with st.form("human_recommendation_review"):
                reviewer = st.text_input("Human reviewer (name or role)")
                rationale = st.text_area("Required decision rationale")
                yes, no = st.columns(2)
                approved = yes.form_submit_button("Approve recommendation review")
                rejected = no.form_submit_button("Reject recommendation review")
                if approved or rejected:
                    try:
                        add_review(
                            REVIEWS, decision_snapshot_id,
                            "APPROVED" if approved else "REJECTED",
                            reviewer, rationale,
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.success("Review recorded locally. No operational actions executed.")
                        st.rerun()
    with b:
        with st.container(border=True):
            st.markdown("#### Evidence integrity")
            st.write("**Case:** " + report["case_id"])
            st.write("**Source SHA-256:** " + report["provenance"]["case_sha256"][:22] + "…")
            st.write("**Evidence items:** " + str(len(report["evidence"])))
            st.write("**Read-only tool traces:** " + str(len(report["tool_trace"])))
            st.write("**Current economic assumptions:**")
            st.json(
                {
                    "frequency_multiplier": freq,
                    "assumed_effectiveness_pct": control,
                    "one_time_cost_usd": installation_cost,
                    "annual_operating_cost_usd": operating_cost,
                    "planning_horizon_years": 3,
                    "discount_rate": 0.1,
                }, expanded=False
            )
    if history:
        st.markdown("#### Recorded human review history")
        st.dataframe(history, use_container_width=True, hide_index=True)
    st.markdown("### Evidence cards")
    for item in report["evidence"]:
        with st.expander(item["evidence_id"] + " · " + item["kind"]):
            st.write(item["description"])
    export = {
        "report": report,
        "uncontrolled_comparison": baseline,
        "hypothetical_control_economics": comparison,
        "decision_snapshot_id": decision_snapshot_id,
        "human_review_history": history,
        "limitations": (
            "All data are synthetic; controls are not deployed; the figures are "
            "hypothetical scenarios, not actual or prevented financial loss."
        ),
    }
    st.download_button(
        "Download complete evidence & economics package (JSON)",
        data=json.dumps(export, indent=2),
        file_name=CASE["case_id"].lower() + "-executive-evidence.json",
        mime="application/json",
    )
    st.caption(
        "The exported bundle records the modeled assumptions and included local "
        "review history. No bank or cloud systems are contacted."
    )

st.divider()
st.caption(
    "AEGIS-NHI v0.2 development · 1 of 4 scenarios implemented · deterministic "
    "agent roles · synthetic risk model · not a production autonomous CRO."
)
