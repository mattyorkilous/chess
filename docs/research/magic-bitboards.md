# Magic bitboards in pure CPython

Research for [`.scratch/rebuild/issues/06-magic-bitboards-research.md`](../../.scratch/rebuild/issues/06-magic-bitboards-research.md).

Magics were already chosen as the slider approach, with tables built by a checked-in
`tools/gen_magics.py`. This settles the *how*.

**Measurement environment.** CPython 3.14.7, arm64 macOS (Darwin 25.6.0), no C extensions.
Every number below marked *measured* was produced by scripts written for this note and run
on that machine; timings are best-of-5 or best-of-7 over 300,000 random `(square, occupancy)`
pairs, memory is a recursive `sys.getsizeof` walk that counts each distinct object once.

---

## TL;DR

| # | Question | Answer |
|---|---|---|
| 1 | Variant | **Fancy magics.** Plain wastes 2.7x the table for nothing in CPython. Black magic buys ~150 KiB and costs a second search problem. PEXT is unreachable from CPython — discard it. |
| 2 | Generation | Trial-and-error, sparse random multipliers, popcount pre-filter, epoch trick. **Measured 21 s** for the full 128-square set in pure Python. |
| 3 | Generate or lift | **Generate.** 21 s once, sidesteps licensing entirely. The good published sets are GPL-3.0 (viral) or zlib (notice retention). |
| 4 | Shape | **`tuple[tuple[int, ...], ...]`, one inner tuple per square.** 231 ns/lookup, ~1.0 MiB live. Flat+offset is 15% slower; per-square dicts are faster but 2.5x the memory and make the magics pointless. |
| 5 | `& 0xFFFF_FFFF_FFFF_FFFF` | Needed **exactly once**, right after the multiply. Not after `&`, `\|`, `^`, `>>`. Costs ~41 ns (20% of a lookup). Omitting it raises `IndexError`, not a subtle bug. |
| 6 | Storage | **Generated `.py` module of nested tuples.** 575 KiB `.pyc`, **1.56 ms** warm import, int objects deduplicated by the compiler. Beats JSON (12 ms), pickle (6.3 ms) and marshal. |

The single largest speed factor is none of the above: **binding the tables to function locals
instead of reading them as module globals is worth 1.6x** (231 ns vs 365 ns, measured). Do that
in the movegen hot loop before optimising anything else here.

---

## 1. Plain vs fancy vs black magic vs PEXT

The index function all four share, per the [Chess Programming Wiki][cpw-magic]: mask the
occupancy to the relevant squares, multiply by a magic constant, right-shift to the top
`n` bits, index a table.

### PEXT — discard it, explicitly

`PEXT` is `_pext_u64`, a single x86-64 BMI2 instruction that gathers the mask-selected bits of
a register into a contiguous low field. It is *hardware*. CPython exposes no intrinsic for it,
`int` has no PEXT-equivalent method, and emulating it in Python is a bit-loop that is orders of
magnitude slower than one multiply. **PEXT is not available to this project and never will be
without a C extension.** It is out of scope by construction, not by preference.

Worth noting as corroboration: PEXT is also on the way out in C. Stockfish master
([`src/attacks.cpp`, `src/attacks.h`][sf-attacks]) contains **no `USE_PEXT` or BMI2 path at
all** any more — it compiles either fancy magics or one of two hyperbola-quintessence variants.
Chasing PEXT would have been chasing a retreating target even in a language that could reach it.

### Plain magics

Lasse Hansen's original: a fixed-width table per piece type, so the shift is a compile-time
constant (`64-12` rook, `64-9` bishop). CPW gives "32 KiB per rook square, 4 KiB for each bishop
square" — 64x4096 + 64x512 = **294,912 entries**.

The one C advantage is that a constant shift needs one fewer register. In CPython there are no
registers; the shift is `SHIFT[sq]`, one more `BINARY_SUBSCR` on an already-hot tuple. Measured
cost of one extra module-level subscript: **~45 ns** as a bare listcomp element, but folded into
a full lookup the difference between fancy and a constant shift is a few ns out of 231. You
would pay 2.7x the table (294,912 vs 107,648 slots, ~1.5 MiB extra of pointer array) to save it.

