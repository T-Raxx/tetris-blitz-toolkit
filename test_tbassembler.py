import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication, QPushButton, QLineEdit, QLabel
import tbassembler, tbmosaic

_app = QApplication.instance() or QApplication([])

def _label_texts(a):
    lay = a.palette_box.layout()
    return [lay.itemAt(i).widget().text() for i in range(lay.count())
            if isinstance(lay.itemAt(i).widget(), QLabel)]

def _assembler(name=None):
    obj = {"colors": ["Y.", ".."], "tags": ["4.", ".."], "groups": ["..", ".."]}
    tb = type("T", (), {"obj": obj})()
    return tbassembler.Assembler(tb, lambda: None, name=name)

def _brush_labels(a):
    lay = a.palette_box.layout()
    return [lay.itemAt(i).widget().text() for i in range(lay.count())
            if isinstance(lay.itemAt(i).widget(), QPushButton)]

def test_color_palette_no_finisher_shows_all_twelve():
    a = _assembler(); a._set_layer("color")
    labels = [l for l in _brush_labels(a) if l != "erase (.)"]
    assert len(labels) == len(tbmosaic.symbols("colors")) == 12

def test_color_palette_finisher_scopes_to_its_own_chars():
    a = _assembler(name="GiftTree.json"); a._set_layer("color")
    labels = [l for l in _brush_labels(a) if l != "erase (.)"]
    own = [l for l in labels if l[0] in "GWY"]
    assert a.finisher == "GiftTree"
    assert len(own) == 3                                          # G, W, Y shown first
    assert any(l.startswith("W") and "Wood" in l for l in labels)

def test_tag_palette_shows_all_tags():
    a = _assembler(); a._set_layer("tag")
    labels = [l for l in _brush_labels(a) if l != "erase (.)"]
    assert len(labels) == len(tbmosaic.symbols("tags"))          # 12 powerups + p + s
    assert any("Bomb" in l for l in labels) and any("Progressive" in l for l in labels)

def test_tag_layer_shows_award_note():
    a = _assembler(name="SuperNova.json"); a._set_layer("tag")
    txt = " ".join(_label_texts(a))
    assert "OTORGA" in txt and "Unlock everything" in txt          # explains tags are finisher rewards
    assert not any("cosmética" in t for t in _label_texts(a))      # SuperNova awards powerups

def test_tag_layer_warns_cosmetic_matrix():
    a = _assembler(name="BlitzinMatrix.json"); a._set_layer("tag")
    assert any("cosmética" in t for t in _label_texts(a))          # BlitzinMatrix ships no powerup tags

def test_color_layer_has_no_tag_note():
    a = _assembler(name="SuperNova.json"); a._set_layer("color")
    assert not any("OTORGA" in t for t in _label_texts(a))

def test_group_layer_free_char_brush():
    a = _assembler(); a._set_layer("group")
    lay = a.palette_box.layout()
    has_lineedit = any(isinstance(lay.itemAt(i).widget(), QLineEdit) for i in range(lay.count()))
    assert has_lineedit
