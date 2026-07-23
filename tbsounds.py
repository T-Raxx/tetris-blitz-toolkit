"""Enumerate the game's loose sounds and flag orphans (present but unreferenced by the native lib)."""
import pathlib

ASSETS = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets"
SOUNDS = ASSETS / "sounds"
SO = pathlib.Path("..") / "Tetris blitz" / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"

def list_sounds(sounds_dir=SOUNDS):
    d = pathlib.Path(sounds_dir)
    return sorted(d.glob("*.mp3")) if d.exists() else []

def detect_sounds(sounds_dir=SOUNDS, so_path=SO):
    so = pathlib.Path(so_path).read_bytes() if pathlib.Path(so_path).exists() else b""
    out = []
    for p in list_sounds(sounds_dir):
        ref = p.stem.encode() in so
        out.append({"category": "sound", "id": f"sound_{p.stem}", "title": p.stem,
                    "status": "referenced" if ref else "orphan", "source_file": "sounds",
                    "sound_path": str(p)})
    return out