**Reject plain magics.**

### Fancy magics — the recommendation

Pradu Kannan's refinement ([his paper][kannan-pdf], summarised on [CPW][cpw-magic]): per-square
table sized to that square's relevant-bit count, with a per-square shift. CPW: "~840 KiB all rook
and bishop attacks".

Stockfish confirms the sizes directly — `std::array<Bitboard, 0x19000> RookTable` and
`std::array<Bitboard, 0x1480> BishopTable`, i.e. 102,400 + 5,248 = **107,648 entries**
([`src/attacks.cpp`][sf-attacks]). My generator reproduces exactly those counts (measured).

This is the mainstream choice, it is what the reference implementation ships, and in CPython its
one drawback (variable shift) is nearly free.

### Black magic

Volker Annuss, CCC August 2017, also credited to Niklas Fiekas ([CPW][cpw-magic]). Instead of
`occ & mask` it uses `occ | ~mask`, which adds a large constant to every key; because black
magics are never zero the minimum producible index can be maximised and the ranges packed more
tightly. CPW: "692 KiB for published black magics", **88,316 entries**, with a *fixed* 12-bit
shift for every square.

Against fancy: saves 19,332 slots. In CPython a slot is an 8-byte `PyObject*` in a tuple, so
that is **~150 KiB** — not the 150 KiB of precious L1 it represents in C, just 150 KiB of heap.
It also gives back the constant shift, worth a few ns.

Against that: you either lift someone's published constants (see §3) or solve a harder search
problem — packing tables to a global minimum is NP-complete
([TalkChess][tc-np]) and the published sets are the product of a long offline search, not
21 seconds of `random.getrandbits`.

**Reject black magic.** ~150 KiB and a few ns do not justify inheriting a licence question or
a second search problem.

---

## 2. The generation algorithm

Tord Romstad's ["Looking for Magics"][cpw-looking] is the canonical statement, and Stockfish's
`init_magics` is the same algorithm hardened. For one square:

1. Build the **relevant-occupancy mask**: the slider's rays from that square with the *edge*
   squares removed. Edges are excluded because a blocker on the last square of a ray has nothing
   behind it to block, so it cannot change the attack set
   ([analog-hors][analog]). Stockfish's version:
   `edges = ((Rank1BB | Rank8BB) & ~rank_bb(s)) | ((FileABB | FileHBB) & ~file_bb(s))`.
2. Enumerate **every subset** of that mask with the Carry-Rippler, and compute the true attack
   set for each by ray-walking. `n` relevant bits gives `2**n` subsets (max 4096 rook, 512 bishop).
3. Draw a candidate multiplier as the **AND of three random 64-bit values**. Romstad:
   "Just trying out random numbers with a low number of nonzero bits until you find a number
   which works is by far the fastest and easiest way." Three-way AND gives ~8 set bits on average;
   sparse multipliers spread the masked bits into the high word without the additive carries that
   a dense multiplier produces.
4. **Pre-filter cheaply.** Stockfish rejects a candidate before touching the table if
   `popcount((magic * mask) >> 56) < 6` — if the magic cannot scatter at least 6 bits into the
   top byte it cannot possibly produce a good index. This costs one multiply instead of up to
   4096 table writes.
5. Try to fill the table. Every subset maps to `((occ * magic) >> (64-n)) & …`; a slot already
   holding a *different* attack set is a **destructive collision** and the candidate dies. A slot
   holding the *same* attack set is a **constructive collision** and is fine — two different
   blocker layouts can legitimately produce the same attacks
   ([analog-hors][analog]).
6. Repeat until one survives.

**The epoch trick.** Naively you must zero the 4096-entry table before each attempt. Stockfish
keeps a parallel `epoch[]` array and an incrementing counter, treating any slot whose epoch is
stale as empty. No clearing, ever.

### Measured: how long it actually takes

