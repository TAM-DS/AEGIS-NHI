"""Synthetic financial-frontier reconciliation and jurisdictional routing *replay*.

No live banking ledger, data residency enforcement, cryptographic signatures,
transaction processing or network routing is performed by these functions.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


_CONSEQUENTIAL_ACTIONS = {
    "initiate_transfer", "post_ledger", "bulk_export", "change_limit"
}


def _usd(raw: object) -> Decimal:
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Ledger amounts must be valid USD decimals") from exc
    if not amount.is_finite() or amount.as_tuple().exponent < -2:
        raise ValueError("Ledger amounts must be finite and expressed to cents")
    return amount.quantize(Decimal("0.01"))


def reconcile_synthetic_ledger(
    case: dict[str, Any], decisions: list[dict[str, Any]]
) -> dict[str, Any]:
    """Validate ledger snapshot roll-forward and any fictional double-entry postings.

    Posting authorization relies on the same event-time NHI policy replay.
    Detection of an exception does not prevent transactions in any real system.
    """
    ledger = case.get("ledger")
    if not isinstance(ledger, dict):
        return {
            "basis": "synthetic_ledger_fixture",
            "status": "NOT_EVALUATED",
            "reason": "Case has no ledger evidence",
            "exceptions": [],
        }
    if ledger.get("currency") != "USD":
        raise ValueError("Synthetic ledger must declare USD")
    accounts = ledger.get("accounts", [])
    if not accounts:
        raise ValueError("Ledger requires account snapshots")
    balances: dict[str, Decimal] = {}
    closing: dict[str, Decimal] = {}
    for account in accounts:
        name = account["account_id"]
        if name in balances or not str(name).strip():
            raise ValueError("Duplicate or empty ledger account ID")
        balances[name] = _usd(account["opening_balance_usd"])
        closing[name] = _usd(account["closing_balance_usd"])
    original_total = sum(balances.values(), Decimal("0.00"))
    policy_by_event = {d["event_id"]: d for d in decisions}
    events_by_id = {e["event_id"]: e for e in case["events"]}
    seen_postings = set()
    exceptions: list[dict[str, str]] = []
    total_posted = Decimal("0.00")
    for entry in ledger.get("postings", []):
        journal_id = entry["journal_id"]
        if journal_id in seen_postings:
            raise ValueError("Duplicate journal entry")
        seen_postings.add(journal_id)
        debit, credit = entry["debit_account"], entry["credit_account"]
        if debit not in balances or credit not in balances or debit == credit:
            raise ValueError("Invalid debit/credit ledger accounts")
        amount = _usd(entry["amount_usd"])
        if amount <= 0:
            raise ValueError("Posted journal amount must be positive")
        total_posted += amount
        # This fixture uses asset account balances: debit increases one account,
        # credit decreases the other, preserving the overall modeled balance.
        balances[debit] += amount
        balances[credit] -= amount
        event_id = entry.get("event_id", "")
        decision = policy_by_event.get(event_id)
        event = events_by_id.get(event_id)
        if not event or not decision:
            exceptions.append({"type": "ORPHAN_POSTING", "reference": journal_id})
        elif (
            event["observed_outcome"] != "executed"
            or not decision["authorized"]
            or event["requested_action"] not in {"initiate_transfer", "post_ledger"}
        ):
            exceptions.append({
                "type": "UNAUTHORIZED_OR_BLOCKED_EVENT_POSTED",
                "reference": journal_id,
            })
    for account_id, expected in balances.items():
        if closing[account_id] != expected:
            exceptions.append({
                "type": "LEDGER_ROLL_FORWARD_MISMATCH",
                "reference": account_id,
            })
    final_total = sum(closing.values(), Decimal("0.00"))
    if final_total != original_total:
        exceptions.append({
            "type": "LEDGER_TRIAL_BALANCE_MISMATCH",
            "reference": ledger.get("ledger_id", "unknown"),
        })
    consequential = [
        {
            "event_id": event["event_id"],
            "requested_action": event["requested_action"],
            "observed_outcome": event["observed_outcome"],
            "policy_authorized": policy_by_event[event["event_id"]]["authorized"],
            "basis": "synthetic_event_and_grant_replay",
        }
        for event in case["events"]
        if event["requested_action"] in _CONSEQUENTIAL_ACTIONS
    ]
    return {
        "basis": "synthetic_ledger_and_event_reconciliation_only",
        "status": "EXCEPTION" if exceptions else "RECONCILED",
        "ledger_id": ledger["ledger_id"],
        "currency": "USD",
        "opening_total_usd": str(original_total),
        "closing_total_usd": str(final_total),
        "posting_count": len(seen_postings),
        "posted_journal_value_usd": str(total_posted),
        "exception_count": len(exceptions),
        "exceptions": exceptions,
        "consequential_action_requests": consequential,
        "limitations": (
            "Reconciles fictional opening/closing snapshots and journal postings only. "
            "Zero postings means no mutation was recorded in the fixture, not that "
            "banking capital was protected or that real-world ledgers were audited."
        ),
    }


def replay_sovereign_routing(case: dict[str, Any]) -> dict[str, Any]:
    """Check declared destination-region metadata against a synthetic allowlist.

    This does not enforce actual network routing, contractual residency, or
    geographic location attestation.
    """
    policy = case.get("routing_policy")
    if not isinstance(policy, dict):
        return {
            "basis": "synthetic_destination_region_policy_replay",
            "status": "NOT_EVALUATED",
            "events": [],
        }
    allowed = policy.get("approved_processing_regions")
    if not isinstance(allowed, list) or not allowed:
        raise ValueError("Routing policy must specify approved processing regions")
    if len(allowed) != len(set(allowed)) or any(not x for x in allowed):
        raise ValueError("Duplicate or empty processing region")
    findings = []
    for event in case["events"]:
        region = event.get("declared_destination_region")
        permitted = isinstance(region, str) and region in allowed
        observed = event["observed_outcome"]
        findings.append({
            "event_id": event["event_id"],
            "requested_action": event["requested_action"],
            "declared_destination_region": region or "UNDECLARED",
            "policy_replay": "ALLOW_REGION" if permitted else "DENY_REGION",
            "observed_outcome": observed,
            "recorded_routing_control_failure": observed == "executed" and not permitted,
            "evidence_ids": list(event["evidence_ids"]),
        })
    return {
        "basis": "synthetic_destination_region_policy_replay",
        "policy_id": policy["policy_id"],
        "classification": policy["data_classification"],
        "approved_regions": list(allowed),
        "events": findings,
        "outside_declared_boundary_count": sum(
            event["declared_destination_region"] not in allowed for event in findings
        ),
        "executed_outside_boundary_count": sum(
            item["recorded_routing_control_failure"] for item in findings
        ),
        "limitations": (
            "Offline declared-region metadata check only. Does not prove network "
            "location, actual data sovereignty, contractual compliance or enforcement."
        ),
    }
