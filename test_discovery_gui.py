import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbdiscovertab

def test_discovery_tab_loads_cards():
    app = QApplication.instance() or QApplication([])
    w = tbdiscovertab.DiscoveryTab()          # builds catalog on first run
    assert len(w.findings) > 100
    assert w.grid.count() > 0
