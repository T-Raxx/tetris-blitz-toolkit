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
    # also select a Nivel-3 injection from another tab
    if ed.inject_tab.source.count():
        for i in range(ed.inject_tab.source.count()):
            if ed.inject_tab.source.itemData(i) != "Custom PNG…":
                ed.inject_tab.source.setCurrentIndex(i); break
        ed.inject_tab.base.setCurrentIndex(0); ed.inject_tab._add()

    applied = ed._stage_all()
    assert "fps_cap" in applied and "unlock_everything" in applied
    st = pathlib.Path(ed.mod_stage)
    assert (st / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so").exists()          # native .so staged
    assert (st / "assets" / "Assets" / "Coefficients" / "helper.json").exists()  # data mod staged
    if ed.inject_tab.selection():                                                # inject applied too
        assert any(a.startswith("inject:") for a in applied)
        assert (st / "assets" / "Assets" / "Cocos2dxImages" / "size150" / "Common" / "Common0.png").exists()

def test_redist_button_stages_all_and_builds(tmp_path, monkeypatch):
    monkeypatch.setattr(tbadb, "device", lambda *a, **k: None)
    ed = tb_editor.Editor()
    ed.mod_stage = str(tmp_path / "stage")
    ed.mod_tab.unlock_everything.setChecked(True)
    captured = {}
    apkbuild = ed._apkbuild_module()
    monkeypatch.setattr(apkbuild, "build",
        lambda stage, out_apk, **k: captured.update(stage=stage, out=out_apk) or
        {"apk": out_apk, "sha256": "0" * 64, "signed": True})
    monkeypatch.setattr(tb_editor.QMessageBox, "information", lambda *a, **k: None)
    ed._build_redist()
    assert captured["stage"].endswith("stage")                       # staged mod_stage passed to builder
    assert (pathlib.Path(ed.mod_stage) / "assets" / "Assets" / "Coefficients" / "helper.json").exists()
