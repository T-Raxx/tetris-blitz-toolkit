# Tetris Blitz — Redistributable APK Builder

Standalone tool. Repacks the base APK tree with your mods (`mod_stage`) and signs
**v1 + v2 + v3** (via `uber-apk-signer`, zipalign included), producing an APK that installs
on **real, non-rooted hardware**. Android 12+ rejects v1-only signatures — MuMu tolerated
them, real phones don't.

## Requirements
- Java in PATH (`java -version`). Any JDK 8+.
- Internet on first run (downloads `uber-apk-signer` into `tools/`).

## Build
```
python apkbuild.py --mods ../tbcheat/mod_stage --out dist/tetrisblitz-modded.apk
```
Options:
- `--base <dir>`  unpacked base APK tree (default `../Tetris blitz`)
- `--ks <file>`   your keystore (alias `tb`, storepass/keypass `android`); default = uber debug key
- `--no-sign`     repack only (unsigned)

Output: signed APK in `dist/` + printed `sha256` + signature verification.

The editor's **"Build Redistributable APK"** button calls this after staging every tab's mods.

## Install on a non-rooted phone
1. Copy the APK to the phone (USB, or `adb install dist/tetrisblitz-modded.apk`).
2. Enable **Install unknown apps** for your file manager / browser.
3. Tap the APK → install. Uninstall the store version first if signatures differ.

## Scope
The APK bakes in **coefficient + native + asset** mods (unlock-all-free, powerup behaviors,
FPS cap, mino injection). **Save-based mods (currency, the Samsung save)** are NOT in the APK —
non-rooted devices can't receive a save push; use adb/root and the editor's **Save** tab for that.

`dist/` and `tools/` are build artifacts (git-ignored).
