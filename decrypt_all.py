import pathlib, json, tbcrypt
SRC = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"
OUT = pathlib.Path("decrypted"); OUT.mkdir(exist_ok=True)
k = tbcrypt.load_key()
ok, bad = [], []
for f in sorted(SRC.glob("*.json")):
    d = f.read_bytes()
    if len(d) % 16 or len(d) < 16:
        bad.append(f"{f.name}: not block-aligned ({len(d)}B)"); continue
    try:
        text = tbcrypt.decrypt_json(d, k)
        json.loads(text)
        (OUT / f.name).write_text(text, encoding="utf-8")
        ok.append(f.name)
    except Exception as e:
        bad.append(f"{f.name}: {e}")
print(f"decrypted OK: {len(ok)}")
for b in bad: print("  SKIP/FAIL", b)
