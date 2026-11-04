"""v0.5 UI smoke test: both new cases render with no external model calls."""

from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_new_scenario_lab_renders_and_switches_fixtures():
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "streamlit_app.py"),
        default_timeout=40,
    ).run()
    assert not app.exception, [str(e) for e in app.exception]
    labels = [metric.label for metric in app.metric]
    assert "Distinct flagged events" in labels
    assert "Executed flagged events" in labels
    selection = [
        item for item in app.selectbox if item.label == "Select new synthetic investigation"
    ]
    assert len(selection) == 1
    assert selection[0].value == "BANK-DATA-003"
    selection[0].set_value("BANK-SHADOW-004").run()
    assert not app.exception, [str(e) for e in app.exception]
    assert selection[0].value == "BANK-SHADOW-004"
    labels = [metric.label for metric in app.metric]
    assert "Policy replay failures" in labels
