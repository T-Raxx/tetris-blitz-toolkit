# Flonase crash — RE notes (WIP)

## Crash located
- SIGSEGV (signal 11, SEGV_MAPERR), **fault addr 0x19**, GLThread (render thread).
- Backtrace (houdini, ARM-translated, approximate): `#00 0xb8bf54` inside `FUN_00b8bf0c` (Ghidra),
  caller `#01 0xa98b2c` in `FUN_00a989b4` (render dispatcher), reached via
  `Java_com_ea_blast_AndroidRenderer_NativeOnDrawFrame`.
- `FUN_00a989b4` iterates renderables and calls a vtable method `(*obj + 0x350)(obj, p2, p3, uVar3)`;
  it null-checks `obj == 0` before calling. So the object is non-null — but the tombstone shows
  **x19 = 0x1** and **x0 = 0x1**: the object pointer is a **garbage value `1`** that passes the
  `== 0` null-check yet is not a real pointer. fault addr `0x19` ≈ `1 + 0x18` → a `[ptr+0x18]` load
  on the garbage pointer.

## Why it crashes (hypothesis)
Flonase (uId 45) is a Mino Vortex reskin whose setup code was cut pre-2016. Its renderable / a field
is left as an uninitialized/sentinel value `1` (likely a stale bool or freed slot) that current code
dereferences as a pointer → SEGV. Consistent with "same as Mino Vortex but crashes on trigger".

## Blockers for a simple byte-patch fix
1. **Unreliable ground truth:** under MuMu/houdini ARM→x86 translation, the reported crash pc is a
   register `mov` (cannot fault) and the register snapshot is translated state — so the exact faulting
   instruction/source of the `1` isn't pinned by static analysis alone. Needs a real ARM debugger or
   a targeted trace, not the houdini backtrace.
2. **No code cave:** `.text` (0x47b520–0x1145648) has **no run of ≥32 zero bytes** — nowhere to inject
   a null-guard stub inline. A guard/redirect would require ELF section-injection (e.g. LIEF adding a
   segment), a heavier patcher than the current `{offset, orig, patch}` byte-writer.

## Paths forward (for a real fix)
- **A. Trace the garbage source:** find where the `1` pointer originates (the uninit field read) and
  patch that single instruction to yield `0` → the caller's existing `== 0` check then skips the
  Flonase object cleanly (an inline single-instruction patch, no cave). Needs reliable RE of the
  object-construction path.
- **B. Section-injection patcher:** extend the byte-patch engine to add a code segment via LIEF,
  giving cave space for a proper null/`1`-guard stub redirected from the render method.
- **C. Accept WIP:** ship the native-patch framework; label Flonase (CRASHES GAME) stays (already done
  in restoration); revisit the fix later.

## Status
Framework (tbnative + Native tab) shipped and unit-tested. Flonase native fix = **WIP** pending the
decision above.
