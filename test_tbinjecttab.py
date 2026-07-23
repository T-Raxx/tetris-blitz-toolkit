import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbinjecttab

_app = QApplication.instance() or QApplication([])

def _first_catalog_index(t):
    for i in range(t.source.count()):
        if t.source.itemData(i) != tbinjecttab.CUSTOM:
            return i
    return -1

def test_tab_lists_catalog_plus_custom():
    t = tbinjecttab.InjectTab(lambda: None)
    labels = [t.source.itemData(i) for i in range(t.source.count())]
    assert tbinjecttab.CUSTOM in labels
    assert any(l != tbinjecttab.CUSTOM for l in labels)          # real catalog sources present
    assert t.base.count() == len(__import__("tbinject").base_targets())

def test_add_and_selection():
    t = tbinjecttab.InjectTab(lambda: None)
    i = _first_catalog_index(t); assert i >= 0
    t.source.setCurrentIndex(i); t.base.setCurrentIndex(0)
    t._add()
    sel = t.selection()
    assert len(sel) == 1 and set(sel[0]) == {"base", "source"}
    assert sel[0]["base"] == t.base.itemData(0)

def test_one_injection_per_base_color():
    t = tbinjecttab.InjectTab(lambda: None)
    i = _first_catalog_index(t)
    t.source.setCurrentIndex(i); t.base.setCurrentIndex(0)
    t._add(); t._add()                                           # same base twice
    assert len(t.selection()) == 1                              # replaced, not duplicated

def test_remove(self=None):
    t = tbinjecttab.InjectTab(lambda: None)
    t.source.setCurrentIndex(_first_catalog_index(t)); t.base.setCurrentIndex(0)
    t._add()
    t.list.setCurrentRow(0); t._remove()
    assert t.selection() == []
