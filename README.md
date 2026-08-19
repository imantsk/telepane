# telepane

A mouse-driven [tmux](https://github.com/tmux/tmux) control dashboard for your
terminal. The send box is the core function. Select a pane in the tree. Type a
message. Telepane sends the message to that pane. You control an agent or a REPL
in a different pane. You do not leave your current pane.

Telepane uses [Textual](https://textual.textualize.io). The mouse and the
keyboard both work.

```
┌──────────────┬──────────────────────────────────────┐
│ ● main    2w │ tmux 3.7  pid 1690  4 sess 9 win     │
│  ▸ 0:edit 2p │ target %6  (pane: edit.1)            │
│   ◆ %0 nvim  │ cmd claude  pid 51231  size 120×40   │
│   ◇ %1 bash  │ ┌ preview ─────────────────────────┐ │
│ ○ work    1w │ │ > waiting for input…             │ │
│   ▸ 0:sh  1p │ └──────────────────────────────────┘ │
│              │ target: %6                           │
│              │ ┌ message ─────────────────────────┐ │
│              │ │ run the tests and report back    │ │
│              │ └──────────────────────────────────┘ │
│              │        [x] Enter  [Clear] [ Send ▶ ] │
└──────────────┴──────────────────────────────────────┘
```

## Pair with your agent

You do not have to set any of this up yourself. Tell your coding agent:

```md
Install telepane from pip and set me up for agent pairing.
```

The repo ships a Claude Code plugin with an `agent-pairing` skill. The skill
teaches the agent the full workflow: terminal and tmux setup, worker agents in
side panes (claude, codex, gemini, copilot, opencode, cursor-agent, and
others), briefing, and teardown. You steer any of those agents mid-session
with telepane: select the target pane, type your message, send it.

## Why not just switch panes?

You can. But you sometimes control several agents across many panes. One control
surface is faster in this case. It lists all the panes. It shows the state of
each pane. You type to any pane and you keep your place.

## Design notes

- Every tmux call is an argv list through `subprocess`. Telepane uses no shell.
- Telepane addresses panes by the stable tmux ids (`$`, `@`, `%`).
- Telepane delivers text with `send-keys -l --` (literal).

## Install the `skill` manually

```bash
$ claude plugin marketplace add imantsk/telepane
# then inside claude: /plugin install telepane
```

## Install `telepane` manually

```bash
$ pip install telepane
# or: pipx install telepane
# or: uv tool install telepane
```

Telepane needs Python 3.9 or higher and a running tmux server.

PNG screenshots need one more package. The cairosvg package needs the native cairo library.
To install the extra, run this command:

```bash
$ pip install "telepane[png]"
```

## Use

```bash
$ telepane     # launch the TUI dashboard
$ telepane -v  # version
```

- Click a session, window, or pane in the left tree to select the target.
- Type a message in the message box. Press **Enter** to send it. You can also
  click **Send ▶** or press `Ctrl+S`.
- The **⏎ to send / ⏎ to newline** switch changes the function of Enter:
  - *⏎ to send*: Enter sends the message. Shift+Enter adds a new line.
  - *⏎ to newline*: Enter adds a new line. Shift+Enter sends the message.

  Shift+Enter needs a terminal that reports extended keys.
- Drag the dotted dividers (┆ and ┄) to resize the sidebar and the message
  box. The message box goes from one input line to the full height. At full
  height, the box hides the viewer.
- Markdown highlighting in the message box is on by default. To disable it, open
  Settings with the `,` key.
- The message box shows a live markdown preview. Completed code fences render
  as rules with the language tag. Bold, italic, links, and headings render
  styled with their markers hidden. The cursor line and broken syntax show raw
  text.
- **Shift+Click** a split key in the footer to pick what runs in the new
  pane: an installed agent CLI (claude, codex, gemini, ...) or a custom
  command.
- **Shift+Click** a link to open it in your browser. Pick the browser in
  Settings (system default, or any installed browser). The toggle
  "Shift+Click opens links" turns the feature off.

Telepane always sends your text and an Enter key to the target pane. (The Enter key submits the message in that pane.)

### Keys

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `Ctrl+S` | send message | `n` | new session |
| `r` | refresh | `R` | rename session/window |
| `s` | split pane → | `k` | kill selected |
| `v` | split pane ↓ | `,` | settings |
| `f` | focus tree | `i` | focus input |
| `q` | quit | | |

Telepane saves settings to `~/.config/telepane/config.json`.

## License

MIT
