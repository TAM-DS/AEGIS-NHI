"""Offline acceptance tests; no source systems are contacted."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from aegis_nhi.source_contract import build_source_report

FIXTURE = Path(__file__).resolve().parents[1] / "data/cross_source/two_source_demo.json"
SOURCES = ["fictional-iam", "fictional-audit"]


class SourceContractTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads(FIXTURE.read_text())

    def report(self, bundle=None):
        return build_source_report(self.bundle if bundle is None else bundle, allowed_sources=SOURCES)

    def test_valid_explicit_link_preserves_scopes_and_authority(self):
        report = self.report()
        self.assertEqual(report["counts"], {"records": 2, "explicit_links": 1})
        self.assertEqual(len(report["observations"]), 2)
        self.assertEqual(report["approval_status"], "NOT_AUTHORIZED_FOR_ACTION")
        self.assertEqual(report["provenance_status"], "DECLARED_NOT_AUTHENTICATED")

    def test_matching_labels_do_not_implicitly_join(self):
        self.bundle["links"] = []
        self.assertEqual(self.report()["counts"]["explicit_links"], 0)

    def test_input_order_does_not_change_report(self):
        expected = self.report()
        self.bundle["records"].reverse()
        link = self.bundle["links"][0]
        link["left"], link["right"] = link["right"], link["left"]
        link["basis_evidence"].reverse()
        self.assertEqual(self.report(), expected)

    def test_independent_allowlist(self):
        for allowlist in ([], "fictional-iam", ["untrusted"]):
            with self.subTest(allowlist=allowlist), self.assertRaises(ValueError):
                build_source_report(self.bundle, allowed_sources=allowlist)

    def test_scope_and_observation_conflicts(self):
        for field, value in [("institution_id", "other-bank"), ("case_id", "other-case"),
                             ("action", "write"), ("outcome", "blocked")]:
            changed = deepcopy(self.bundle)
            changed["records"][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.report(changed)

    def test_duplicate_and_conflicting_records_rejected(self):
        for outcome in ("executed", "blocked"):
            changed = deepcopy(self.bundle)
            copy = deepcopy(changed["records"][0])
            copy["outcome"] = outcome
            changed["records"].append(copy)
            with self.subTest(outcome=outcome), self.assertRaises(ValueError):
                self.report(changed)

    def test_malformed_records_fail_closed(self):
        for field, value in [("source_id", "unknown"), ("record_id", "a/b"),
                             ("identity_id", ""), ("outcome", "unknown"),
                             ("evidence", []), ("evidence", [{"evidence_id": "e", "sha256": "bad"}])]:
            changed = deepcopy(self.bundle)
            changed["records"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.report(changed)

    def test_missing_and_unknown_fields(self):
        changed = deepcopy(self.bundle)
        del changed["records"][0]["case_id"]
        with self.assertRaises(ValueError):
            self.report(changed)
        self.bundle["authorization"] = True
        with self.assertRaises(ValueError):
            self.report()

    def test_schema_and_synthetic_boundary(self):
        for field, value in [("schema_version", True), ("schema_version", 2), ("synthetic", False), ("synthetic", 1)]:
            changed = deepcopy(self.bundle)
            changed[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.report(changed)

    def test_bad_links_and_evidence_rejected(self):
        for field, value in [("left", ["unknown", "event-001"]), ("right", ["fictional-iam", "event-001"]),
                             ("relation", "AUTHORIZE"), ("basis_evidence", []),
                             ("basis_evidence", [["fictional-iam", "event-001", "missing"], ["fictional-audit", "event-001", "evidence-001"]])]:
            changed = deepcopy(self.bundle)
            changed["links"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.report(changed)

    def test_one_sided_or_duplicate_evidence_rejected(self):
        ref = self.bundle["links"][0]["basis_evidence"][0]
        self.bundle["links"][0]["basis_evidence"] = [ref, ref]
        with self.assertRaises(ValueError):
            self.report()

    def test_duplicate_links_rejected(self):
        self.bundle["links"].append(deepcopy(self.bundle["links"][0]))
        with self.assertRaises(ValueError):
            self.report()

    def test_bounds(self):
        for field, value in [("records", []), ("records", self.bundle["records"] * 501),
                             ("links", self.bundle["links"] * 1001)]:
            changed = deepcopy(self.bundle)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.report(changed)

    def test_cli_success_and_rejection_without_raw_content(self):
        command = [sys.executable, "-m", "aegis_nhi.source_contract"]
        result = subprocess.run(command + [str(FIXTURE), "--source", SOURCES[0], "--source", SOURCES[1]], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["counts"]["explicit_links"], 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            for raw in ('{"schema_version":1,"schema_version":2,"secret":"DO_NOT_PRINT"}', 'x' * 1048577):
                path.write_text(raw)
                result = subprocess.run(command + [str(path), "--source", SOURCES[0]], capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(json.loads(result.stdout)["status"], "rejected")
                self.assertNotIn("DO_NOT_PRINT", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
