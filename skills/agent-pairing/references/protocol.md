# Protocol: the raw tmux mechanics

Everything here is what telepane does for the owner with a click. The driver
does it with commands. Same channel, same visibility.

## Identify the panes

```bash
tmux display-message -p '#{pane_id}'          # you, the driver, e.g. %0
tmux list-panes -a -F 'id=#{pane_id} cmd=#{pane_current_command} active=#{pane_active}'
```

Always use `%N` pane ids. `session:window.index` is a trap: indexes renumber
when any pane in the window is created or killed, so a command aimed at
`0:0.1` can land in a pane you did not mean, including your own.

## Spawn the worker

```bash
WORKER=$(tmux split-window -h -t %0 -c /path/to/repo -P -F '#{pane_id}' \
  'codex --dangerously-bypass-approvals-and-sandbox')
tmux select-pane -t %0
```

`-P -F '#{pane_id}'` prints the new pane's id; that is the only race-free way
to learn it. `select-pane` back to yourself immediately, otherwise the owner's
keystrokes land in the worker's TUI. Use `-v` instead of `-h` on narrow
terminals; two TUIs under ~120 columns each wrap badly enough to break screen
scraping.

## Send a message

```bash
tmux send-keys -t %1 -l 'your message'
sleep 1
tmux send-keys -t %1 Enter
```

Three non-negotiables:

- `-l` sends the string literally. Without it tmux parses words like `Enter`,
  `C-c`, or `Space` as key names.
- Enter is a **separate** call. TUIs debounce fast input; a combined call
  frequently submits a truncated message.
- The `sleep` between them matters. 1s is enough for codex; slower TUIs
  need 2.

Never send multi-line text. The first newline submits, and the rest arrives
as separate prompts, usually mid-sentence. Write a file and send a pointer:

```bash
tmux send-keys -t %1 -l 'Read /tmp/scratch/BRIEF.md in full and follow it.'
```

(telepane sends the same way: literal text, then Enter. What the owner types
in its message box obeys the same one-message-one-turn rule.)

## Read the worker

```bash
tmux capture-pane -p -t %1 | grep -v '^[[:space:]]*$' | tail -20   # current screen
tmux capture-pane -p -t %1 -S -200 | grep -v '^[[:space:]]*$'      # with scrollback
```

`-S -N` reaches N lines back into scrollback; needed after a long turn, since
the visible screen holds only the tail.

## Detect state

Screen scraping is the only interface a TUI gives you.

| State | How | Note |
|---|---|---|
| busy | pane matches the harness busy marker | absent for one frame during redraws; check twice |
| idle | busy marker absent twice, one interval apart | |
| approval | matches a confirm-prompt pattern | only in sandboxed mode; bypass modes never show it |

Answer a menu prompt by sending the bare number or letter with no `-l` and no
separate Enter: `tmux send-keys -t %1 '1'`.

## Wait without polling

Block in one Bash call rather than one tool call every 30 seconds:

```bash
for i in $(seq 1 180); do
  out=$(tmux capture-pane -p -t %1 2>/dev/null)
  echo "$out" | grep -qE 'Would you like to run|Press enter to confirm' && { echo APPROVAL; break; }
  echo "$out" | grep -q 'esc to interrupt' && { sleep 10; continue; }
  sleep 12
  tmux capture-pane -p -t %1 | grep -q 'esc to interrupt' || { echo IDLE; break; }
done
```

Swap the two patterns for the target harness's own markers.

## The back-channel

The worker types into your input the same way you type into its TUI:

```bash
tmux send-keys -t %0 -l 'CODEX: the tests contradict the brief, which wins?'
sleep 1
tmux send-keys -t %0 Enter
```

That submits into the driver's session, so it arrives as an ordinary user
turn. The prefix distinguishes it from the owner. You can also scrape your
own pane for missed ones:

```bash
tmux capture-pane -p -t %0 -S -60 | grep -F 'CODEX:' | tail -3
```
