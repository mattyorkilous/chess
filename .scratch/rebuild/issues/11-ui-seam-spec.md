# UI seam spec

Type: grilling
Status: open
Blocked by: 07
Parent: ../map.md

## Question

`run_game` is a loop and stays one — that's the agreed exception. Everything else in
the UI goes pure. Needs the `Position` shape from 07.

The current `ui.py` is 623 lines: `run_game`, `select_players`, `handle_click`,
`animate_move`, `draw_game`, `draw_board`, `highlight_square`, `draw_pieces`,
`show_possible_squares`, `draw_message`, `draw_text`, plus a `ui_defaults()` config
dict and PNGs under `Pieces/`.

- **The state/render split**: a frozen `GameState` (position, selection, animation
  progress, player config, message) plus a pure `update(state, event) -> GameState`
  and a `render(surface, state)` whose only impurity is blitting. The loop then does
  nothing but poll events, fold them through `update`, and call `render`.
- **Animation** is the hard part — `animate_move` currently blocks with its own
  inner loop. Making it a function of elapsed time held in the state is what lets
  the outer loop stay the only loop. Confirm that's the approach.
- **Asset loading** is I/O: where it happens, and whether surfaces get cached (the
  current `load_image` reloads per call).
- **What carries over verbatim** versus gets rewritten. The drawing functions are
  mostly already close to pure; `handle_click` and `run_game` are not.
- Whether `ui_defaults()` stays a dict or becomes a frozen config dataclass.
