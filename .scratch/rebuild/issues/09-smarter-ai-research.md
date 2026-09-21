# What actually makes the AI smarter, within a Python node budget

Type: research
Status: open
Blocked by: 03
Parent: ../map.md

## Question

"Smarter" needs to become a list of specific techniques ranked by Elo-per-node,
constrained by a Python node budget that makes each one expensive.

The current AI: fixed depth 4, no quiescence (so it hangs pieces at the horizon),
a transposition table keyed on `str(numpy_array)` with no Zobrist and no bound
flags, move ordering by a simple score, a `maximizing_player` flag tangled with
negamax negation, and an eval of piece values + piece-square tables plus three
stub functions (`evaluate_pawn_structure`, `evaluate_king_safety`,
`evaluate_center_control`) that all return 0.

Research, from primary sources, the approximate Elo gain and node cost of:

- Quiescence search — almost certainly the single largest win, since without it
  depth 4 is effectively blind. Confirm and quantify.
- Proper Zobrist hashing, TT with exact/lower/upper bound flags and replacement
  policy.
- Move ordering: MVV-LVA, killer moves, history heuristic, TT-move-first, and
  whether SEE earns its cost in Python.
- Null-move pruning, late move reductions, futility pruning, aspiration windows.
- Eval terms worth having versus the three stubs: pawn structure, king safety,
  mobility, tapered midgame/endgame eval.

The Python angle is the point: several of these are cheap in C and expensive here.
Rank by (Elo gained) / (Python cost), and say which ones are traps.

Findings land in a Markdown file in the repo, linked from the answer.
