# Onboarding: owner setup from zero

The owner's shortcut: tell any agent

> Install telepane from pip and set me up for agent pairing.

and the agent walks this file with them. Teach each step; do not silently do
it. The owner must be able to rebuild this on a new machine.

## 1. A terminal that can host the workflow

tmux does the splitting, so the terminal only needs true colour and good font
rendering. Tabs and native splits are a bonus, not a requirement.

| OS | Suggested | Notes |
|---|---|---|
| macOS | iTerm2 | `brew install --cask iterm2`. WezTerm, kitty, and Ghostty also work. `tmux -CC attach` gives native panes in iTerm2. |
| Windows | Windows Terminal + WSL2 | tmux needs a Unix userland. Install Ubuntu in WSL2, run everything inside it. |
| Debian/Ubuntu | GNOME Terminal, kitty, or WezTerm | Whatever ships is fine if it reports 256-colour or better. |
| Arch | kitty, WezTerm, or Alacritty + tmux | `pacman -S kitty`. |

## 2. Install tmux

```bash
brew install tmux        # macOS
sudo apt install tmux    # Debian/Ubuntu/WSL2
sudo pacman -S tmux      # Arch
tmux -V                  # verify: 3.2 or newer wanted, 3.4+ ideal
```

Then apply the settings in `tmux-setup.md`. Each one prevents a concrete
failure with agent TUIs (laggy ESC, wrong colours, dead mouse).

## 3. Start a session

```bash
tmux new -s dev
```

Teach the three moves the owner cannot avoid knowing, even mouse-first:

- `Ctrl-b %` split right, `Ctrl-b "` split down
- `Ctrl-b [` scroll a pane (copy mode), `q` to leave
- `tmux attach -t dev` to come back after a disconnect

Everything else is telepane's job.

## 4. Install and launch telepane

```bash
pip install telepane     # or: pipx install telepane / uv tool install telepane
```

Split a pane for it and run `telepane` there. Give it a narrow side pane; it
is a dashboard, not a workspace. Then have the owner do this once, hands on:

1. Click a pane in the tree. The target line shows its id and command.
2. Type `echo hello from telepane` in the message box. Press Enter.
3. Watch the text land and execute in the target pane.

That echo into a shell pane is the whole mechanism. An agent TUI is steered
the same way: click its pane, type the instruction, Enter.

## 5. First worker

Start the driver agent (this session) in one pane. Spawn one worker with the
loop in `SKILL.md`, or have the owner pick a harness from `harnesses.md` and
launch it by hand in a fresh pane. Then have the owner send the worker its
first mid-session instruction through telepane, not through you. When that
works, the workflow is adopted; everything after is scale.
