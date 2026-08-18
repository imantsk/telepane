# tmux setup for agent panes

Driving an agent TUI over tmux needs a few settings beyond the defaults. None
of them is taste; each fixes a concrete failure you will otherwise hit.

Add to `~/.tmux.conf`, then `tmux source-file ~/.tmux.conf`:

```tmux
set -s escape-time 10
set -g default-terminal "tmux-256color"
set -as terminal-features ",*:RGB"
set -g variation-selector-always-wide on   # tmux >= 3.4
set -g mouse on
set -g history-limit 50000
set -g focus-events on
set -g set-clipboard on
```

## What each line prevents

| Setting | Failure it prevents |
|---|---|
| `escape-time 10` | Claude Code and codex bind ESC to interrupt. A high escape-time (500ms on older tmux) makes ESC lag or double-register. |
| `default-terminal` + `RGB` | Agent TUIs render 24-bit colour. Without true colour, diffs and syntax highlighting are wrong. |
| `variation-selector-always-wide` | Emoji status bars (base glyph + U+FE0F) drawn double-width desync tmux's cursor maths and corrupt the redraw. |
| `mouse on` | Click to select a pane, drag to resize, scroll into copy mode. telepane needs the tmux server, not this setting, but the owner does. |
| `history-limit 50000` | The 2000-line default loses a worker's long output; codex blows past it fast. |
| `focus-events on` | TUIs render stale after you click between panes if they never learn focus changed. |
| `set-clipboard on` | Copy-mode selections reach the system clipboard via OSC52. |

## Scrolling a worker pane

A redrawing worker TUI grabs the mouse while it renders, so the wheel does
nothing over it. Scroll it through copy mode instead: `Ctrl-b [`, then wheel
or PageUp, then `q` to return to live.

## iTerm2 notes

- With `mouse on`, hold Option while dragging for a native iTerm2 selection
  instead of a tmux one.
- `tmux -CC attach` renders tmux panes as native iTerm2 splits; native
  scroll, click, and copy work, and the copy-mode dance disappears.
