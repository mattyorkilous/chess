# ruff.toml and ty.toml

Type: grilling
Status: open
Blocked by: 04
Parent: ../map.md

## Question

Turn the standards doc into enforced config. Strict was asked for explicitly.

- **ruff**: which rule sets beyond `E`/`F` — the realistic candidate is `ALL` with a
  short, justified ignore list rather than an opt-in list that quietly stays small.
  Decide per-directory overrides: does `search/` get a carve-out for the loop rules,
  and do tests get relaxed docstring rules?
- Which standards are *mechanically* enforceable (mutable default args, `Any`,
  return-expression-directly, comprehension preference via `C4`/`PERF`) versus
  prose-only in `CODING_STANDARDS.md`. Anything enforceable should not be prose.
- **ty**: Astral's checker is young. Pick the strictness level, decide what happens
  when it disagrees with the standards doc's "rewrite rather than `# type: ignore`",
  and confirm it handles the packed-int/`Move` boundary without complaint.
- Where these run: pre-commit, a `uv run` task, CI, or all three.
