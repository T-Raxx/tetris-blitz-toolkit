import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication, QLabel
import tbmodbuilder, tbcrypt

_app = QApplication.instance() or QApplication([])

def _tab():
    return tbmodbuilder.ModBuilderTab(tbcrypt.load_key(), on_build=lambda cfg: None)

def test_build_config_has_core_mechanics_key():
    t = _tab()
    cfg = t._build_config()
    assert "core_mechanics" in cfg and isinstance(cfg["core_mechanics"], dict)

def test_core_group_enabled_emits_knob():
    t = _tab()
    t.core_on.setChecked(True)
    key = list(t.core_fields.keys())[0]
    t.core_fields[key].setValue(300000)
    cfg = t._build_config()
    assert cfg["core_mechanics"].get(key) == 300000

def test_core_group_disabled_is_empty():
    t = _tab()
    t.core_on.setChecked(False)
    assert t._build_config()["core_mechanics"] == {}

def test_behavior_param_labels_are_human():
    t = _tab()
    grid = t.param_box.layout()
    labels = [grid.itemAt(i).widget().text() for i in range(grid.count())
              if isinstance(grid.itemAt(i).widget(), QLabel)]
    assert all(("_" not in l) for l in labels)
