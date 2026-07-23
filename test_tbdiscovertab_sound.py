import os, json, pathlib
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbdiscovertab, tbsounds

_app = QApplication.instance() or QApplication([])

def test_two_subtabs_assets_and_sounds(tmp_path):
    tab = tbdiscovertab.DiscoveryTab(cache_dir=str(tmp_path / "cache"))
    assert tab.subtabs.count() == 2
    assert tab.subtabs.tabText(0) == "Assets" and tab.subtabs.tabText(1) == "Sounds"

def test_sounds_view_has_only_sounds_and_plays(tmp_path):
    tab = tbdiscovertab.DiscoveryTab(cache_dir=str(tmp_path / "cache"))
    assert tab.sounds.findings and all(f["category"] == "sound" for f in tab.sounds.findings)
    assert all(f["category"] != "sound" for f in tab.assets.findings)   # sounds excluded from assets
    tab._play(str(tbsounds.list_sounds()[0]))
    assert tab._player.source().toLocalFile().endswith(".mp3")

def test_ensure_fresh_rebuilds_when_stale(tmp_path):
    tab = tbdiscovertab.DiscoveryTab(cache_dir=str(tmp_path / "cache"))
    cat = pathlib.Path(tab.cache_dir) / "catalog.json"
    os.utime(cat, (0, 0))                                   # make catalog ancient -> stale vs detectors
    tab.ensure_fresh()
    assert cat.stat().st_mtime > 0 and tab.findings         # rebuilt + reloaded
