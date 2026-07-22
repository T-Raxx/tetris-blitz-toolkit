import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbnativetab

def test_native_tab_lists_and_builds():
    app = QApplication.instance() or QApplication([])
    got = {}
    w = tbnativetab.NativeTab(lambda ids: got.setdefault("ids", ids))
    if w.boxes:
        pid, cb = w.boxes[0]; cb.setChecked(True)
        w._apply()
        assert pid in got["ids"]
    else:
        w._apply()
        assert got.get("ids") == []
