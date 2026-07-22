import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbnativetab

_app = QApplication.instance() or QApplication([])

def test_pace_conversion():
    assert tbnativetab.pct_to_pace(50, 1, 50) == 2
    assert tbnativetab.pct_to_pace(100, 1, 50) == 1
    assert tbnativetab.pct_to_pace(14, 1, 50) == 7
    assert tbnativetab.pct_to_pace(1, 1, 50) == 50   # clamped to max

def test_apply_passes_values():
    got = {}
    tab = tbnativetab.NativeTab(lambda ids, values: got.update(ids=ids, values=values))
    for pid, cb in tab.boxes:
        if pid == "powerup_pace_fixed":
            cb.setChecked(True)
    tab.param_ctrls["powerup_pace_fixed"].setValue(50)
    tab._apply()
    assert "powerup_pace_fixed" in got["ids"]
    assert got["values"]["powerup_pace_fixed"]["pace"] == 2
