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
