# Tetris Blitz Modkit

A reverse-engineering + modding toolkit for **EA's Tetris Blitz** — a discontinued,
server-offline, single-player Android game. It decrypts the game's data layer, gives you a
GUI to edit it, revives cut content, patches the native engine, injects custom art, edits
your device save, and repacks a redistributable, properly-signed APK.

> **This repo ships the tooling, not the game.** It contains **no** EA binaries, assets,
> coefficients, or encryption key. You supply your own legally-obtained copy of the game.
> See **Legal** below.

## Download

Prebuilt binaries for **Windows** and **macOS** are attached to each
[Release](../../releases) (built by CI with PyInstaller), alongside a source archive. They
still need a JDK, `adb`, and your own game files (see **Setup**). Or run from source below.

## What it does

- **Crypto layer** (`tbcrypt`, `tbfiles`) — AES-128-CBC round-trip of the game's encrypted
  JSON coefficients and save files (byte-identical re-encrypt).
- **File editor** (`tb_editor`) — dark-themed PyQt6 GUI: smart panels, raw JSON with live
  validity, device pull/push.
- **Mosaic assembler** (`tbmosaic`, `tbassembler`) — paint finisher/powerup matrices with
  the correct **per-finisher palette** (RE'd in `docs`), real extracted sprites.
- **Content discovery** (`tbdiscover`, `tbgallery`) — surface hidden powerups, orphan
  sprites, unused modes, `.db` atlas assets, and sounds.
- **Mod builder** (`tbmods`) — currency, unlock-all, powerup behavior, core-mechanics knobs.
- **Restore** (`tbrestore`) — re-enable disabled/cut content (typeId-aware).
- **Native patches** (`tbnative`) — value-templated arm64 patches: fixed powerup spawn rate,
  on-board cap removal, FPS uncap, mino texture swaps.
- **Mino injection** (`tbinject`) — pixel-inject any image (real hidden textures or your own
  PNG) over a base-color mino frame in the Common atlas.
- **Save editor** (`tbsave`) — use your own pulled device save as the mod base (genuine
  unlocks preserved), edit currency / unlocks / helpers, export or push.
- **APK builder** (`apkbuilder/`) — repack + sign **v1+v2+v3** (real, non-rooted phones
  reject v1-only) into a shareable APK.

## Setup

Requires Python 3.11+, and for the full feature set:

```
pip install PyQt6 Pillow pycryptodome keystone-engine lief
```

Plus `adb` (device I/O) and a JDK with `java` on PATH (APK signing).

You must provide, locally and **never committed**:

1. **The base APK tree** — unpack your own `Tetris Blitz.apk` into a sibling `Tetris blitz/`
   folder.
2. **The AES key** — recovered automatically from *your own* game files (no EA secret is
   shipped). Run:
   ```
   python tbkeyfind.py
   ```
   It scans your `libTetrisBlitzApp.so` for the key and validates it against one of your
   encrypted coefficients, writing `key.json`. The editor also does this on first launch (or
   via the **Extract key** button). Manual method, if you prefer: `ghidra_targets.md`.
3. **Your device save** (optional, for the Save tab) — pull it and point `TB_SAVE_DIR` at it.

Run the GUI:

```
python tb_editor.py          # or: ./run_editor.sh  (macOS/Linux)  |  run_editor.bat  (Windows)
```

Works on Windows, macOS, and Linux — JDK tools (`jarsigner`/`keytool`) and `java` are resolved
from `PATH` / `JAVA_HOME` / common JDK install dirs automatically.

## Tests

```
pytest -q
```

Tests that need your local save / atlas are auto-skipped when absent.

## Legal

This is an independent, non-commercial reverse-engineering and interoperability tool for a
**discontinued, offline, single-player** game, intended for use with a copy you legally own.

- It bundles **no** EA/Tetris code, art, audio, data, or keys. All such assets are
  git-ignored; you extract them from your own installation.
- Not affiliated with, endorsed by, or associated with Electronic Arts or The Tetris Company.
  "Tetris" and "Tetris Blitz" are trademarks of their respective owners.
- Provided for educational and personal use. You are responsible for complying with the
  game's EULA and your local laws.

Tool code is MIT-licensed (`LICENSE`). The license covers this repository's original code
only — not any third-party game content it may operate on.
