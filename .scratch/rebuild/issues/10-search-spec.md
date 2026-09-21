# Search module spec

Type: grilling
Status: open
Blocked by: 03, 09
Parent: ../map.md

## Question

Spec `src/chess/search/` — the sole mutation seam. Needs the measured node budget
(03) and the ranked technique list (09).

- **Which techniques from 09 make the first cut**, and which are explicitly deferred.
  Ponytail applies: the cheapest set that hits the 03 target, not everything that
  exists.
- **Negamax, cleanly** — the current code mixes a `maximizing_player` flag with
  sign flipping and is confusing at best. Settle on plain negamax and say so.
- **TT design**: Zobrist key generation and where the random keys live, entry
  layout, bound flags, replacement policy, size, and — per the seam rule — how it's
  threaded explicitly through the search rather than sitting in a module global.
- **Time management**: iterative deepening with a wall-clock budget and a safe abort
  that doesn't return a half-searched move, versus fixed depth. The 03 target is
  expressed in seconds, so this is how it gets honoured.
- **The seam contract**: exactly what `search/` exposes to the rest of the codebase.
  Ideally one pure-looking function — `find_best_move(position, budget) -> Move` —
  with all mutation sealed behind it.
- Threading/parallelism: explicitly deferred to the fog item on free-threaded 3.14,
  or considered now?
