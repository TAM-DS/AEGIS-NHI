"""Evidence-locked executive narration, with optional bounded model outline selection.

Only approved deterministic claim cards are rendered; the model cannot compose
unverified prose or authorize operational responses.
"""

from __future__ import annotations

import json
from typing import Any


def claim_cards(report: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = report["authorization_decisions"]
    refs = sorted({e for d in decisions for e in d["evidence_ids"]})
    if not refs:
        raise ValueError("Narration requires event-linked evidence")
    denied = sum(not d["authorized"] for d in decisions)
    failures = sum(d["control_failure"] for d in decisions)
    cards = [
        {"id": "case", "text": (
            f"Fictional case {report['case_id']} contains {len(decisions)} synthetic requests; "
            f"{denied} were denied by offline scoped-grant replay."
        ), "evidence_ids": refs, "assumption_source": None},
        {"id": "authority", "text": (
            f"The synthetic trace records {failures} executions contradicting "
            "authorization replay. This is not a live enforcement control."
        ), "evidence_ids": refs, "assumption_source": None},
        {"id": "risk", "text": (
            "Under fictional scenario assumptions, conditional expected annual "
            f"loss is USD {report['financial_risk']['expected_annual_loss_usd']:,.2f}. "
            "This is modeled exposure, not observed loss or realized savings."
        ), "evidence_ids": [], "assumption_source": report["provenance"]["case_sha256"]},
    ]
    specialized = report.get("scenario_findings")
    if specialized:
        cards.append({"id": "specialized", "text": (
            f"Offline {specialized['scenario_type'].replace('_', ' ')} checks "
            f"flagged {specialized['flagged_event_count']} distinct fictional events; "
            f"{specialized['executed_flagged_event_count']} were recorded as executed."
        ), "evidence_ids": specialized["evidence_ids"], "assumption_source": None})
    cards.append({"id": "disposition", "text": (
        "A named human must review the recommendation and evidence. Reviewing "
        "this report never grants permission to change accounts, send funds, "
        "export data, mutate cloud resources, or take autonomous action."
    ), "evidence_ids": refs, "assumption_source": None})
    return cards


def select_claim_ids(raw: str, approved_ids: list[str]) -> list[str]:
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("Model response must be JSON") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"selected_claim_ids"}:
        raise ValueError("Model may return only selected_claim_ids")
    ids = parsed["selected_claim_ids"]
    if (not isinstance(ids, list) or not 1 <= len(ids) <= len(approved_ids)
        or any(not isinstance(x, str) for x in ids) or len(ids) != len(set(ids))
        or not set(ids).issubset(approved_ids)):
        raise ValueError("Model selected unknown or repeated claims")
    return ids


def narrate_evidence(
    report: dict[str, Any], *, model_selection: str | None = None
) -> dict[str, Any]:
    cards = claim_cards(report)
    ids = ([c["id"] for c in cards] if model_selection is None else
           select_claim_ids(model_selection, [c["id"] for c in cards]))
    by_id = {c["id"]: c for c in cards}
    chosen = [by_id[x] for x in ids]
    return {
        "basis": "preverified_evidence_claim_cards",
        "selection_mode": "bounded_model_claim_selection" if model_selection is not None
                          else "deterministic_claim_selection",
        "narrative": "\n\n".join(c["text"] for c in chosen),
        "selected_claim_ids": ids,
        "claims": chosen,
        "approval_status": "PENDING_HUMAN_REVIEW",
        "limitations": "Model text is discarded; only predefined cited claims are rendered.",
    }


def narrate_with_optional_model(
    report: dict[str, Any], *, client: Any, model: str = "gpt-4.1-mini"
) -> dict[str, Any]:
    """Caller-authorized one-call selection; no model-authored prose survives."""
    cards = claim_cards(report)
    answer = client.responses.create(
        model=model, max_output_tokens=180, input=[
            {"role": "system", "content": (
                "Return JSON with exactly one field selected_claim_ids, a list of "
                "unique IDs from the provided cards. Do not write prose or other fields."
            )},
            {"role": "user", "content": json.dumps(
                [{"id": c["id"], "text": c["text"], "evidence_ids": c["evidence_ids"]}
                 for c in cards], sort_keys=True)},
        ],
    )
    return narrate_evidence(report, model_selection=answer.output_text)
