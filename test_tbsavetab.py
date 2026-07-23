import os, pathlib, pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbsavetab, tbsave, tbcrypt, tbfiles

pytestmark = pytest.mark.skipif(not (tbsave.BASE_DIR / "PlayerData.json").exists(),
                                reason="Samsung save base not present")
_app = QApplication.instance() or QApplication([])
KEY = tbcrypt.load_key("key.json")

def test_tab_loads_base_and_populates_spins():
    t = tbsavetab.SaveTab(KEY)
    assert t.base is not None
    assert t.spins["Coins"].value() == tbsave.playerdata(t.base)["Coins"]
    assert "Level=193" in t.status.text()

def test_max_currency_button():
    t = tbsavetab.SaveTab(KEY)
    t._max_currency()
    assert all(sb.value() == tbsave.MAXINT for sb in t.spins.values())

def test_export_writes_modded_save(tmp_path, monkeypatch):
    t = tbsavetab.SaveTab(KEY)
    t.spins["Coins"].setValue(123456); t.unlock_all.setChecked(True)
    monkeypatch.setattr(tbsavetab.QFileDialog, "getExistingDirectory", lambda *a, **k: str(tmp_path))
    monkeypatch.setattr(tbsavetab.QMessageBox, "information", lambda *a, **k: None)
    t._export()
    pd = tbfiles.load_path(str(tmp_path / "PlayerData.json"), KEY).obj
    assert pd["Coins"] == 123456
    assert 18 in {u["Id"] for u in pd["Unlocks"]}                # unlock_all applied
    assert (tmp_path / "NarcSave.json").exists()                 # NarcSave exported too
