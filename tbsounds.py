"""Enumerate the game's loose sounds and flag orphans (present in the folder but NOT registered in the
game's sound bank = cut/unused, e.g. the leftover '_Retro' theme)."""
import pathlib, json
import tbfiles, tbcrypt

ASSETS = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets"
SOUNDS = ASSETS / "sounds"
COEFF = ASSETS / "Coefficients"
SO = pathlib.Path("..") / "Tetris blitz" / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"

def list_sounds(sounds_dir=SOUNDS):
    d = pathlib.Path(sounds_dir)
    return sorted(d.glob("*.mp3")) if d.exists() else []

def _registry_text():
    """SoundBank.json (the game's sound registry) as text; falls back to the .so strings if the bank
    can't be decrypted."""
    try:
        return json.dumps(tbfiles.load_path(str(COEFF / "SoundBank.json"), tbcrypt.load_key()).obj)
    except Exception:
        return SO.read_bytes().decode("latin1") if SO.exists() else ""

def detect_sounds(sounds_dir=SOUNDS):
    reg = _registry_text()
    out = []
    for p in list_sounds(sounds_dir):
        ref = p.stem in reg
        out.append({"category": "sound", "id": f"sound_{p.stem}", "title": p.stem,
                    "status": "referenced" if ref else "orphan", "source_file": "sounds",
                    "sound_path": str(p)})
    return out
