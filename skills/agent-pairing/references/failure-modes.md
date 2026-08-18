# Failure modes

Every entry here comes from a real pairing session, not from theory.

## Pane index drift

**Symptom:** a prompt meant for the worker appears in the driver's own input,
or a command targets the wrong pane.
**Cause:** addressing panes as `0:0.1`. Indexes renumber on every pane
create/kill.
**Fix:** use `%N` ids everywhere; capture them at spawn with
`split-window -P -F '#{pane_id}'`. telepane targets by `%N` id for the same
reason.
**If it already happened:** nothing was executed if you catch it before
Enter; clear the input with `C-u`. Say so plainly rather than quietly
retrying.

## Truncated or split messages

**Symptom:** the worker replies to half a sentence, or to three fragments.
**Cause:** Enter sent in the same `send-keys` call, or a newline inside the
message.
**Fix:** literal send, sleep, separate Enter. Never multi-line; use a file
and send a pointer.

## Resume reattaches an exhausted session

**Symptom:** the worker compacts immediately, forgets the brief, and starts
acting on stale intent from a previous task.
**Cause:** a resume flag reattached a session already near its context limit.
**Fix:** prefer a fresh worker plus the brief file. Before trusting a resumed
worker, check what it thinks it is doing; one resumed session's next intent
was to *delete* the uncommitted red tests it was supposed to make pass.

## Silent worker

**Symptom:** long busy period, no output, no questions.
**Cause:** the brief never told it a back-channel exists, or told it only
once in an early session that compacted since.
**Fix:** put the back-channel in the **brief file**, not in a chat message.
Re-briefing a fresh worker then re-establishes it automatically.

## Runaway worker in bypass mode

**Symptom:** a workspace-wide format churns 25 files; an unreviewed
`git push`; a test deleted instead of fixed.
**Cause:** the bypass flag removed the approval gate and the brief did not
replace it.
**Fix:** the house-rules section of the brief is not boilerplate. Name the
specific prohibitions, and say why; workers respect a rule with a reason
attached far more reliably than a bare "don't".

## Two agents editing the same file

**Symptom:** one agent's edit silently reverts the other's; git shows churn.
**Cause:** no ownership split.
**Fix:** partition by directory or by commit in the brief. If the work
genuinely overlaps, give the worker a git worktree of its own instead.

## Update prompt swallows the first message

**Symptom:** the first message goes nowhere; the pane shows a version banner
with a numbered menu.
**Cause:** the agent CLI prompted for a self-update on launch.
**Fix:** wait for the pane to settle before briefing. If it happens anyway,
answer the menu with a bare key (`tmux send-keys -t %N '2'`) and resend.

## Worker claims done, is not

**Symptom:** "all tests pass"; they do not.
**Fix:** verify yourself. `git log`, `git diff`, run the test command. The
worker's summary is a claim; the exit code is evidence. This is the driver's
job and it is not optional.

## Owner and driver type into the same worker at once

**Symptom:** interleaved fragments in the worker's input; a half-command
submits.
**Cause:** the owner sent via telepane while the driver was mid `send-keys`
sequence.
**Fix:** coordination, not tooling. When the owner takes over a worker,
the driver stops steering that pane until the owner says done. Watch the
worker's pane for input you did not send before typing into it.
