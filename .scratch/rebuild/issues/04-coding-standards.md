# Write CODING_STANDARDS.md

Type: grilling
Status: open
Blocked by: —
Parent: ../map.md

## Question

Adapt `../soccer/CODING_STANDARDS.md` to this repo. Settled while charting:

- Keep **Style / Naming / Types / Docstrings / Tests** near-verbatim, including
  "name the return value, then return it" and comprehensions-over-loops as hard
  rules.
- **Drop** the entire Polars section and the dataframe naming rules.
- **Add — Dataclasses**: frozen; no methods except dunders and validation; plain
  functions do the work. The rule needs a stated reason and one example of the
  wrong shape, or it won't survive contact.
- **Add — Mutation seam**: `src/chess/search/` is the sole module permitted mutable
  state and imperative loops, named by path. TT passed explicitly, never a global.
  Say what qualifies something to live there, so the seam doesn't creep.
- **Add — Bitboards**: naming under the adjective-suffix rule (`pawns_white`, not
  `white_pawns`), how packed-int moves are named and where `encode_move` /
  `decode_move` sit, and the square-indexing convention (A1=0 vs A8=0 — pick one
  and write it down; the old code used row/col with row 0 = rank 8).

Open for discussion: whether the no-loops rule is enforceable by ruff or is
prose-only, and how strictly "few public functions, each deep" applies to movegen.
