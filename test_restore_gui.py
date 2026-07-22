import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbcrypt, tbrestoretab

def test_restore_tab_lists_and_builds(tmp_path):
    app = QApplication.instance() or QApplication([])
    key = tbcrypt.load_key("key.json")
    got = {}
    w = tbrestoretab.RestoreTab(key, lambda ids: got.setdefault("ids", ids), cache_dir=str(tmp_path / "c"))
    assert len(w.cards) >= 10
    uid, cb = w.cards[0]; cb.setChecked(True)
    w._restore()
    assert uid in got["ids"]
