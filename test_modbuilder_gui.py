import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbcrypt, tbmodbuilder

def test_modbuilder_builds_config_and_calls_back():
    app = QApplication.instance() or QApplication([])
    key = tbcrypt.load_key("key.json")
    captured = {}
    w = tbmodbuilder.ModBuilderTab(key, lambda cfg: captured.update(cfg))
    w.cur_on.setChecked(True)
    w.cur_fields["Coins"].setValue(500000)
    w.show_hidden.setChecked(True)
    cfg = w._build_config()
    assert cfg["currency"]["on"] and cfg["currency"]["coins"] == 500000
    assert cfg["show_hidden"] is True
    w._apply()
    assert captured.get("show_hidden") is True
