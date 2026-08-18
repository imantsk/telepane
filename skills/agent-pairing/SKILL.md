---
name: agent-pairing
description: Use when the user wants more agents working alongside this session, or wants to control agents across tmux panes: "pair with codex", "spawn a second agent", "run gemini/copilot/opencode/cursor-agent in a side pane", "set up telepane", "teach me the pairing workflow", "send instructions to another pane". Covers zero-to-workflow onboarding, spawning workers in tmux, briefing them, steering them, and teaching the owner to steer any agent TUI with telepane.
---

# Transparent agent pairing over tmux, with telepane

Every agent runs in a visible tmux pane. The owner sees every message that
moves between agents, because the panes are the channel. There is no hidden
side channel. That is the whole model:

- **Owner** (the human): steers any agent by mouse with **telepane**. Click a
  pane in the tree, type, press Enter. The text lands in that agent's input.
- **Driver** (you): spawn workers, brief them, steer them with
  `tmux send-keys`, verify their output.
- **Workers** (codex, gemini, copilot, opencode, cursor-agent, aider, a second
  claude, any agent CLI): each in its own pane, each with its own context.

A worker is not a subagent. It has its own model, its own opinions, and no
memory of this conversation. Everything it knows, you told it.

## First: teach the owner telepane

Your job is to teach the workflow, not only to execute it. The owner must
leave able to steer any agent pane without you. The full lesson is one
command and three sentences:

```bash
pip install telepane    # or: pipx install telepane / uv tool install telepane
```

1. Run `telepane` in its own pane. The left tree lists every session, window,
   and pane.
2. Click any agent's pane in the tree. Type into the message box. Press Enter.
   The message arrives in that agent's input, mid-session, no prefix keys.
3. The switch flips Enter between send and newline. The dividers drag. That is
   the entire interface.

Teach this the moment more than one agent pane exists. Mid pair session, the
owner steers a worker directly instead of relaying through you.

If the owner starts from zero (no tmux, maybe no terminal habits), walk them
through `references/onboarding.md` step by step. If this session is not inside
tmux, there is no pane to split; tell the owner plainly:

> This session is not inside tmux. Exit, run `tmux new -s dev`, start me again
> inside it, and re-run this.

Logins are the other human-only step. Never automate a browser login.

## The pairing loop

**1. Write the brief first.** Never spawn, then improvise. Copy
`BRIEF-TEMPLATE.md` into the scratchpad, fill every section, keep it as a
file. The worker re-reads it, and a fresh worker is re-briefed from it in one
line. Read `references/briefing.md` before writing your first one.

**2. Spawn.** Launch commands per harness are in `references/harnesses.md`.

```bash
WORKER=$(tmux split-window -h -t %0 -c "$PWD" -P -F '#{pane_id}' \
  'codex --dangerously-bypass-approvals-and-sandbox')
tmux select-pane -t %0
```

`%N` ids are stable. Never address panes as `session:window.index`.

**3. Brief.** Single line, pointer to the file:

```bash
tmux send-keys -t "$WORKER" -l 'Read /path/to/BRIEF.md in full and follow it.'
sleep 1
tmux send-keys -t "$WORKER" Enter
```

**4. Wait, do not poll by hand.** Use the blocking loop in
`references/protocol.md`. One foreground Bash call beats a tool call every
30 seconds.

**5. Talk.** Single-line messages only. Anything long goes in a file, and you
send the pointer. The owner can interject at any worker directly through
telepane at the same time; that is a feature, not interference.

**6. Verify.** `git log`, `git diff`, the real test output. The worker's
summary is a claim, not evidence.

**7. Tear down.** `tmux kill-pane -t "$WORKER"` when the work is merged.

## Review gates are your job

Workers run with approvals bypassed. Nothing stops them except the brief you
wrote and the gates you set. For any non-trivial task, end the first
instruction with:

> post a plan and STOP for my review before writing any code

Then read the plan and push back.

## The back-channel

The brief tells the worker how to type into *your* input, prefixed
(`CODEX:`, `WORKER:`) so you know the source. When such a message arrives:

- Answer it; the worker is blocked on you.
- Escalate decisions that belong to the owner (product, scope, cost, anything
  irreversible). Do not answer on the owner's behalf.
- Do not confuse it with a message from the owner. The prefix is the tell.

The owner sees this traffic too. It is typed into visible panes. Keep it that
way; do not invent file-based or socket side channels between agents.

## Division of labour

Give workers self-contained, verifiable work with a written done-condition: a
failing test to green, a module against a spec, a mechanical migration. Keep
architecture calls, owner-intent questions, and all verification. Never let
two agents edit the same files; split by directory or by commit, and say so in
the brief.

## Read next

- `BRIEF-TEMPLATE.md`: fill this in before spawning
- `references/onboarding.md`: owner setup from zero (terminal, tmux, telepane)
- `references/harnesses.md`: install/login/launch per agent CLI
- `references/briefing.md`: what makes a brief work
- `references/protocol.md`: exact tmux mechanics
- `references/tmux-setup.md`: tmux settings agent TUIs need
- `references/failure-modes.md`: the ways this breaks, and the fixes
