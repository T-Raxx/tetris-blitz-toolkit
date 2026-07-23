import os, pathlib
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tb_editor, tbadb

_app = QApplication.instance() or QApplication([])

def test_stage_all_applies_native_and_mods(tmp_path, monkeypatch):
    monkeypatch.setattr(tbadb, "device", lambda *a, **k: None)   # no device probe in test
    ed = tb_editor.Editor()
    ed.mod_stage = str(tmp_path / "stage")
    for pid, cb in ed.native_tab.boxes:      # select a native patch
        if pid == "fps_cap":
            cb.setChecked(True)
    ed.mod_tab.unlock_everything.setChecked(True)   # select a data mod (other tab)
    applied = ed._stage_all()
    assert "fps_cap" in applied and "unlock_everything" in applied
    st = pathlib.Path(ed.mod_stage)
    assert (st / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so").exists()          # native .so staged
    assert (st / "assets" / "Assets" / "Coefficients" / "helper.json").exists()  # data mod staged
