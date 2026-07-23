import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbrawview

_app = QApplication.instance() or QApplication([])

def test_validity_flips():
    v = tbrawview.RawJsonView()
    v.setText('{"a": 1, "b": [2, 3]}')
    assert v.is_valid() and "valid" in v.validity.text()
    v.setText('{"a": ')
    assert not v.is_valid() and "line" in v.validity.text()

def test_plaintext_proxy():
    v = tbrawview.RawJsonView()
    v.setText('{"x": 9}')
    assert v.toPlainText() == '{"x": 9}'

def test_highlighter_attached():
    v = tbrawview.RawJsonView()
    assert v.hl.document() is v.editor.document()
