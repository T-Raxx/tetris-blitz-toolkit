import os, pathlib
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tb_editor
from PyQt6.QtWidgets import QApplication

COEFF = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"

def test_editor_opens_and_loads_coeff(tmp_path):
    app = QApplication.instance() or QApplication([])
    w = tb_editor.Editor()
    w.open_local(str(COEFF / "GameplayCoefficients.json"))
    assert w.current is not None and w.current.obj["Version"] == "41000"
    w.current.obj["Version"] = "99999"
    out = tmp_path / "out.json"
    w.save_local(str(out))
    import tbfiles, tbcrypt
    assert tbfiles.load_bytes(out.read_bytes(), tbcrypt.load_key("key.json")).obj["Version"] == "99999"

def test_pull_loads_save_into_editor(monkeypatch):
    app = QApplication.instance() or QApplication([])
    import tbadb, pathlib
    save_bytes = pathlib.Path("save_PlayerData.bin").read_bytes()
    monkeypatch.setattr(tbadb, "device", lambda run=None: "emulator-5554")
    monkeypatch.setattr(tbadb, "pull", lambda remote, run=None: save_bytes)
    w = tb_editor.Editor()
    w._pull()
    assert w.current is not None and w.current.fmt == "save" and "Coins" in w.current.obj

def test_mosaic_file_shows_assembler():
    app = QApplication.instance() or QApplication([])
    import tbassembler
    w = tb_editor.Editor()
    w.open_local(str(COEFF / "SuperNova.json"))
    holder = w.smart_holder.layout()
    widgets = [holder.itemAt(i).widget() for i in range(holder.count())]
    assert any(isinstance(x, tbassembler.Assembler) for x in widgets)

def test_editor_has_discovery_tab():
    app = QApplication.instance() or QApplication([])
    w = tb_editor.Editor()
    titles = [w.tabs.tabText(i) for i in range(w.tabs.count())]
    assert "Discovery" in titles

def test_stage_for_build_writes_override(tmp_path):
    app = QApplication.instance() or QApplication([])
    import pathlib, tbfiles, tbcrypt
    w = tb_editor.Editor()
    w.mod_stage = str(tmp_path / "stage")
    w.open_local(str(COEFF / "helper.json"))
    w.current.obj["helpers"][0]["price"] = 0
    w._stage_current()
    staged = pathlib.Path(w.mod_stage) / "assets" / "Assets" / "Coefficients" / "helper.json"
    assert staged.exists()
    tb = tbfiles.load_bytes(staged.read_bytes(), tbcrypt.load_key("key.json"))
    assert tb.obj["helpers"][0]["price"] == 0
