import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication, QPushButton, QLineEdit
import tbassembler, tbmosaic

_app = QApplication.instance() or QApplication([])

def _assembler():
    obj = {"colors": ["Y.", ".."], "tags": ["4.", ".."], "groups": ["..", ".."]}
    tb = type("T", (), {"obj": obj})()
    return tbassembler.Assembler(tb, lambda: None)

def _brush_labels(a):
    lay = a.palette_box.layout()
    return [lay.itemAt(i).widget().text() for i in range(lay.count())
            if isinstance(lay.itemAt(i).widget(), QPushButton)]

def test_color_palette_shows_all_seven():
    a = _assembler(); a._set_layer("color")
    labels = [l for l in _brush_labels(a) if l != "erase (.)"]
    assert len(labels) == len(tbmosaic.symbols("colors")) == 7

def test_tag_palette_shows_all_tags():
    a = _assembler(); a._set_layer("tag")
    labels = [l for l in _brush_labels(a) if l != "erase (.)"]
    assert len(labels) == len(tbmosaic.symbols("tags"))          # 9 powerups + p + s
    assert any("Bomb" in l for l in labels) and any("Special" in l for l in labels)

def test_group_layer_free_char_brush():
    a = _assembler(); a._set_layer("group")
    lay = a.palette_box.layout()
    has_lineedit = any(isinstance(lay.itemAt(i).widget(), QLineEdit) for i in range(lay.count()))
    assert has_lineedit
