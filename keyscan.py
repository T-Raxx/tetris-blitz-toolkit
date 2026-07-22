"""Known-plaintext AES key search over libTetrisBlitzApp.so.

Coefficient files are AES-CBC with a fixed key. In CBC:
    P1 = AES_ECB_decrypt(K, C1) XOR C0
which needs only ciphertext (no IV). Coefficient plaintext is JSON (printable).
So: scan the binary's constant data for a 16/32-byte window K that turns
block 1 of a real coefficient file into printable text. Verify against a
second file (different plaintext group) to kill false positives.
"""
import pathlib, sys, time
from Crypto.Cipher import AES

ROOT = pathlib.Path("..") / "Tetris blitz"
SO = (ROOT / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so").read_bytes()
COEFF = ROOT / "assets" / "Assets" / "Coefficients"

f1 = (COEFF / "GameplayCoefficients.json").read_bytes()          # group 1
f2 = (COEFF / "CoreMechanicsCoefficients.json").read_bytes()     # group 2
C0a, C1a, C2a = f1[0:16], f1[16:32], f1[32:48]
C0b, C1b = f2[0:16], f2[16:32]

# many files for a sharp multi-file PKCS7 filter: (last_block, prev_block)
FILES = []
for p in sorted(COEFF.glob("*.json")):
    b = p.read_bytes()
    if len(b) >= 32 and len(b) % 16 == 0:
        FILES.append((p.name, b[-16:], b[-32:-16]))
FILES = FILES[:14]
print(f"[i] using {len(FILES)} files for multi-file PKCS7 filter")

def printable(bs):
    return sum(1 for b in bs if b in (9, 10, 13) or 32 <= b < 127)

def xorb(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def valid_pkcs7(last):
    n = last[-1]
    return 1 <= n <= 16 and all(b == n for b in last[-n:])

def test_key(K):
    # Multi-file PKCS7 oracle: correct key yields valid PKCS7 on the last block
    # of EVERY coefficient file (ciphertext-only, compression-agnostic).
    npass = 0
    for name, cn, cprev in FILES:
        last = xorb(AES.new(K, AES.MODE_ECB).decrypt(cn), cprev)
        if not valid_pkcs7(last):
            return None
        npass += 1
    P1 = xorb(AES.new(K, AES.MODE_ECB).decrypt(C1a), C0a)
    return (npass, printable(P1), P1)

def good_window(w):
    # AES keys are high-entropy: many distinct bytes, no long zero runs
    if b"\x00\x00\x00" in w:
        return False
    return len(set(w)) >= len(w) * 0.8

def scan():
    hits = []
    t0 = time.time()
    for size in (32, 16):
        n = len(SO) - size
        for off in range(0, n, 4):         # keys are aligned
            w = SO[off:off + size]
            if not good_window(w):
                continue
            r = test_key(w)
            if r:
                hits.append((r[0], r[1], size, off, r[2]))
        print(f"  scanned AES{size*8} in {time.time()-t0:.1f}s, hits so far={len(hits)}")
    hits.sort(reverse=True)
    return hits

if __name__ == "__main__":
    hits = scan()
    print(f"\n=== {len(hits)} candidate(s) (npass, printable) ===")
    for npass, pr, size, off, P1 in hits[:15]:
        print(f"AES{size*8} off=0x{off:x} files_passed={npass}/{len(FILES)} P1printable={pr}")
        print(f"   key={SO[off:off+size].hex()}")
        print(f"   P1={P1!r}")
