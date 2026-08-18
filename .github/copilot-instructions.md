# Copilot instructions. Telepane

Condensed re-delivery. Canonical rules: [`AGENTS.md`](../AGENTS.md).

- Never build shell command strings. Every tmux call goes through
  `tmux._run([...argv])`; no `shell=True`, no interpolation.
- Target tmux objects by id (`$`/`@`/`%`), never by name.
- All environment access lives in `config.py`.
- Never launch the TUI in the working pane; use `App.run_test()` or a separate pane.
- Single-line Conventional Commits (`feat:`/`fix:`/`chore:`/`docs:`), no scope,
  no body, no trailers, no `Co-Authored-By`.
- Search and reuse before adding; smallest change at the root cause.
- Verification loop before "done": `ruff check` → `ruff format --check` →
  `pytest` → run in a real tmux pane.
