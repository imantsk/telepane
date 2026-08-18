# AGENTS.md: telepane

Single source of truth for how work is done in this repo, shared across every AI
tool and human contributor. `CLAUDE.md` carries project and architecture facts
and points back here for workflow rules. `.cursor/rules/*.mdc` and
`.github/copilot-instructions.md` re-deliver these rules to their tools. No other
file originates a rule. If a rule feels wrong, fix it here. Do not scatter
contradicting guidance elsewhere.

Precedence: a direct human instruction in the current session, then the most
specific scoped rule, then this file. If instructions still conflict, STOP and
ask.

## Rule 0: never build shell command strings

Every tmux invocation goes through `tmux._run([...argv])`. No `shell=True`, no
`os.system`, no f-string or `%`-interpolation of any value into a command.
Add a new tmux operation by appending argv tokens, never by assembling a string.
Enforced by `tests/test_tmux.py::test_send_text_builds_literal_argv`.

## Rule 1: target tmux objects by id, never by name

Sessions/windows/panes are addressed by their tmux ids (`$0`, `@0`, `%0`), which
`tmux.py` reads from `list-*`. Ids are unique, need no quoting, and survive
renames. Never pass a user-facing name as a `-t` target.

## Rule 2: all environment access lives in `config.py`

No `os.environ` / `os.getenv` / `Path.home()` anywhere else. Reading config or an
env var from another module is the change that breaks the boundary. Put it in
`config.py` and pass the value in.

## Rule 3: never launch the TUI in the pane you are working in

`telepane` takes over the terminal. Exercise the UI with `App.run_test()` (pilot)
for tests, or launch it in a *separate* tmux pane for manual checks.

## Rule 4: comments state constraints, never narrate

A comment or docstring states only a current constraint or behaviour the code
cannot show. No rationale, no history, no "why"/"so that"/"otherwise", no
decision or provenance narration, no docstrings restating a signature. Module
docstrings are one line. If a "why" feels unavoidable, the ruleset is incomplete.
Raise it. Do not write it into the source.

---

## Project

