from pathlib import Path
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_connected_view_renders_and_traces_selected_event():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=40).run()
    assert not app.exception, [str(e) for e in app.exception]
    assert any(metric.label == "Declared sessions" and metric.value == "2" for metric in app.metric)
    selection = next(item for item in app.selectbox if item.label == "Trace an event")
    selection.set_value("SHADOW-003").run()
    assert not app.exception, [str(e) for e in app.exception]
    assert next(item for item in app.selectbox if item.label == "Trace an event").value == "SHADOW-003"
    assert any(metric.label == "Fictional fixture charges" and metric.value == "$0.019" for metric in app.metric)
    assert any("No live security feeds" in item.value for item in app.info)
    assert any(metric.label == "Executed events requiring investigation" and metric.value == "1"
               for metric in app.metric)
    assert any(metric.label == "Blocked attempts requiring review" and metric.value == "2"
               for metric in app.metric)
    assert any("grants no operational authority" in item.value for item in app.caption)


def test_invalid_source_renders_error_without_partial_report():
    script = '''
from pathlib import Path
from unittest.mock import patch
from aegis_nhi.ui_connected import render_connected
with patch("aegis_nhi.ui_connected.build_connected_investigation", side_effect=ValueError("bad source")):
    render_connected(Path(ROOT_PATH))
'''.replace("ROOT_PATH", repr(str(ROOT)))
    app = AppTest.from_string(script, default_timeout=40).run()
    assert not app.exception
    assert len(app.error) == 1
    assert not app.metric
    assert not app.selectbox
    assert not app.dataframe
    assert not any("Recommendation:" in item.value for item in app.markdown)
