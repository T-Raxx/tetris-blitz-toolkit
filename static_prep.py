"""Guide Ghidra to the coefficient key: find crypto PLT call-sites and string
xrefs in libTetrisBlitzApp.so, so the RE targets exact functions."""
import pathlib
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN

SO = pathlib.Path("..") / "Tetris blitz" / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"
f = open(SO, "rb")
elf = ELFFile(f)

def sec(name):
    return elf.get_section_by_name(name)

text = sec(".text"); plt = sec(".plt"); rodata = sec(".rodata")
text_addr = text["sh_addr"]; text_data = text.data()
plt_addr = plt["sh_addr"] if plt else None

# --- PLT stub -> symbol map (from .rela.plt JUMP_SLOT order) ---
plt_map = {}
rela = sec(".rela.plt")
dynsym = sec(".dynsym")
if rela and plt_addr is not None:
    relocs = list(rela.iter_relocations())
    # arm64 PLT: 32B header + 16B per stub, stub i == reloc i
    for i, r in enumerate(relocs):
        symname = dynsym.get_symbol(r["r_info_sym"]).name
        stub = plt_addr + 32 + i * 16
        plt_map[stub] = symname

CRYPTO = ("EVP_DecryptInit", "EVP_EncryptInit", "EVP_CipherInit", "EVP_DecryptUpdate",
          "EVP_EncryptUpdate", "AES_set_decrypt_key", "AES_set_encrypt_key",
          "AES_cbc_encrypt", "AES_encrypt", "AES_decrypt", "EVP_aes_128_cbc",
          "EVP_aes_256_cbc", "EVP_aes_128_ecb", "EVP_BytesToKey", "PKCS5_PBKDF2_HMAC",
          "SHA256", "SHA1", "MD5", "EVP_sha", "HMAC")
crypto_stubs = {a: n for a, n in plt_map.items() if any(c in n for c in CRYPTO)}
print("=== crypto PLT stubs present ===")
for a, n in sorted(crypto_stubs.items()):
    print(f"  0x{a:x}  {n}")

# --- interesting rodata strings + their virtual addresses ---
ro_addr = rodata["sh_addr"]; ro = rodata.data()
WANT = (b"GameplayCoefficients", b"CoreMechanicsCoefficients", b"Coefficients",
        b"PlayerData", b"LocalFileHash", b"aes", b"AES", b"decrypt", b"password",
        b"secret", b"salt", b"pbkdf", b"key", b"Cipher", b".json")
str_addrs = {}
for w in WANT:
    start = 0
    while True:
        i = ro.find(w, start)
        if i < 0: break
        # only string-starts (preceded by NUL) to reduce noise
        if i == 0 or ro[i-1] == 0:
            str_addrs.setdefault(w, []).append(ro_addr + i)
        start = i + 1

print("\n=== rodata strings of interest (addr) ===")
for w, addrs in str_addrs.items():
    print(f"  {w.decode(errors='replace')}: {len(addrs)} @ " + ", ".join(f"0x{a:x}" for a in addrs[:6]))

# --- disassemble .text: crypto call-sites + string xrefs ---
md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
md.detail = False
target_strs = set()
for addrs in str_addrs.values():
    target_strs.update(addrs)

adrp_reg = {}
crypto_calls = []   # (call_addr, symbol)
str_xrefs = []      # (instr_addr, string_addr)
for insn in md.disasm(text_data, text_addr):
    m = insn.mnemonic
    if m == "bl":
        tgt = int(insn.op_str.lstrip("#"), 0)
        if tgt in crypto_stubs:
            crypto_calls.append((insn.address, crypto_stubs[tgt]))
    elif m == "adrp":
        try:
            reg, imm = insn.op_str.split(", ")
            adrp_reg[reg] = int(imm.lstrip("#"), 0)
        except Exception:
            pass
    elif m == "add" and "#" in insn.op_str:
        parts = insn.op_str.split(", ")
        if len(parts) == 3:
            dst, src, imm = parts
            if src in adrp_reg and imm.startswith("#"):
                try:
                    a = adrp_reg[src] + int(imm[1:], 0)
                    if a in target_strs:
                        str_xrefs.append((insn.address, a))
                except Exception:
                    pass

addr2str = {a: w.decode(errors="replace") for w, addrs in str_addrs.items() for a in addrs}
print(f"\n=== crypto call-sites in .text ({len(crypto_calls)}) ===")
from collections import Counter
by_sym = Counter(n for _, n in crypto_calls)
for n, c in by_sym.most_common():
    sites = [f"0x{a:x}" for a, s in crypto_calls if s == n][:8]
    print(f"  {n}: {c}x  e.g. " + ", ".join(sites))

print(f"\n=== string xref sites ({len(str_xrefs)}) ===")
for ia, sa in str_xrefs[:40]:
    print(f"  0x{ia:x} -> {addr2str.get(sa,'?')} (0x{sa:x})")
