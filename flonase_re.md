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

## Iteration 1 (2026-07-22) — object-validity guard did NOT fix it
- Section-injection patcher built (LIEF+keystone, shift-aware). Cave stub verified correct:
  `cmp x0,#0x1000; b.lo skip; stp d9,d8,[sp,#-0x70]!; b entry+4; skip: ret` at `FUN_00b8bf0c`.
  Built + installed + booted clean.
- Triggered Flonase in-game → **still crashes.** So the fault is NOT `FUN_00b8bf0c` entered with a
  garbage `x0` — the houdini backtrace/regs were misleading (translated state). The real fault is
  elsewhere (deeper callee / different function / pre-2016 logic path).
- Correct next step needs reliable ground truth: an actual ARM debugger breakpoint (Ghidra debugger
  or gdbserver) at the fault, or bisecting via multiple guarded candidates — not the houdini backtrace.

## RESOLVED (2026-07-22) — root cause = typeId routes to a broken vortex effect
The houdini backtrace (FUN_00b8bf0c) was a red herring (the earlier guard was correctly ineffective).
Real cause found by comparing Flonase (uId45) against its working behavior-twin Mino Vortex (uId38):

- Flonase is a half-finished **Mino Vortex reskin**. Its params are the vortex params but keyed
  **`numMinos`** (lowercase) — read only by the **deprecated OLD vortex effect** class
  (`FUN_009f3e84`). Current Mino Vortex uses **`NumMinos`** + the **NEW effect** (`FUN_00a10e98`).
- The effect class is selected by **`typeId`**: Flonase = 37 (old/broken), Mino Vortex = 31 (new/works).
  Both param loaders default safely, so the crash is in the OLD effect's *execution/render*, which was
  never finished (likely dereferences a Flonase in-game asset that doesn't exist → the garbage `1`
  pointer / fault addr 0x19). Prior restoration already gave Flonase Mino Vortex perks and it STILL
  crashed → not perks, not param-defaults → the typeId→effect routing is the cause.
- **Live-verified A/B:** typeId37 crashes on trigger; typeId31 does not.

### Fix shipped (data layer) — `tbmods.fix_flonase`
Reroute Flonase to Mino Vortex's working effect: typeId 37→31, param `numMinos`→`NumMinos`, inherit
Mino Vortex perks, enable + free. Result (live-verified): **no crash**; shop keeps Flonase's icon+name
(`iconBasePath`/`name` are Java/store-side — NOT in the native `.so`), in-play shows the vortex effect
(typeId-driven native visuals; Flonase had no unique in-game art). Wired into Mod Builder
("Fix Flonase crash"). No native patch needed.

### Identity note (why not a native patch)
Native powerup visuals are typeId-keyed (`iconBasePath` absent from the `.so`). Preserving the in-play
visual as "Flonase" would require the typeId→effect **factory** switch (case 37 → new vortex class),
which is buried in large code-pointer tables with no clean RTTI and no string anchor
(helper.json field names aren't in the `.so`); dynamic tracing is blocked by houdini x86 JIT. Not worth
it — the vortex is the intended effect and shop identity is already preserved.

## Status (superseded)
Flonase crash = **FIXED** via data reroute. The old section-injection cave notes below are historical.
