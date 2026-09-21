# Switch to arm64 Python and lay the uv skeleton

Type: task
Status: open
Blocked by: —
Parent: ../map.md

## Question

Nothing to decide — work that unblocks measurement.

`.python-version` says `3.14`, but the only 3.14 uv can see locally is
`/usr/local/bin/python3.14`, an **x86_64** homebrew build running under Rosetta on
Apple Silicon. Every benchmark taken on it is wrong, so this lands before the spike.

- `uv python install 3.14` (arm64), pin it, confirm `platform.machine() == 'arm64'`.
- Declare deps: `pygame`, `pytest`. No numpy.
- Confirm the `src/chess/` layout from `uv init --package` and the `chess` script
  entry point resolve.
- `.gitignore` sanity, and get an initial commit down — the repo has no commits yet.

Record in the answer: the interpreter path, `platform.machine()`, and a
before/after timing of one identical workload so the Rosetta cost is on the record.
