# TB File Editor

Decrypt / edit / re-encrypt Tetris Blitz coefficient files + the live `PlayerData` save
(AES-128-CBC, key recovered via Ghidra).

## Run
    python tb_editor.py        (or double-click run_editor.bat)

## Deps
    pip install PyQt6 pycryptodome

## Use
- **Left list** = APK coefficient files (`Coefficients/*.json`). Double-click to open.
- **Pull save** grabs the live save from MuMu (`emulator-5554`); edit; **Push save** writes it
  back. A timestamped backup lands in `tbcheat/backups/` before every push. Restart the game to
  load changes.
- **Smart tab** = friendly controls: currency spinboxes with **MAX**, powerup inventory grid,
  coefficient "Quick Cheats" (coin awards, energy).
- **Raw JSON tab** = full edit of any field.
- **Badge** shows format + `✓` when the file round-trips byte-identical.

## Formats (handled automatically)
- Coefficient: `json + 0x00 + PKCS7`
- Save: `json + 0x00 + binary trailer` (block-aligned; trailer preserved)

## Notes
- Save edits that change JSON length zero-align the trailer — verify once in-game.
- Shop / Bonus Blitz files are editable via Raw JSON but get no smart panel (server-dependent).
- `key.json`, pulled saves, and `backups/` are gitignored (local only).
