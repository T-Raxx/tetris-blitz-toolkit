import os, pathlib
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tbnative
from PyQt6.QtWidgets import QApplication
import tbnativetab

_app = QApplication.instance() or QApplication([])

def test_fps_to_ms():
    assert tbnativetab.fps_to_ms(30, False) == 33
    assert tbnativetab.fps_to_ms(60, False) == 17
    assert tbnativetab.fps_to_ms(120, False) == 8
    assert tbnativetab.fps_to_ms(60, True) == 0          # uncapped

def test_fps_cap_patch_assembles():
    patches = tbnative.load_patches()
    p = next(x for x in patches if x["id"] == "fps_cap")
    w = p["writes"][0]
    assert tbnative.assemble_write(w, {"ms": 16}).hex() == "080280d2"    # mov x8,#16
    assert tbnative.assemble_write(w, {"ms": 0}).hex() == "080080d2"     # mov x8,#0 (uncapped)

def test_apply_fps_cap_uncapped(tmp_path):
    src = str(tbnative.SRC_SO); patches = tbnative.load_patches()
    out = tbnative.apply_patches(["fps_cap"], patches, src_so=src,
                                 out_so=str(tmp_path / "o.so"), values={"fps_cap": {"ms": 0}})
    b = pathlib.Path(out).read_bytes()
    assert b[0xca2470 - 0x100000:0xca2470 - 0x100000 + 4].hex() == "080080d2"

def test_native_tab_fps_control_passes_ms():
    got = {}
    tab = tbnativetab.NativeTab(lambda ids, values: got.update(ids=ids, values=values))
    for pid, cb in tab.boxes:
        if pid == "fps_cap":
            cb.setChecked(True)
    # uncapped toggle lives next to the fps spinbox; set the fps then apply capped=120
    tab.param_ctrls["fps_cap"].setValue(120)
    tab._apply()
    assert got["values"]["fps_cap"]["ms"] == 8
