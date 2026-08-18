# Harnesses: install, login, launch per agent CLI

Any agent CLI that runs in a terminal can be a worker pane. The pattern never
changes: install, login (human-only), launch in a bypass mode, learn its busy
marker.

The table is a starting point, not the truth. These tools rename flags
between releases and differ across platforms. Before the first spawn of any
harness, verify its row in the running environment:

```bash
command -v codex                # installed?
codex --version                 # which release?
codex --help | grep -i bypass   # does the launch flag still exist?
```

If a flag is gone, find its replacement in `--help` and correct the row.

| Agent | Install | Login | Launch as worker | Busy marker |
|---|---|---|---|---|
| claude (Claude Code) | `npm i -g @anthropic-ai/claude-code` or `curl -fsSL https://claude.ai/install.sh \| bash` | run `claude`, complete `/login` | `claude --dangerously-skip-permissions` | `esc to interrupt` |
| codex (OpenAI) | `npm i -g @openai/codex` | `codex login` | `codex --dangerously-bypass-approvals-and-sandbox` (older releases: `--yolo`) | `esc to interrupt` |
| gemini (Google) | `npm i -g @google/gemini-cli` | run `gemini` once, browser login or `GEMINI_API_KEY` | `gemini --yolo` | `esc to cancel`, `Thinking` |
| copilot (GitHub) | `npm i -g @github/copilot` | run `copilot`, complete `/login` | `copilot --allow-all-tools` (or the wider `--allow-all`) | check the footer on first run |
| opencode | `npm i -g opencode-ai` or `curl -fsSL https://opencode.ai/install \| bash` | `opencode auth login` | `opencode` (no bypass flag; permissions live in `opencode.json`) | check the footer on first run |
| cursor-agent | `curl https://cursor.com/install -fsS \| bash` | `cursor-agent login` | `cursor-agent --yolo` (alias of `-f, --force`) | check the footer on first run |
| aider | `uv tool install aider-chat` | export the provider key (`ANTHROPIC_API_KEY`, ...) | `aider --yes-always` | prompt-loop; watch for the prompt marker to return |

## Bypass modes and the bargain

`--dangerously-*`, `--yolo`, `--allow-all-tools`, `--yes-always`: all remove
the human approval gate. The brief replaces it. Never launch a worker in a
bypass mode without a brief whose house-rules section names the specific
prohibitions (push policy, formatter scope, test integrity). See
`briefing.md`. Where a sandboxed middle ground exists (codex
`--ask-for-approval` and `--sandbox`, gemini `--approval-mode auto_edit`),
prefer it for early sessions with a new harness.

## Learn a new harness

For any agent CLI not in the table (new tools appear monthly):

1. Find its install command and login step in its docs; the login is the
   owner's job.
2. Launch it plainly in a spare pane. Give it a one-minute task.
3. `tmux capture-pane -p -t %N` while it works. The persistent footer text it
   shows mid-turn is the busy marker.
4. Find its approval-bypass flag in `--help`. If none exists, check its
   config file for a permissions block (opencode style), or keep it sandboxed
   and answer its menus with `tmux send-keys -t %N '1'` (bare key, no `-l`,
   no Enter).
5. Add the row to this table.

Prompt-loop tools (aider style, REPLs) have no persistent busy footer, so
idle detection is weak. Put an explicit done-signal in the brief instead:
"reply DONE when the tests are green".

## IDE-bound agents

Some agents (Google Antigravity, Cursor's IDE side) live in an editor, not a
terminal. They cannot be a tmux pane, so telepane cannot steer them, but the
reverse works: their built-in terminals can host tmux, telepane, and worker
panes like any other terminal. Treat the IDE agent as a separate peer, not a
pane.
