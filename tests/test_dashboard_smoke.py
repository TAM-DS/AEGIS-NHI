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
