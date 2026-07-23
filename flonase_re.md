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

## OPEN (2026-07-23) — restore Flonase's OWN in-game effect (NOT the vortex clone)

### CORRECTION: Flonase HAS a full dedicated in-game asset set (yesterday's "no art" was WRONG)
- `CocosScenes/Scene_Flonace/` : `Layer_FlonaceFx.csb` + `flonase_PU_vfx1..6.plist` (particle emitters,
  each referencing texture `flonase_PU_vfx{N}.png`).
- `imagesSize{150,200}_GamePowerupsFlonase.db` + `...FlonaseAdditive.db` (in-game sprites, 166KB —
  BIGGER than MinoVortex's 56KB db).
- Sounds: `SFX_FLN_MinoPlacement_01..12`, `SFX_FLN_VortexEffect_01`, `SFX_FLN_MinoSwishFast/Slow`.
- `Common0.plist` frames: `Flonase_TagBar.png` (in-play HUD tag) + `flonase.png`.
- **Spelling inconsistency (suspicious, mirrors numMinos/NumMinos):** folder + csb = "Flona**c**e"
  (`Scene_Flonace`, `Layer_FlonaceFx.csb`) but the vfx plists + store sprite = "flona**s**e".
- Asset generations: OLD powerups use `CocosScenes/Scene_X` + `imagesSize_GamePowerupsX.db`
  (Flonace, Spooky, SuperNova, MinoVortex-db, MinoRain, GoldenMino). NEW powerups use
  `Cocos2dxImages/.../PowerUps/X/` (Rocket, Bolt, Cupid, Bday, BDay421). Flonase = OLD style.

### Revised strategy: keep typeId37 + Flonase assets; fix the crash at its source
Flonase's OLD vortex effect (`FUN_009f3e84` class, reads `numMinos`) crashes — most likely loading an
asset by a path whose spelling/name doesn't match the shipped files (Flonase vs Flonace, or a missing
`flonase_PU_vfx*.png` texture) → null → the garbage `1` deref (fault 0x19).

NEXT (needs Ghidra reconnected — MCP was down 2026-07-23 AM):
1. In the OLD effect class (`FUN_009f3e84` + its update/render methods), find the asset-load calls
   (Scene/csb/plist/db path strings) and see the EXACT spelling the code expects.
2. Compare to shipped files. If mismatch → **fix is an ASSET rename/duplication (no native patch)**:
   ship both spellings (Scene_Flonace + Scene_Flonase, Layer_Flona{c,s}eFx.csb) so the code finds it.
3. If the load path is fine but the effect still derefs null → native patch the crashing instruction.
4. Verify Flonase's vfx textures (`flonase_PU_vfx1..6.png`) actually exist (in the .db or loose) — a
   missing particle texture is a strong crash candidate.

### Deferred fallback (if the old effect is unsalvageable)
The typeId31 clone (data reroute, `tbmods.fix_flonase`) already ships crash-free (shop=Flonase,
in-play=vortex). Keep as fallback. The native factory-reroute path (typeId37→new effect) is the
identity-swap alternative; factory switch buried in code-ptr tables (no RTTI/string anchor,
helper field names absent from `.so`, houdini blocks dynamic trace). Fresh angle: powerup-def registry
`DAT_016335f0` (`FUN_00545dcc` build / `FUN_00546db0` lookup) or the piece-lock→effect-create switch.

### Broader goal (2026-07-23): fix MANY powerup crashes
Multiple cut/pre-2016 powerups: some crash (Flonase), some "don't work but don't crash" (load but no
effect). Likely same class of bug (old-effect asset-path/code mismatches). Plan: enumerate all
powerups, classify effect-class health (works / no-op / crashes), fix crashers first. Needs Ghidra.

## Bottle cosmetic gap (2026-07-23) — SHELVED, not worth chasing
Flonase restored + live: no crash, real vortex effect, particles, "FLONASE PARA GANAR" banner all
render. Only the nasal-spray **bottle** sprite (`Image_FlonaseBottle`) does not appear. Ruled out asset
availability: supplied the bottle as (1) loose `flonase_Bottle_idle.png` (exact `.csb` casing, valid
search path `Assets/CocosScenes/` per `FUN_00cb0814`), (2) regenerated `Scene_Flonace.plist`+`.png`
atlas frame (both casings) — the cut file `FUN_009f28fc` loads via `addSpriteFramesWithFile`. ALL failed
while the same `.csb`'s Text + particle-panel widgets render fine → the bottle is suppressed by CODE
(per-widget visibility via `FUN_009f28fc`'s `(*bottleWidget+0x50)` calls / an animation timeline that
never fires for cut content), NOT a missing asset. Fixing = deep RE of `CocosLayerFlonaseView`/
`FlonaseAnimationView` widget-visibility + native-patch the reveal, houdini-blocked, for one decorative
sprite. Decision: SHIP AS-IS. logcat is dead under MuMu (release build logs nothing, buffer empty).

## Status (superseded)
Flonase crash = **FIXED** via data reroute (no crash, live-verified). Above is the open in-game-asset
follow-up. The old section-injection cave notes below are historical.
