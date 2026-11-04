"""Executive Scenario Lab: v0.5 cases, evidence, and human review.

Nothing in this view connects to a bank or runs operational remediation.
External model selection is manual opt-in and receives fictional claim cards only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import streamlit as st

from .narration import narrate_with_optional_model
from .review import add_review, get_reviews
from .workflow import load_case, run_case


_CASES = {
    "BANK-DATA-003": {
        "file": "sensitive_data_exposure.json",
        "label": "03 / Restricted Data Exposure",
        "description": "A blocked bulk export and an executed fictional region-policy exception.",
    },
    "BANK-SHADOW-004": {
        "file": "shadow_ai.json",
        "label": "04 / Shadow AI & Tool Inventory",
        "description": "Unregistered AI identities and unapproved tools in a fictional bank.",
    },
}


def _display_narration(report: dict[str, Any]) -> dict[str, Any]:
    """Display only narration for the exact immutable report snapshot."""
    result = st.session_state.get("scenario_model_briefing")
    if isinstance(result, dict) and result.get("report_id") == report["report_id"]:
        return result["narration"]
    return report["evidence_narration"]


def render_scenario_lab(root: Path, review_store: Path) -> None:
    st.caption("AEGIS-NHI v0.5 / SYNTHETIC INVESTIGATION PORTFOLIO")
    st.subheader("Four cases. One governed decision system.")
    st.write(
        "The completed reference library examines scoped access, runaway tool calls, "
        "restricted-data exposure, and unregistered AI tools. **Nothing here is connected "
        "to a bank, live identity service, or cloud account.**"
    )
    cards = [
        ("01 · Agent Authority", "Grant-bound actions; see Autonomous Perimeter."),
        ("02 · Agent Forensics", "Runaway calls and token economics; see Agent Forensics."),
        ("03 · Data Exposure", "Confidential-data rules and declared routing exceptions."),
        ("04 · Shadow AI", "Unregistered identities and tools in synthetic event traces."),
    ]
    columns = st.columns(4)
    for column, (title, detail) in zip(columns, cards):
        with column:
            with st.container(border=True):
                st.markdown("**" + title + "**")
                st.caption(detail)
    st.divider()
    choice = st.selectbox(
        "Select new synthetic investigation",
        options=list(_CASES),
        format_func=lambda case_id: _CASES[case_id]["label"],
        key="scenario_lab_case",
    )
    case = load_case(root / "data/scenarios" / _CASES[choice]["file"])
    report = run_case(case)
    special = report["scenario_findings"]
    st.markdown("### " + case["title"])
    st.caption(f"{choice} · Offline, deterministic fixture replay · Human review required")
    st.write(case["scenario_context"])

    one, two, three, four = st.columns(4)
    one.metric("Synthetic requests", len(case["events"]))
    two.metric("Distinct flagged events", special["flagged_event_count"])
    three.metric("Executed flagged events", special["executed_flagged_event_count"])
    four.metric("Policy replay failures", special["policy_control_failure_count"])
    st.warning(
        "**Interpret the scope correctly:** An executed flagged event describes a fictional "
        "record in the fixture. It does not establish an actual data leak, shadow-AI "
        "deployment, financial loss, or successful prevention.",
        icon="🧪",
    )

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown("#### Identity-to-action evidence replay")
        st.dataframe(
            [
                {
                    "Event": d["event_id"],
                    "Identity": d["identity_id"],
                    "Action": d["requested_action"],
                    "Observed": d["observed_outcome"],
                    "Policy": "ALLOW" if d["authorized"] else "DENY",
                    "Control failure": "YES" if d["control_failure"] else "NO",
                    "Evidence": ", ".join(d["evidence_ids"]),
                }
                for d in report["authorization_decisions"]
            ],
            hide_index=True, width="stretch",
        )
    with right:
        st.markdown("#### Specialized deterministic rule hits")
        st.dataframe(
            [
                {
                    "Rule": f["rule"],
                    "Event": f["event_id"],
                    "Priority": f["severity"],
                    "Observed": f["observed_outcome"],
                    "Evidence": ", ".join(f["evidence_ids"]),
                }
                for f in special["findings"]
            ],
            hide_index=True, width="stretch",
        )

    st.markdown("### Executive interpretation · evidence locked")
    selected = _display_narration(report)
    for claim in selected["claims"]:
        with st.container(border=True):
            st.write(claim["text"])
            st.caption(
                "Support: " + (
                    ", ".join(claim["evidence_ids"])
                    if claim["evidence_ids"]
                    else "Source scenario assumptions · SHA-256 "
                         + str(claim["assumption_source"])[:18] + "…"
                )
            )
    st.caption(
        f"Narration mode: {selected['selection_mode']}. "
        "The prose is constructed from validated Python claim cards, never "
        "model-authored statements. Risk estimates remain hypothetical."
    )

    with st.expander("Optional: let a bounded model select the order of verified claims"):
        st.write(
            "Manual opt-in only. This action sends **fictional verified claim cards** "
            "to an external model API; no live customer information is used. "
            "The model can choose a subset, not invent the briefing."
        )
        st.caption(
            "Requires OPENAI_API_KEY and the optional openai Python package. "
            "One response call, maximum 180 output tokens, 12-second timeout, "
            "no retry. If validation fails, the deterministic briefing remains."
        )
        if st.button("Select verified claim outline with AI", key="scenario_model_outline"):
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                st.warning("No API key configured; deterministic briefing remains available.")
            else:
                try:
                    from openai import OpenAI

                    client = OpenAI(api_key=api_key, timeout=12.0, max_retries=0)
                    alternate = narrate_with_optional_model(
                        report, client=client, model="gpt-4.1-mini"
                    )
                except Exception as exc:  # External SDK response must fail closed.
                    # Explicit fail-closed: never show unverified model prose.
                    st.error(
                        "Could not validate the optional outline. The deterministic "
                        "verified briefing remains. Technical error: " + type(exc).__name__
                    )
                else:
                    st.session_state["scenario_model_briefing"] = {
                        "report_id": report["report_id"], "narration": alternate
                    }
                    st.success("Verified claim selection recorded for this scenario only.")
                    st.rerun()

    st.markdown("### Human review and evidence export")
    st.caption(
        "Human review concerns this investigation recommendation—not a production "
        "permission grant or an approval to send data or execute a transaction."
    )
    history = get_reviews(review_store, report["report_id"])
    if history:
        st.success(
            "Latest recommendation review: "
            + history[0]["decision"] + " by " + history[0]["reviewer"]
        )
    else:
        st.info("PENDING HUMAN REVIEW · exact report " + report["report_id"])
    with st.form("scenario_lab_review_form"):
        reviewer = st.text_input("Named human reviewer", key="scenario_lab_reviewer")
        note = st.text_area("Required review rationale", key="scenario_lab_rationale")
        yes, no = st.columns(2)
        approve = yes.form_submit_button("Approve recommendation for evaluation")
        reject = no.form_submit_button("Reject recommendation")
        if approve or reject:
            try:
                add_review(
                    review_store, report["report_id"],
                    "APPROVED" if approve else "REJECTED", reviewer, note,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.success("Recommendation review recorded; no external action taken.")
                st.rerun()

    with st.expander("Source fixture, model assumptions and provenance"):
        st.json({
            "case_id": case["case_id"],
            "source_sha256": report["provenance"]["case_sha256"],
            "source_evidence": case["evidence"],
            "loss_assumptions": case["annual_loss_model"],
            "risk_limitation": report["financial_risk"]["limitations"],
            "detector_limitation": special["limitations"],
        }, expanded=False)
    st.download_button(
        "Download complete synthetic investigation JSON",
        data=json.dumps({
            "report": report,
            "source_case": case,
            "human_recommendation_reviews": history,
            "limitations": (
                "Synthetic proof of architecture only, not deployed monitoring "
                "or an operational authorization."
            ),
        }, indent=2),
        file_name=choice.lower() + "-evidence.json",
        mime="application/json",
        key="scenario_lab_evidence_download",
    )
