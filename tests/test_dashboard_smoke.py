"""Execute the actual Streamlit app without browser network calls.

This verifies that all page sections, charts and fixture outputs are renderable.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_executive_app_initial_render():
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "streamlit_app.py"),
        default_timeout=30,
    ).run()
    messages = [getattr(err, "message", str(err)) for err in app.exception]
    assert not messages, messages
    assert len(app.metric) >= 12
    labels = [entry.label for entry in app.metric]
    assert "Unmitigated modeled annual loss*" in labels
    assert "Mitigated modeled annual loss*" in labels
    assert "Investment case" in labels
    assert "Recommendation review" in labels
    assert "Synthetic requests" in labels
    assert "Blocked requests" in labels
    assert "Unauthorized executions" in labels
    assert "Modeled annual exposure" in labels
    assert "Recorded synthetic tool calls" in labels
    assert "Normal-workflow amplification" in labels
    assert "Rule findings" in labels

    # Streamlit Markdown treats paired dollar signs as LaTeX delimiters unless escaped.
    # Verify that financial currency amounts remain visible as ordinary prose.
    financial_prose = [
        entry.value
        for entry in app.markdown
        if "At the current assumption of" in str(entry.value)
    ]
    assert len(financial_prose) == 1
    assert r"\$" in financial_prose[0]
    assert "\n\nYear-one" in financial_prose[0]
