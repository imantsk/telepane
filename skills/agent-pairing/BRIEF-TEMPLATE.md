# BRIEF: <project>

<!--
Fill every section. Delete nothing: an empty section is a signal you skipped
a decision, and the worker will make that decision for you.
Save to the scratchpad, then send the worker one line:
  Read <this file> in full and follow it.
Placeholders: %0 = driver pane, %1 = worker pane. Fill in the real ids from
`tmux split-window -P -F '#{pane_id}'`.
-->

## 0. Read first

- `<repo>/CLAUDE.md` and `<repo>/AGENTS.md`; AGENTS.md is the source of truth
  for workflow.
- Trust the code, not the docs. `docs/` can describe features that do not
  exist or are stale.
- Check what already exists before building anything.

## 1. tmux comms

- You are pane **%1**. The driver is pane **%0**. The owner can also type
  into your input directly (via telepane); treat unprefixed input as the
  owner.
- Message the driver at any time:
  ```
  tmux send-keys -t %0 -l "AGENT: <your message>"
  sleep 1
  tmux send-keys -t %0 Enter
  ```
- Prefix every message with `AGENT:` so the driver knows the source.
- Use it when the alternative is to stall or to guess: a decision that is
  genuinely the driver's or the owner's, a contradiction between code and
  docs, a blocked command, a driver instruction that turns out to be wrong,
  or any point where an assumption wastes work.
- Do **not** use it for routine progress. That goes in your normal replies.
- Do not go silent on a blocker.

## 2. You run with approvals bypassed; self-enforce these

There is no human gate on your commands. These are on you:

- **Commits:** <house style, e.g. single-line scopeless conventional commits,
  `feat:` / `fix:` / `chore:` / `docs:`, no body, no trailers>
- **Never** `git push`, `git pull`, or `git fetch` without asking the driver
  first via the back-channel. <why, e.g. the branch is published; unreviewed
  pushes are not acceptable>
- **Never** run a workspace-wide formatter. Format only files you edited.
  <a previous session churned 25 files this way and it had to be reverted>
- Tests first: red test, then implementation.
- Verify before claiming done: `<test command>` and `<lint command>`. Paste
  the real output, not a summary.
- Do not weaken or delete a test to make it pass. If an expectation is
  genuinely wrong, stop and say why via the back-channel.

## 3. Current state

- Branch `<branch>`, at `<sha>`, <in sync with origin / ahead by N>.
- Worktree is clean, except <list any deliberately dirty files and why>.
- Files the driver is editing right now, **do not touch**: <paths, or
  "none">.

## 4. Task

<One concrete task with a done-condition someone else could check. Prefer
"make these three named tests pass" over "improve validation".>

**Constraints:** <the specific things that must hold: existing seams to
reuse, error message phrasing that tests assert on, paths not to touch>

**Explicitly out of scope:** <what not to build>

## 5. How to proceed

1. Read the docs in section 0 and the files named in section 4.
2. Verify the claims in this brief against the actual code. If any is wrong,
   tell me via the back-channel before acting on it.
3. Post a plan (module layout, interfaces, test list) and **STOP for my
   review before writing any code**.
4. After approval, implement. Commit when green and report the hash.
