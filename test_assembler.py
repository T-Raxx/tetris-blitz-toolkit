import os, pathlib
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbfiles, tbcrypt, tbassembler

def _mosaic_tbfile():
    key = tbcrypt.load_key("key.json")
    src = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients" / "SuperNova.json"
    return tbfiles.load_path(str(src), key)

def test_paint_cell_updates_obj():
    app = QApplication.instance() or QApplication([])
    tb = _mosaic_tbfile()
    changed = []
    a = tbassembler.Assembler(tb, lambda: changed.append(1))
    a.layer = "color"; a.brush = "R"
    a.paint_cell(20, 0)
    assert tb.obj["colors"][20][0] == "R"
    assert changed

def test_paint_tag_places_powerup():
    app = QApplication.instance() or QApplication([])
    tb = _mosaic_tbfile()
    a = tbassembler.Assembler(tb, lambda: None)
    a.layer = "tag"; a.brush = "8"
    a.paint_cell(22, 5)
    assert tb.obj["tags"][22][5] == "8"
