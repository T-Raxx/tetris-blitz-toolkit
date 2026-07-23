import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
import tbdiscovertab, tbsounds

_app = QApplication.instance() or QApplication([])

def test_sound_in_cats():
    assert "sound" in tbdiscovertab.CATS

def test_play_sets_source(tmp_path):
    tab = tbdiscovertab.DiscoveryTab(cache_dir=str(tmp_path / "cache"))
    mp3 = str(tbsounds.list_sounds()[0])
    tab._play(mp3)                                    # must not raise; sets the shared player source
    assert tab._player.source().toLocalFile().endswith(".mp3")
