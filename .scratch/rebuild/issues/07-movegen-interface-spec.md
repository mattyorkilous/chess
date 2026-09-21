# Position and movegen interface spec

Type: grilling
Status: open
Blocked by: 03, 06
Parent: ../map.md

## Question

The core spec a build session executes. Needs the spike's verdict (03) and the
magics shape (06) before it can be pinned.

- **`Position` fields exactly**: which bitboards (6 piece types × 2 colours, or
  piece-type boards plus 2 colour-occupancy boards, plus a combined occupancy?),
  and where side-to-move, castling rights, ep square, halfmove and fullmove clocks
  live. Redundant boards cost memory and copy time but save recomputation — the
  spike's copy-make number decides this.
- **Laziness mechanism**: legal moves, checkers, pins and check status must be
  computed on demand, never eagerly. But the position is frozen, so no caching on
  the instance. Options: plain functions recomputed at each call site, an
  `@lru_cache`'d module function keyed on the position (needs `Position` hashable),
  or a separate non-frozen analysis object built explicitly where it's wanted.
  This is the thing the old engine got most wrong — it computed everything up front
  in `add_position_info` on every single node.
- **Move packing layout**: which bits for from, to, promotion, and flags
  (capture / ep / castle / double-push). Where the frozen `Move` boundary sits and
  who is allowed to cross it.
- **Generation API surface**: one `generate_moves(position)`, or split
  captures/quiets for staged generation in search? Staged generation matters for
  move ordering later (ticket 10) — decide now or pay to retrofit.
- **FEN parse/format** contract and error behaviour on malformed input.
