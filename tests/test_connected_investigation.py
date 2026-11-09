from copy import deepcopy
import json
from pathlib import Path
import unittest

from aegis_nhi.connected_investigation import build_connected_investigation, adapt_case_events, digest

ROOT = Path(__file__).resolve().parents[1]


class ConnectedTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((ROOT / "data/scenarios/shadow_ai.json").read_text())
        self.telemetry = json.loads((ROOT / "data/connected/shadow_sessions.json").read_text())

    def test_adapter_preserves_original_evidence(self):
        report = adapt_case_events(self.case)
        self.assertEqual(report["counts"]["records"], 4)
        self.assertEqual(report["links"], [])
        self.assertEqual(report["observations"][0]["evidence"][0]["evidence_id"], "SA-001")

    def test_complete_replay_deterministic_and_no_authority(self):
        report = build_connected_investigation(self.case, self.telemetry)
        self.assertEqual(report, build_connected_investigation(self.case, self.telemetry))
        self.assertEqual(report["session_count"], 2)
        self.assertEqual(report["host_observation_count"], 2)
        self.assertEqual(report["unassigned_event_ids"], [])
        self.assertEqual(report["approval_status"], "NOT_AUTHORIZED_FOR_ACTION")
        ids = {n["id"] for n in report["nodes"]}
        self.assertEqual(len(ids), len(report["nodes"]))
        self.assertTrue(all(e["source"] in ids and e["target"] in ids for e in report["edges"]))
        self.assertEqual(report["fixture_runtime_cost"]["synthetic_tool_cost_usd"], 0.019)
        self.assertEqual(report["hypothetical_annual_exposure"]["period"], "year")
        self.assertTrue(any(f["rule"] == "UNREGISTERED_AI_TOOL" for f in report["scenario_findings"]["findings"]))

    def test_unknown_source_case_and_scope_rejected(self):
        for field, value in [("case_id", "another-case"), ("institution", "another-bank"),
                             ("case_sha256", "0" * 64), ("source_id", "external-edr"),
                             ("synthetic", 1), ("schema_version", True)]:
            telemetry = deepcopy(self.telemetry)
            telemetry[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_connected_investigation(self.case, telemetry)

    def test_changed_source_is_not_silently_reused(self):
        self.case["events"][0]["synthetic_tool_cost_usd"] = 10
        with self.assertRaises(ValueError):
            build_connected_investigation(self.case, self.telemetry)

    def test_session_identity_time_and_unknown_events(self):
        for field, value in [("identity_id", "another-agent"), ("event_ids", ["UNKNOWN"]),
                             ("event_ids", ["SHADOW-001", "SHADOW-001"]),
                             ("started_at", "2026-10-25T09:20:00Z"),
                             ("ended_at", "2026-10-25T09:00:00Z")]:
            telemetry = deepcopy(self.telemetry)
            telemetry["sessions"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_connected_investigation(self.case, telemetry)

    def test_host_reference_cannot_cross_session_or_time(self):
        for field, value in [("session_id", "session-2"), ("session_id", "unknown"),
                             ("event_id", "SHADOW-004"), ("observed_at", "2026-10-25T09:30:00Z")]:
            telemetry = deepcopy(self.telemetry)
            telemetry["hosts"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_connected_investigation(self.case, telemetry)

    def test_duplicate_and_unbounded_telemetry_rejected(self):
        for field in ("sessions", "hosts"):
            for count in (2, 101):
                telemetry = deepcopy(self.telemetry)
                telemetry[field] = [telemetry[field][0]] * count
                with self.subTest(field=field, count=count), self.assertRaises(ValueError):
                    build_connected_investigation(self.case, telemetry)

    def test_missing_assignments_are_visible_not_inferred(self):
        self.telemetry["sessions"][0]["event_ids"].remove("SHADOW-001")
        report = build_connected_investigation(self.case, self.telemetry)
        self.assertEqual(report["unassigned_event_ids"], ["SHADOW-001"])

    def test_invalid_schema_rejected(self):
        self.telemetry["production_authorized"] = True
        with self.assertRaises(ValueError):
            build_connected_investigation(self.case, self.telemetry)

    def test_brief_separates_grant_authority_inventory_and_outcome(self):
        brief = build_connected_investigation(self.case, self.telemetry)["decision_brief"]
        self.assertEqual(brief["escalation_event_ids"], ["SHADOW-003"])
        self.assertEqual(brief["blocked_attempt_event_ids"], ["SHADOW-002", "SHADOW-004"])
        rows = {r["event_id"]: r for r in brief["events"]}
        self.assertTrue(rows["SHADOW-003"]["grant_authorized"])
        self.assertFalse(rows["SHADOW-003"]["authorization_control_failure"])
        self.assertEqual(rows["SHADOW-003"]["reason_codes"], ["UNREGISTERED_AI_TOOL"])
        self.assertEqual(rows["SHADOW-003"]["evidence_ids"], ["SA-003"])
        self.assertEqual(rows["SHADOW-003"]["host_observation_ids"], ["host-observation-1"])
        self.assertEqual(rows["SHADOW-001"]["host_observation_ids"], [])
        self.assertEqual(rows["SHADOW-001"]["disposition"], "NO_TRIGGER_UNDER_EVALUATED_RULES")
        # Two registry findings plus a grant denial still represent one blocked event.
        self.assertEqual(len(rows["SHADOW-002"]["reason_codes"]), 3)
        self.assertEqual(brief["human_review_status"], "PENDING_HUMAN_REVIEW")
        self.assertEqual(brief["operational_authority"], "NOT_AUTHORIZED_FOR_ACTION")

    def test_execution_without_grant_escalates_independently_of_registry(self):
        self.case["ai_registry"]["approved_identity_ids"].append("unregistered-assistant-09")
        self.case["ai_registry"]["registered_tool_ids"].append("unapproved.vendor-llm")
        self.case["events"][1]["observed_outcome"] = "executed"
        self.telemetry["case_sha256"] = digest(self.case)
        brief = build_connected_investigation(self.case, self.telemetry)["decision_brief"]
        self.assertEqual(brief["escalation_event_ids"], ["SHADOW-002"])
        row = brief["events"][1]
        self.assertTrue(row["authorization_control_failure"])
        self.assertEqual(row["finding_ids"], [])
        self.assertEqual(row["reason_codes"], ["DENY_NO_IDENTITY_GRANT"])

    def test_blocked_findings_do_not_become_recorded_execution(self):
        self.case["events"][2]["observed_outcome"] = "blocked"
        self.telemetry["case_sha256"] = digest(self.case)
        brief = build_connected_investigation(self.case, self.telemetry)["decision_brief"]
        self.assertEqual(brief["escalation_event_ids"], [])
        self.assertEqual(brief["recommendation"], "REVIEW_BLOCKED_ATTEMPTS")
        self.assertEqual(len(brief["blocked_attempt_event_ids"]), 3)

    def test_missing_relationships_do_not_erase_escalation_or_invent_host_links(self):
        self.telemetry["sessions"][0]["event_ids"].remove("SHADOW-003")
        self.telemetry["hosts"].pop(0)
        brief = build_connected_investigation(self.case, self.telemetry)["decision_brief"]
        self.assertEqual(brief["escalation_event_ids"], ["SHADOW-003"])
        row = brief["events"][2]
        self.assertIsNone(row["session_id"])
        self.assertEqual(row["host_observation_ids"], [])
        self.assertEqual(row["evidence_gaps"], ["NO_DECLARED_SESSION", "NO_EXPLICIT_HOST_OBSERVATION"])

    def test_no_trigger_is_not_an_approval_or_safety_claim(self):
        # All requests get a matching grant and registered inventory in this variant.
        self.case["ai_registry"]["approved_identity_ids"].append("unregistered-assistant-09")
        self.case["ai_registry"]["registered_tool_ids"].append("unapproved.vendor-llm")
        for event in self.case["events"][1::2]:
            grant = deepcopy(self.case["grants"][0])
            grant.update(grant_id="GR-" + event["event_id"], identity_id=event["identity_id"],
                         resource_id=event["resource_id"], allowed_actions=[event["requested_action"]])
            self.case["grants"].append(grant)
        self.telemetry["case_sha256"] = digest(self.case)
        brief = build_connected_investigation(self.case, self.telemetry)["decision_brief"]
        self.assertEqual(brief["recommendation"], "NO_TRIGGER_UNDER_EVALUATED_RULES")
        self.assertEqual(brief["operational_authority"], "NOT_AUTHORIZED_FOR_ACTION")
        self.assertTrue(any("Safety" in item for item in brief["not_established"]))

    def test_brief_citations_and_rules_are_bound_into_report_hash(self):
        before_case, before_telemetry = deepcopy(self.case), deepcopy(self.telemetry)
        report = build_connected_investigation(self.case, self.telemetry)
        self.assertEqual(self.case, before_case)
        self.assertEqual(self.telemetry, before_telemetry)
        self.assertEqual(report["decision_brief"]["source_case_sha256"], digest(self.case))
        self.assertEqual(report["decision_brief"]["source_telemetry_sha256"], digest(self.telemetry))
        expected = report.pop("report_sha256")
        self.assertEqual(digest(report), expected)
        report["decision_brief"]["rule_version"] = "changed-rule"
        self.assertNotEqual(digest(report), expected)


if __name__ == "__main__":
    unittest.main()