Both variants implemented in pure CPython 3.14.7, full set of 64 rook + 64 bishop squares:

| Generator | Wall time | Candidates past the popcount filter |
|---|---|---|
| Naive (clear the table each attempt) | **29.3 s** | 12,997,405 draws |
| Stockfish-style (popcount filter + epoch trick) | **21.0 s** | 1,303,618 accepted |

Both produce 102,400 rook + 5,248 bishop entries and pass a full round-trip verification
(every `(square, occupancy)` pair re-derives the ray-walked attack set — 0 failures).

For reference, Romstad reported "less than a second" for the same job in C on a 2.8 GHz Core
Duo. A ~25x pure-Python penalty for a build script run once is not a problem.

**Make the seed a constant.** Stockfish seeds its PRNG from a fixed per-rank table
(`int seeds[][RANK_NB] = {{8977, 44560, …}, {728, 10316, …}}`) so init is deterministic and
fast. `tools/gen_magics.py` should take `--seed` with a fixed default so regenerating produces
a byte-identical module and the diff is empty.

---

## 3. Generate, or lift a published set?

**Generate.** 21 seconds, once, in a script that is already being written. Lifting saves nothing
and imports a question.

The licence position on the well-known sets, if it ever matters:

| Source | Licence | Practical effect |
|---|---|---|
| Kannan, `magicmoves.h` / `magicmoves.c` | **zlib** (verbatim: "Copyright (C) 2007 Pradyumna Kannan… permission is granted to anyone to use this code for any purpose, including commercial applications… 1. The origin of this code must not be misrepresented… 3. This notice may not be removed or altered from any source distribution.") | Permissive, but the notice must travel with the constants. |
| [Stockfish][sf-attacks] | **GPL-3.0-or-later** | Viral. Also moot — it *searches* its magics at init, it does not ship them. |
| [python-chess][pychess] | **GPL-3.0-or-later** | Viral. Also moot — no magics at all (see §4). |
| [cozy-chess][cozy] (analog-hors) | **MIT** | Fine with attribution. |
| [magic-bits][magicbits] | **MIT** | Fine with attribution. |
| Chess Programming Wiki | **CC BY-SA** | Share-alike applies to the wiki text; code snippets on it carry their authors' own terms. |
| Annuss black magics | Posted to a [TalkChess thread][tc-black] with **no licence statement at all** | The worst case: no grant, no disclaimer, nothing to comply with. |

There is a reasonable argument that a magic multiplier is a discovered fact rather than an
original work and so is not copyrightable at all — but that argument costs more to have than the
21 seconds it would save. Generate them.

---

## 4. Table size and shape, in CPython terms

### Why the C reasoning does not transfer

In C a magic table is a `Bitboard[107648]` — 841 KiB of contiguous `uint64_t`, and the whole
design conversation is about fitting hot parts of it in L1/L2. **None of that reasoning survives
in CPython.** A Python list or tuple of ints is an array of `PyObject*`; each int is a separate
heap object (`sys.getsizeof(2**63) == 36` bytes, measured). A lookup is a pointer dereference to
somewhere else on the heap. There is no contiguity to exploit and no cache-line argument to make.

What actually matters instead:

- **Bytecode operations per lookup.** Every `X[i]` is a `BINARY_SUBSCR`; every name is a
  `LOAD_FAST`/`LOAD_GLOBAL`. This dominates.
