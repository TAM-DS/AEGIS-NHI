from copy import deepcopy
import json
from pathlib import Path
import unittest

from aegis_nhi.connected_investigation import build_connected_investigation, adapt_case_events

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


if __name__ == "__main__":
    unittest.main()
