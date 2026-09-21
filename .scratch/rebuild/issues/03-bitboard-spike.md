# Bitboard spike: measure nps, settle copy-make, fix the speed target

Type: prototype
Status: open
Blocked by: 01
Parent: ../map.md

## Question

Three things no argument can settle — only a measurement.

1. **What nps does a frozen-dataclass bitboard `Position` actually reach in
   CPython 3.14 on arm64?** Pure-Python bitboard engines land roughly 50k–200k.
   Where we land decides everything downstream.
2. **Copy-make or make/unmake?** A bitboard position is ~12 ints, so constructing
   a new frozen dataclass is cheap — possibly cheap enough that copy-make (fully
   pure, no undo stack, no mutation in movegen) is within noise of make/unmake.
   If it is, purity wins for free. If it's 2×+, the mutation seam has to widen and
   that's a real cost to the standards doc.
3. **Is depth 6 in ≤2s reachable?** Q6 was agreed *conditionally*. Effective
   branching factor ~5–6 with good ordering gives ~20–50k main-search nodes, times
   3–5× for quiescence. At 150k nps that's comfortable; at 50k nps it's 5s+.

Build the smallest throwaway that answers these: a frozen `Position`, knight/king
pawn attack tables, one slider approach (classical rays are fine here — magics are
ticket 06), legal movegen, and `perft`. Correctness only needs to hold for the
start position and Kiwipete.

Deliberately **not** in the spike: magics, eval, search, TT, UI.

Resolution must state: measured nps, the copy-make vs make/unmake delta as a
percentage, and the depth/time target we commit to — a number, not "fast".
