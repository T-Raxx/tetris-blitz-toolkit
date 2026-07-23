# PowerUpPace — RE notes

## What it is
`CoreMechanicsCoefficients.PowerUpPace` (JSON default **7**) is **not** a percentage. It is the size of
a **shuffle bag** (`EA::TetrisBlitz::BlitzPowerUpPaceBag`).

- Loaded into the CoreMechanics coefficient struct at **field offset 0x5c** by `FUN_00f14cb0`
  (`GoldenMinoPace` → 0x60, right after it).
- Passed to the bag constructor `FUN_00f4f484(this, ctx, pace)` (vtable `PTR_FUN_015ffca8`):
  - `this+0x54 = pace`, `this+0x4c = pace`, `this[10] (0x50) = 1`
  - fills `this+0x10..` with `1,2,…,pace` — the bag slots.
- Mechanic: **one powerup guaranteed per `pace` pieces, at a random piece within each window of
  `pace`.** Effective per-piece rate ≈ `1/pace` (Pace 7 ≈ 14%/piece, Pace 2 = 50%, Pace 1 = every piece).
  It is a bag draw, NOT an independent per-piece dice roll — only `1/N` rates are achievable.

## Runtime override (Daily Challenge)
In the board setup `FUN_00f44950`: `if (param_2[0xc] != 0) FUN_00f16c30(coreMech, param_2[0xc]);`
applies a Daily-Challenge override to the CoreMechanics struct, driven by
`DCPowerUpPaceLowerLimit=5` / `DCPowerUpPaceUpperLimit=8`. So in DC mode the JSON value is replaced at
runtime — which is why editing only the JSON does not fully fix the rate.

The separate **PlayerData.PowerUpPace** field (deserialized in `FUN_00936910`) is the per-player stored
pace, distinct from this bag's source value.

## Patch sites (force a fixed pace)
Two constructor sites read `CoreMech+0x5c` for the **powerup** bag. Forcing `w2` (the `pace` arg) to a
constant bypasses both the JSON read and the DC override (the struct field is no longer read):

| Ghidra addr | function | original | orig bytes | patched |
|---|---|---|---|---|
| `0x00f44cb8` | `FUN_00f44950` (main board) | `ldr w2,[x22,#0x5c]` | `c25e40b9` | `mov w2,#N` |
| `0x00f4f9b0` | `FUN_00f4f698` (alternate model) | `ldr w2,[x0,#0x5c]` | `025c40b9` | `mov w2,#N` |

`mov w2,#N` (MOVZ) assembles to 4 bytes for N in 0..65535. `GoldenMinoPace` (`+0x60`, sites `0x00f44cc8`
/ `0x00f4fa00`) is left untouched.

File offset = Ghidra addr − 0x100000 (image_base 0x100000).

## On-board powerup cap (the "~7 cap, then rate returns to normal")
Separate from pace. The powerup **type** bag `FUN_00f4e9dc` (size `PowerUpBagSize=3`) picks which
powerup to spawn, gated by a per-type on-board count limit:
```c
type = draw_from_type_bag();
if (type != -1) {
  cur = FUN_00f4ee54(gen, type);   // count of this type already on matrix + in queue
  max = FUN_00f4bdd8(def);         // per-type max = *(int*)(def + 0x34)
  if (cur < max) return type;      // allow
}
return -1;                         // capped → this piece spawns NO powerup
```
When all 3 bag types hit their max (sum ≈ 7 on board), every draw returns -1 → spawns stop until
powerups clear → observed "hard cap ~7, then droprate returns to normal". **CONFIRMED live:** with
`powerup_cap_removed` + pace=1 the matrix saturates at a true 100% drop rate with no ~7 wall — so the
perceived ~50% ceiling was purely the cap's steady-state (spawn ≈ clear rate), NOT a separate gate.

Cap-removal patch site (make the `cur < max` check always pass):
| Ghidra addr | function | original | orig bytes | patched |
|---|---|---|---|---|
| `0x00f4edbc` | `FUN_00f4e9dc` | `b.lt f4edc4` | `4b000054` | `b f4edc4` (`02000014`, unconditional) |

Implemented as native patch **powerup_cap_removed** (inline, fixed write). Pair with `powerup_pace_fixed`
pace=1 to saturate the matrix.

## Implemented as
Native patch `powerup_pace_fixed` in `native_patches.json` (type `inline`, two `asm` writes
`mov w2, #{pace}`), applied by `tbnative.assemble_write` (keystone) with a per-patch `values` dict. The
Native tab takes a **% per piece** input and snaps to `pace = max(1, round(100/pct))`, showing the true
"1 powerup every N pieces (~X%/piece)".