- **Object count, not slot count.** Among 102,400 rook slots there are only **4,900 distinct
  attack-set values** (measured; 1,428 for bishops, matching CPW's "1428/4900 distinct attack
  sets"). If those 4,900 ints are shared, the int objects cost ~160 KiB; if each slot owns its
  own int, they cost ~3.3 MiB. **Whether the loader deduplicates is worth 4x the memory** — and
  it is entirely determined by §6.
- **Local vs global.** Measured 1.6x.

### Measured: lookup cost by shape

Rook lookups, 300,000 random `(square, occupancy)` pairs, all tables bound as function locals,
best of 7:

| Shape | ns / lookup |
|---|---|
| `tuple[tuple[int, ...], ...]` — per-square inner tuple | **230.6** |
| `list[list[int]]` — per-square inner list | 230.9 |
| flat `list` + per-square offset | 266.0 |
| flat `tuple` + per-square offset | 275.3 |
| `array('Q')` + per-square offset | 318.3 |
| per-square `dict[occ] -> attacks`, no magic at all | **172.6** |
| python-chess shape: `rank_dict[sq][m&occ] \| file_dict[sq][m&occ]` | 289.1 |

Nested and flat are the *same* arithmetic; flat just adds `OFFSET[sq] +` — one more subscript and
one more add, ~35 ns, **15%**. Nested tuple and nested list are indistinguishable. `array('Q')`
loses because every read allocates a fresh `int` object.

### Measured: memory by shape (rook tables, 102,400 slots)

| Shape | Live bytes | Notes |
|---|---|---|
| nested tuples, ints shared | **~1,050 KiB** (full 107,648-entry set) | 6,326 distinct int objects |
| `list[list[int]]`, ints *not* shared | 3,992 KiB | 40 B/slot: 8 B pointer + 32 B int |
| flat list, ints not shared | 4,088 KiB | |
| per-square dicts | **10,031 KiB** | 102,400 unique keys, no sharing possible |
| rank+file dicts (python-chess shape) | **472 KiB** | only 5,120 keys total |

### The honest aside: magics are not the fastest option in CPython

[python-chess][pychess] — written by Niklas Fiekas, the same person credited with the black
magics — **does not use magic bitboards.** It builds three `List[Dict[Bitboard, Bitboard]]`
tables at import with a Carry-Rippler and indexes them directly by masked occupancy:

```python
attacks = BB_DIAG_ATTACKS[square][BB_DIAG_MASKS[square] & self.occupied]
```

That is measurable, and it agrees with the table above: a plain dict keyed by masked occupancy
is **172.6 ns vs 230.9 ns** for the magic lookup, because it skips the multiply, the 64-bit
mask and the shift, and `hash(int)` is nearly free. The magic index arithmetic alone costs
211.5 ns of the 230.9 ns; the table read is the cheap part.

The catch is memory: one dict per square over the full rook occupancy is **10 MiB**. python-chess
avoids that by splitting rook attacks into separate **rank** and **file** tables (6 relevant bits
each instead of 12), so the whole slider set is **10,368 entries** built at import in **14 ms**,
using 472 KiB — at the cost of two lookups and an OR per rook (289.1 ns).

So the real CPython landscape is:

| Approach | ns/lookup | Memory | Checked-in data |
|---|---|---|---|
| per-square dicts, full occupancy | 173 | 10 MiB | large |
| **fancy magics, nested tuples** | **231** | **1.0 MiB** | 575 KiB `.pyc` |
| python-chess rank+file dicts | 289 | 0.5 MiB | **none** |

Magics are the middle of that three-way trade, not the winner on either axis. The decision to
use them is already made and is defensible — but it should be made knowing that it is not a
speed win over the obvious dict, and that the only well-known pure-Python engine chose
differently. If perft numbers later disappoint, the dict shape is the thing to try, not a
fancier magic.

### Recommendation

```python
# tables.py (generated)
MASK    = (…, …)                 # 128 ints, rook 0..63 then bishop 0..63
MAGIC   = (…, …)
SHIFT   = (…, …)
ATTACKS = ((…), (…), …)          # 128 inner tuples
```

Nested tuples, one inner tuple per square, parallel `MASK`/`MAGIC`/`SHIFT` tuples. Fastest
measured, smallest measured, and (see §6) the shape that makes the `.pyc` small. Bind all four
to locals in the movegen hot loop.

---

## 5. `& 0xFFFF_FFFF_FFFF_FFFF` — exactly where

Python's `int` is arbitrary-precision, so nothing wraps. `occ * magic` is a genuine ~120-bit
product, and `>> 52` of a 120-bit value leaves a ~68-bit index. **This is not a subtle
off-by-something.** Measured, running the loop without the mask:

```
IndexError: list index out of range
```

Which operators escape `[0, 2**64)` when both operands are in range (measured):

| Expression | Stays in range? | Note |
|---|---|---|
| `a & b` | yes | |
| `a \| b` | yes | |
| `a ^ b` | yes | |
| `a >> k` | yes | |
| `a & ~b` | yes | `~b` is negative, but ANDing with an in-range `a` clamps it |
| `a + b` | **no** | 65th bit |
| `a - b` | **no** | negative when `a < b` |
| `a << k` | **no** | grows without bound |
| `a * b` | **no** | ~120 bits |
| `~a` | **no** | always negative |

So across a bitboard engine the discipline is: **mask after `<<`, `*`, `+`, and any subtraction
that can go negative; never after `&`, `|`, `^`, `>>`.** Use `~a` only immediately inside an
`&` with an in-range value, otherwise write `a ^ FULL`.

In the magic index specifically the mask is needed **exactly once**, after the multiply:

```python
idx = ((occ & MASK[sq]) * MAGIC[sq] & 0xFFFF_FFFF_FFFF_FFFF) >> SHIFT[sq]
```

`occ & MASK[sq]` cannot escape, and the `>>` afterwards cannot either.

### Measured cost, and the one alternative

Isolating the index arithmetic (listcomp over 300,000 pairs):

| | ns |
|---|---|
| index arithmetic **with** `& M64` | 211.5 |
| index arithmetic **without** (wrong) | 170.8 |
| full lookup including the table read | 206.6 |

The mask costs **~41 ns — about 20% of a lookup.** It buys a fresh `int` object from a 120-bit
bignum, which is why it is not free.

The one legitimate alternative is to mask *after* the shift instead of before, taking the low
`n` bits rather than truncating the product to 64:

```python
idx = ((occ & MASK[sq]) * MAGIC[sq]) >> SHIFT[sq] & SIZEMASK[sq]   # SIZEMASK = (1 << n) - 1
```

These are arithmetically identical — both select product bits `[64-n, 63]`. Measured **252.1 ns
vs 248.7 ns**, i.e. no difference, and it costs a fourth parallel table. **Keep the `& M64`
after the multiply**; it reads closer to the C and to every reference implementation.

---

## 6. Storage format

Measured on the full 107,648-entry set (both pieces), fresh interpreter per run, best of 5–7.

| Format | File size | `.pyc` | Load / import | Live memory | Distinct int objects |
|---|---|---|---|---|---|
| **`.py`, nested tuples** | 1,635 KiB | **575 KiB** | **1.56 ms** | **1,050 KiB** | **6,326** |
| `.py`, flat tuple | 1,636 KiB | 583 KiB | 1.55 ms | 1,043 KiB | 6,326 |
| `.py`, nested lists | 1,635 KiB | 2,345 KiB | 2.44 ms | 1,082 KiB | 6,326 |
| `.py`, flat list | 1,636 KiB | 2,658 KiB | 2.30 ms | 1,082 KiB | 6,326 |
| `json.load` | 1,636 KiB | — | 12.0 ms | 6,190 KiB peak | 107,648 |
| `pickle.load` (protocol 5) | 835 KiB | — | 6.3 ms | 4,285 KiB | 107,648 |
| `marshal.loads(bytes)` | 1,154 KiB | — | 4.5 ms | 4,194 KiB | 107,648 |
| `array('Q').frombytes` | 841 KiB | — | 1.2 ms | 894 KiB | — (slow lookups) |
| raw `int.from_bytes` loop | 841 KiB | — | 25.4 ms | — | 107,648 |

Three findings drive the recommendation.

**Tuple literals compile to one constant; list literals compile to bytecode.** A module-level
tuple of tuples becomes a single marshalled constant in the `.pyc`, so the `.pyc` is **575 KiB**
and import is one unmarshal. The identical data as nested *lists* compiles to a `BUILD_LIST`
with one `LOAD_CONST` per element — a **2,345 KiB** `.pyc`, 4x larger, and 57% slower to import.
Same source size, same runtime shape, same lookup speed. **Write tuples.**

**Only the `.py` path shares int objects.** The compiler deduplicates equal constants, so an
imported table holds **6,326** distinct int objects for 107,648 slots. `json`, `pickle` and
`marshal` all construct **107,648** separate int objects — 4x the live memory (4.2 MiB vs 1.0 MiB)
and ~15 MiB more RSS (34.5 vs 16.5 MiB measured; 13.2 MiB baseline interpreter). You can recover
it manually (`u = {}; D = [u.setdefault(x, x) for x in D]` measured back down to 1,082 KiB) but
that is code and time to undo a problem the `.py` path never has.

**`marshal.load(file)` is a trap.** `marshal.loads(open(p,'rb').read())` is **4.5 ms**;
`marshal.load(fileobj)` on the same data is **84 ms**, ~19x slower. If marshal is ever used,
read the bytes first. (This is also why the `.pyc` import is fast despite being marshal — the
import machinery reads the whole file.)

### Cold-start caveat

First import with no `.pyc` must compile 1.6 MB of source: **184 ms** (tuples) / **203 ms**
(lists), measured. After that it is 1.5 ms forever. This is a one-off per install/upgrade, it is
already how every Python package behaves, and it is not worth engineering around. Don't commit
`.pyc` files.

### Recommendation

`tools/gen_magics.py` writes a generated `.py` module of **nested tuples**, with a header
recording the seed and a "generated, do not edit" line. Check in both the script and its output.
1.56 ms import, 575 KiB `.pyc`, 1.0 MiB resident, deduplicated ints, no runtime parser, no
schema, no second file format. JSON and binary lose on every axis that matters here.

---

## Sources

- [Chess Programming Wiki — Magic Bitboards][cpw-magic] (plain/fancy/black, table sizes, index formula, distinct-attack-set counts)
- [Chess Programming Wiki — Looking for Magics][cpw-looking] (Romstad's `find_magic`, `random_uint64_fewbits`, "less than a second")
- [Stockfish `src/attacks.cpp` / `src/attacks.h`][sf-attacks] (`init_magics`, `seeds[][]`, popcount pre-filter, epoch trick, `0x19000`/`0x1480`, absence of any PEXT path; GPL-3.0-or-later)
- [python-chess `chess/__init__.py`][pychess] (`_carry_rippler`, `_attack_table`, dict-based sliders; GPL-3.0-or-later)
- [analog-hors — Magical Bitboards and How to Find Them][analog] (edge exclusion, constructive collisions, three-way-AND sparse randoms)
- [Pradyumna Kannan — Magic Move-Bitboard Generation in Computer Chess][kannan-pdf] (fancy magics)
- [`magicmoves.h` licence header, verbatim][magicmoves] (zlib)
- [TalkChess — Black magic bitboards][tc-black] (Annuss/Fiekas, Aug 2017, no licence statement)
- [TalkChess — Hashtable packing is strongly NP-complete][tc-np]
- [cozy-chess][cozy] (MIT), [magic-bits][magicbits] (MIT)

[cpw-magic]: https://www.chessprogramming.org/Magic_Bitboards
[cpw-looking]: https://www.chessprogramming.org/Looking_for_Magics
[sf-attacks]: https://github.com/official-stockfish/Stockfish/blob/master/src/attacks.cpp
[pychess]: https://github.com/niklasf/python-chess/blob/master/chess/__init__.py
[analog]: https://analog-hors.github.io/site/magic-bitboards/
[kannan-pdf]: http://pradu.us/old/Nov27_2008/Buzz/research/magic/Bitboards.pdf
[magicmoves]: https://github.com/sgriffin53/raven/blob/master/magicmoves.h
[tc-black]: https://talkchess.com/viewtopic.php?t=64790
[tc-np]: https://www.talkchess.com/forum3/viewtopic.php?f=7&t=73071
[cozy]: https://github.com/analog-hors/cozy-chess
[magicbits]: https://github.com/goutham/magic-bits
