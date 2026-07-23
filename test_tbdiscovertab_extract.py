import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbdiscovertab

_app = QApplication.instance() or QApplication([])

def test_extract_all_dir(tmp_path):
    tab = tbdiscovertab.DiscoveryTab(cache_dir=str(tmp_path / "cache"))
    res = tab._extract_all_dir(str(tmp_path / "out"))
    assert res["count"] > 0 and res["by_type"]["db"] > 0
