# Briefing: what makes a worker useful

The worker's entire understanding of the job is the brief. Everything vague
in it becomes a decision the worker makes without you.

## Why a file, not a chat message

- It survives compaction. A worker that has forgotten everything is restored
  with one line: "Re-read BRIEF.md."
- A fresh worker gets the same context as the old one, for free.
- The owner can read it, and correct it, before any code is written.
- Multi-line instructions cannot be typed into a TUI anyway.

Write it to the session scratchpad, then send a pointer.

## The six sections

**0. Read first.** Which repo docs are authoritative, plus the two rules that
prevent the most waste: trust the code, not the docs; check what already
exists before building.

**1. Comms.** Its pane id, your pane id, the exact back-channel command, and,
crucially, *when* to use it. "Ask if unsure" produces nothing. Enumerate the
triggers: a decision that is genuinely yours or the owner's, a contradiction
between code and docs, a blocked command, an instruction of yours that turns
out to be wrong, any point where a guess wastes work. Then rule out the
opposite: routine progress goes in normal replies, not the back-channel.

**2. House rules.** In a bypass mode this section *is* the safety system.
Be specific and give reasons:

> Never run a workspace-wide formatter. Format only files you edited. A
> previous session churned 25 files this way and it had to be reverted.

carries far more weight than "don't reformat everything". Cover at minimum:
commit format, push/pull/fetch policy, formatter scope, test-first, and the
exact verification commands.

**3. Current state.** Branch, sha, sync status, and the one people forget:
which files *you* are editing right now, so the worker stays out of them.

**4. Task.** One task with a done-condition a third party could check. "Make
these three named tests pass" beats "improve validation". List the
constraints that are not negotiable: existing seams to reuse, error phrasing
the tests assert on, paths not to touch. State what is out of scope; workers
expand scope when it is undefined.

**5. How to proceed.** Always end with a review gate:

> Verify the claims in this brief against the code. If any is wrong, tell me
> via the back-channel before acting on it. Then post a plan and STOP for my
> review before writing any code.

The verification step matters: briefs go stale, and a worker that checks
yours catches your mistakes before they become its commits.

## Anti-patterns

- **Spawn first, brief later.** The worker starts forming intent the moment
  it boots. Brief before, or at, spawn.
- **A brief that restates the repo docs.** Point at them instead. Duplication
  goes stale and eats the worker's context.
- **No done-condition.** The worker will invent one, and it will be bigger
  than yours.
- **Prohibitions without reasons.** They get rationalised away under
  pressure.
- **Skipping the gate on "small" tasks.** Small tasks are where scope creep
  is cheapest to prevent and most often skipped.
