# Perft test harness spec

Type: grilling
Status: open
Blocked by: 02
Parent: ../map.md

## Question

The main automated test. Uses Stockfish's `go perft` as oracle over raw UCI
subprocess (settled; no `python-chess`), with 02's sample output as the parser spec.

- **Corpus**: the standard six positions (start, Kiwipete, position 3/4/5/6) and to
  what depth — depth is a direct runtime cost, so pick per-position depths that keep
  the default suite usable in CI.
- **Fuzzer**: the standard six miss weird ep-pin and castling-through-check edges.
  Spec a random-position generator — random legal play from the start for N plies,
  then perft-compare at shallow depth. Decide the seed policy: fixed seed for
  reproducibility, or random with the failing seed printed.
- **Divide-and-descend on mismatch**: when counts disagree, the harness should walk
  `perft divide` down to the single move that diverges and report the FEN plus the
  move, not just "12345 != 12344". This is the difference between a useful failure
  and a night of manual bisection.
- **Skip behaviour** when Stockfish is absent, so the suite stays green on a fresh
  clone without silently testing nothing.
- **Speed regression**: does the harness also record nps so the target from 03 is
  protected by a test, or is that a separate benchmark script?
- Where perft tests live and how they're marked slow/fast for `pytest`.
