# Install Stockfish and verify `go perft` over UCI

Type: task
Status: open
Blocked by: —
Parent: ../map.md

## Question

Nothing to decide. Stockfish is not on this machine (`which stockfish` → not found),
and it is the oracle the whole test strategy rests on.

- Install it (`brew install stockfish`).
- Verify raw UCI over `subprocess` works end to end: `uci` → `isready` →
  `position fen <fen>` → `go perft 5`, parse the node count off stdout. No
  `python-chess`.
- Note the quirks a harness will have to handle: exact stdout format of
  `go perft`, whether it's `Nodes searched:` or per-move divide lines, buffering
  and newline behaviour, and how a wrong FEN fails.

Record in the answer: version, binary path, and a verbatim sample of `go perft`
output so ticket 08 can spec the parser without re-deriving it.