`telepane` is a mouse-driven [Textual](https://textual.textualize.io) TUI that
controls tmux from one pane. Its centre is a text box: pick any session/window/
pane in the tree, type, and the text is delivered there via `tmux send-keys`.
Also shows server stats, a live pane preview, and session/window/pane controls.
Ships to PyPI as the `telepane` command.

```
src/telepane/
  tmux.py        the ONLY tmux boundary. Argv subprocess calls, id targeting
  config.py      the ONLY env boundary. Loads/saves ~/.config/telepane/config.json
  app.py         Textual App: layout, timers, actions, message wiring
  cli.py         argparse entry point (`telepane`), preflight checks
  widgets/       tree.py, send_box.py, info.py, modals.py. UI only, no tmux logic
  styles.tcss    Textual CSS
tests/           mirror src units; test_live.py gated by TELEPANE_LIVE_TESTS
```

Read `tmux.py` before touching anything that talks to tmux; read `app.py` before
touching UI wiring.

## Execution sequence

Before writing code, in order:

1. **SEARCH FIRST**: find similar functionality or confirm none exists.
2. **REUSE FIRST**: extend existing modules; smallest change at the root cause.
3. **NO ASSUMPTIONS**: act only on files you have read and tool results. State
   unknowns; do not guess.
4. **CHALLENGE IDEAS**: if you see a flaw or better approach, say so directly.
5. **PLAN IF COMPLEX**: anything 3+ steps gets a short plan first.
6. **TEST BEFORE DONE**: exercise the changed flow, not just imports.

If a requirement is unclear, conflicts, or appears unsafe, STOP and ask.

## Code style

- Python ≥3.9, 4-space indent, `from __future__ import annotations` in modules
  using new-style type syntax. Format with `ruff format`. Only files you edited.
- Match the surrounding module's naming, comment density, and structure.
- No magic numbers. Name constants (−1/0/1 exempt).
- Functions with 3+ parameters take keyword arguments.
- One responsibility per module; new files stay under ~250 lines.
- No wildcard imports. Import order: stdlib, third-party, local.

### Comments

A comment states only a current constraint or behaviour the code cannot show.
No "what" comments, no history, no docstrings restating a signature. Prefer a
better name or smaller unit over a comment. Match the file's comment density.

## Configuration boundary

All environment access lives in `config.py`. Precedence for the config dir:
`XDG_CONFIG_HOME`, else `HOME/.config`, then `/telepane`. Never hardcode, log, or
persist secrets (this tool has none. Keep it that way).

## Architecture invariants

- **The tmux seam**: every external call is `tmux._run([...])`. Callers use the
  typed helpers in `tmux.py`; no other module imports `subprocess`.
- **Id targeting**: see Rule 1.
- **UI holds no tmux logic**: `widgets/` render and emit messages; `app.py`
  translates messages into `tmux` calls.
- **The poll loop never crashes the app**: `_tick` and `refresh_data` swallow
  transient tmux errors and retry on the next tick; the tree rebuilds when the
  server disappears and returns. Keep any tmux access in those paths wrapped.

### Deliberate limits: keep them, do not silently "fix"

- **No self-update.** Updates go through `pip`. Do not add code that installs or
  upgrades the package at runtime.
- **Preview is a snapshot**, not a live pty mirror. It is `capture-pane` polled
  on the refresh interval. Do not turn it into a terminal emulator.

## Testing

- Tests mirror source units; keep the mapping direct.
- Deterministic and isolated. Mock `tmux.subprocess.run` or the `tmux` helpers;
  no live server in the default suite.
- Mock-based tests prove call shape. `tests/test_live.py` exercises the real
  tmux server and is gated by `TELEPANE_LIVE_TESTS=1`. Run it at least once when
  changing `tmux.py`.
- Magic-number and file-length rules are relaxed in tests.

## Verification loop: before claiming done

1. `ruff check src tests`. Clean.
2. `ruff format --check src tests`. Clean.
3. `pytest`. Green.
4. Launch `telepane` in a separate tmux pane and `capture-pane` it; paste the real
   output. A summary is a claim, not evidence.

## Commits and git

- **Single-line Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`. No
  scope in parentheses, no body, no trailers, no `Co-Authored-By`.**
- Imperative mood, lowercase after the colon. One logical change per commit.
- Branches: `feat/…`, `fix/…`, `chore/…`, `hotfix/…`. Production branch: `main`.
- **Never push, open PRs, or merge without explicit human confirmation.**

## Pull requests

Factual: what changed and how it was verified. No narrative reasoning.

## Docs and messages (ASD-STE100 Simplified Technical English)

Write all documentation, error messages, notifications, and help text in
Simplified Technical English. Do not write documentation unless asked. Keep
`README.md` in sync when the CLI, key bindings, config keys, or send behaviour
change.

Rules:

- Keep an instruction to 20 words or fewer. Keep a description to 25 words or fewer.
- Write one instruction per sentence. Do not join steps with "and" or "then".
- Use active voice. Passive voice is allowed only when the actor is unknown.
- Use simple present, simple past, or simple future only.
- Do not use perfect tenses, continuous tenses, or "-ing" action verbs.
- Do not use "should", "would", "may", or "might". Use "can" or "must".
- Use one word for one meaning. Do not rotate synonyms. Always use "check".
- Do not use phrasal verbs. Use "remove", not "take off".
- Keep a noun cluster to 3 words or fewer.
- State the condition first. Write "If the light is red, stop.".
- Use a numbered list for a sequence of 3 or more steps.
- Keep one topic per paragraph. Keep a paragraph to 6 sentences or fewer.
- Keep articles and subjects. Keep "that" where it adds clarity.
- Do not use em-dashes.

If a fact needs exact wording for safety, keep the fact. Add the tag
`[STE Note: length required for precision]` after the sentence.

## Known issues: real, out of scope

- Pane rename is not offered (tmux has no first-class pane name; only titles).
- No favorites UI yet, though `Config.favorites` is persisted.

## Security

- Text sent to a pane is delivered literally (`send-keys -l --`); it is never
  interpreted as a command by telepane and never passes through a shell.
- Targets are tmux ids telepane itself read from the server. Never user strings.
- No dynamic evaluation of any input. No secrets, no remote content fetching.
- Named invariant: **no shell interpolation**, enforced by `tmux._run`, proven by
  `tests/test_tmux.py`.

## Hard guardrails

- Do not modify protected guidance files (`AGENTS.md`, `CLAUDE.md`, `.cursor/`,
  `.github/`) without explicit human approval.
- Do not run the TUI in the working pane (Rule 3). Do not run long-lived
  processes. Assume the user runs them.
- Do not touch subsystems unrelated to the current task; flag problems, don't fix
  them inline.
- Do not add dependencies outside the declared stack (`textual`) without a
  proposal including licence and security justification.
- Do not commit build output, `dist/`, or `.venv/`.

## Keeping this file in sync

This file, the re-delivered copies, and the code must never contradict each
other. Fix this file first, then re-deliver. Changes to this file are their own
commit, with human approval.
