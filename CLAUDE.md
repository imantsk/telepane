# CLAUDE.md

> **Workflow rules live in [`AGENTS.md`](AGENTS.md)**: execution sequence,
> commit convention, testing/verification loop, and guardrails. This file
> carries project and architecture facts only. If a workflow rule feels wrong,
> fix it in AGENTS.md, not here.

## What this is

`telepane` is a mouse-driven Textual TUI for controlling tmux from a single pane.
The point of the tool is the send box: choose any pane in the tree, type a
message, and it is delivered there with `tmux send-keys`. So you can drive an
agent (or any REPL) running in another pane without switching to it.

## Commands

```bash
uv venv && uv pip install -e ".[dev]"   # set up
ruff check src tests                      # lint
ruff format --check src tests             # format check
pytest                                    # unit + app (pilot) tests
TELEPANE_LIVE_TESTS=1 pytest tests/test_live.py   # real-tmux roundtrip
telepane                                      # run (in its own pane. See Rule 3)
./scripts/dev.sh                           # dev supervisor (in its own pane)
```

### Dev mode

`scripts/dev.sh` runs `scripts/_dev_watch.py`, a silent watcher: any edit under
`src/telepane/` hot-restarts the app, a crash auto-heals, and the screen is reset
before each launch so no stale frame or watcher log leaks onto the TUI. Launch it
in a dedicated tmux pane, edit source elsewhere, and it reloads live. The
development loop is driven end-to-end against the running app. `q` quits cleanly;
Ctrl-C stops the supervisor.

The app is also self-healing at runtime: the poll timer swallows transient tmux
errors and rebuilds the tree when the server disappears and returns, so a killed
pane or a bounced server never crashes the UI.

## Architecture

- **`tmux.py`**: the only module that talks to tmux. `_run([...])` shells out
  via `subprocess` with an argv list (never `shell=True`). Reads use tab-delimited
  `-F` format strings; writes/controls are thin argv wrappers (incl.
  `set_option`/`show_option`/`source_file`). Objects are addressed by tmux id
  (`$`/`@`/`%`). Core call: `send_text(pane, text, enter)`.
- **`config.py`**: the only module that reads the environment (`home_dir`, XDG).
  `Config` dataclass ↔ `~/.config/telepane/config.json`.
- **`clipboard.py`**: argv-only clipboard (macOS `pbcopy`/`osascript` file copy,
  Linux `wl-copy`/`xclip`/`xsel`). **`screenshot.py`**: svg/png/md capture,
  save and/or clipboard. **`tmux_schema.py`**: categorised option specs,
  named profiles, colour-swatch palette.
- **`app.py`**: `TelepaneApp(App)`. Left: window/pane `Tree`. Right: server stats,
  selected-target info, `capture-pane` preview, and the `SendBox`. A refresh
  timer re-polls; tree selection sets `self.selected` (a `NodeRef`); `SendBox.Send`
  messages become `tmux.send_text` calls.
- **`widgets/`**: `tree.py` (windows-as-roots + `NodeRef`), `send_box.py` (input
  box + `MessageArea`, dual-label enter toggle), `info.py` (Rich renderers +
  `compact_path`), `resizer.py` (draggable dividers, axis x/y, emit `Committed`),
  `modals.py` (new/rename prompt, kill confirm, help), `settings_screen.py`
  (full-screen settings: subsection sidebar + field list). UI only.
- **`cli.py`**: `telepane` entry point; preflight checks tmux is installed and a
  server is running before launching the app.

## Key behaviours

- A tree node resolves to a `send_target` pane id: a pane → itself; a window →
  its active pane; a session → the active pane of its active window.
- `send_text` sends `send-keys -l -- <text>` then `Enter` (send always submits in
  the target). The `enter_sends` toggle instead governs the *input box*: on ⇒
  Enter sends / Shift+Enter newline; off ⇒ Enter newline / Shift+Enter sends.
- Preview is `capture-pane -p` of the current target, tail-trimmed to
  `Config.preview_lines`.
