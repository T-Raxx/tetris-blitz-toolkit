# Ghidra Targets — Tetris Blitz coefficient AES key

**Binary:** `Tetris blitz/lib/arm64-v8a/libTetrisBlitzApp.so` (AARCH64:LE:64:v8A, 22 MB).
Import → auto-analyze → run "Decompiler Parameter ID" + "AARCH64 constant reference analyzer".

## What we know (from recon)
- Coefficient files = AES-CBC, **fixed key + fixed IV**, block size 16, **AES-256 or 128** (both
  `EVP_aes_*_cbc` names in the OpenSSL string table). Plaintext = uncompressed pretty JSON.
- **OpenSSL is statically linked** — NO PLT/dynamic crypto imports. AES code is internal; find it by
  the AES S-box (`63 7c 77 7b f2 6b 6f c5 ...`) or Te0/Td0 tables, or via the loader below.
- **Key is derived/obfuscated at runtime** (no embedded contiguous key: a 14-file PKCS7 + printable
  known-plaintext scan of the whole `.so` found nothing). So the RE goal is the **key-derivation**
  code that runs just before the AES-CBC decrypt, then reproduce it in Python.
- Key is **fixed across runs** (files encrypted once at build) → we need the key *value* once.

## Entry points — coefficient loader (xrefs to filename strings)
Filename string addrs: `GameplayCoefficients` @ 0x1046276/0x1047c00/0x1047dd0/... ;
`CoreMechanicsCoefficients` @ 0x104622d/0x1046983/0x10539bd/...

Code xref clusters (decompile these; find the one that reads the file bytes then AES-decrypts):
- **0x635400–0x636500** — 8× GameplayCoefficients refs (0x6354b0, 0x6355c4, 0x635678, 0x636244,
  0x63627c, 0x63636c, 0x636420). **Best candidate for the read+decrypt path.**
- 0x50a958, 0x50ab54, 0x50d3b8, 0x50d3f0 — Gameplay refs (file-read region).
- 0x4668e0, 0x466910, 0x4673e4, 0x467414 — both filenames (registration/table).
- 0x48722c, 0x69e6a4, 0x752e3c — secondary.

## RE procedure
1. Decompile a loader cluster above. Trace the buffer holding raw file bytes.
2. Follow it into the decrypt call. Because AES is internal, look for: a function taking
   (key, iv, in, out, len) shape, or calls to an internal `AES_set_decrypt_key` / `AES_cbc_encrypt`
   equivalent (locate those by the S-box/Te tables, then xref their callers).
3. At the decrypt call, recover the **key** and **IV** arguments. They may be:
   - a static buffer built by an obfuscation routine (XOR/rotate of a rodata blob), or
   - EVP_BytesToKey/PBKDF2 over a hardcoded password+salt (reproduce the KDF in Python), or
   - assembled from split constants.
4. Reproduce in Python → write `key.json` `{algo,keysize,mode:CBC,key_hex,iv_hex,padding}`.

## Instant verification oracle (we have known-plaintext)
Decrypted coefficient JSON is live in RAM (proven). To verify ANY candidate key without guessing:
`AES-CBC-decrypt(GameplayCoefficients.json)` must yield text starting with `{` and `json.loads()`-able.
`tbcheat/keyscan.py` already has the CBC/PKCS7 primitives; drop the key in and check.

## Faster backup if RE drags (not the chosen path, but available)
`aeskeyfind`-style scan of a process memory dump: dump the running game's `rw-` ranges, validate any
176/240-byte region as a valid AES key schedule, extract candidate keys, test each with the oracle
above. Recovers the derived key from RAM in minutes without full RE.

## Side data captured (system-libcrypto, NOT the coefficient key — may be save/network keys)
- Cand A: key `a295266a9f0828e09654fa4124eabb333f6f466453d22fdf091b3db8190b58ab`
  iv `104a47b02065d14875f200e34641f44a` (AES-256, high entropy).
- Cand B: key `5a584967625746796132563049476c7501c1...` iv `5756756443776754573971595735484b`
  (key bytes are ASCII/base64 — a text-processing subsystem).
Revisit these for the Task-6 save file if it uses a different key than the coefficients.
