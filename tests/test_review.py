import sqlite3
import pytest
from aegis_nhi.review import add_review, get_reviews

def test_review_requires_human_and_rationale(tmp_path):
    db = tmp_path / "audit" / "reviews.db"
    with pytest.raises(ValueError, match="reviewer"):
        add_review(db, "report-123", "APPROVED", "", "Reviewed")
    with pytest.raises(ValueError, match="rationale"):
        add_review(db, "report-123", "APPROVED", "CRO", "")
    with pytest.raises(ValueError, match="APPROVED or REJECTED"):
        add_review(db, "report-123", "EXECUTE_PAYMENT", "CRO", "not allowed")
    assert get_reviews(db, "report-123") == []

def test_local_audit_persistence_no_payment_table(tmp_path):
    db = tmp_path / "reviews.db"
    add_review(db, "report-123", "REJECTED", "CRO", "Need evidence")
    add_review(db, "report-123", "APPROVED", "CFO", "Recommendation only")
    history = get_reviews(db, "report-123")
    assert [item["decision"] for item in history] == ["APPROVED", "REJECTED"]
    assert history[0]["reviewer"] == "CFO"
    with sqlite3.connect(db) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "recommendation_reviews" in tables
    assert "bank_transactions" not in tables
