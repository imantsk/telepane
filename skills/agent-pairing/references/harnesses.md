# Harnesses: install, login, launch per agent CLI

Any agent CLI that runs in a terminal can be a worker pane. The pattern never
changes: install, login (human-only), launch in a bypass mode, learn its busy
marker. Flags below were verified against the versions noted; these tools
rename flags between releases, so re-check `--help` when a row fails.

| Agent | Install | Login | Launch as worker | Busy marker |
|---|---|---|---|---|
| claude (Claude Code) | `npm i -g @anthropic-ai/claude-code` or `curl -fsSL https://claude.ai/install.sh \| bash` | run `claude`, complete `/login` | `claude --dangerously-skip-permissions` | `esc to interrupt` |
| codex (OpenAI) | `npm i -g @openai/codex` or `brew install codex` | `codex login` | `codex --dangerously-bypass-approvals-and-sandbox` | `esc to interrupt` |
| gemini (Google) | `npm i -g @google/gemini-cli` or `brew install gemini-cli` | run `gemini` once, browser login or `GEMINI_API_KEY` | `gemini --yolo` | `esc to cancel`, `Thinking` |
| copilot (GitHub) | `npm i -g @github/copilot` | run `copilot`, complete `/login` | `copilot --allow-all-tools` (or the wider `--allow-all`) | check footer on first run |
| opencode | `npm i -g opencode-ai` or `curl -fsSL https://opencode.ai/install \| bash` | `opencode auth login` | `opencode` (no bypass flag; permissions live in `opencode.json`) | check footer on first run |
| cursor-agent | `curl https://cursor.com/install -fsS \| bash` | `cursor-agent login` | `cursor-agent --yolo` (alias of `-f, --force`) | check footer on first run |
| aider | `uv tool install aider-chat` | export the provider key (`ANTHROPIC_API_KEY`, ...) | `aider --yes-always` | prompt-loop; watch for the prompt marker returning |

Flag verification (2026-08-18, macOS): claude 2.1.234, codex 0.147.0,
gemini 0.29.5, copilot 1.0.61, opencode 1.18.18, cursor-agent 2026.08.11.
aider row is unverified scaffold. Codex removed `--yolo` around 0.147; older
guides still show it.

## Bypass modes and the bargain

`--dangerously-*`, `--yolo`, `--allow-all-tools`, `--yes-always`: all remove
the human approval gate. The brief replaces it. Never launch a worker in a
bypass mode without a brief whose house-rules section names the specific
prohibitions (push policy, formatter scope, test integrity). See
`briefing.md`. Where a sandboxed middle ground exists (codex
`--ask-for-approval`, `--sandbox`; gemini `--approval-mode auto_edit`),
prefer it for early sessions with a new harness.

## Learning a new harness

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
5. Add the row to this table with the version you verified.

Prompt-loop tools (aider style, REPLs) have no persistent busy footer, so
idle detection is weak. Put an explicit done-signal in the brief instead:
"reply DONE when the tests are green".

## IDE-bound agents

Some agents (Google Antigravity, Cursor's IDE side) live in an editor, not a
terminal. They cannot be a tmux pane, so telepane cannot steer them, but the
reverse works: their built-in terminals can host tmux, telepane, and worker
panes like any other terminal. Treat the IDE agent as a separate peer, not a
pane.
