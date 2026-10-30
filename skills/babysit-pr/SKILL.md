---
name: babysit-pr
description: Monitor a pull request through CI and review. Use when the user asks to monitor, watch, or babysit a PR, or when a hook reports that a new PR was created.
---

# Babysit PR

Watch a PR until it merges or closes. Fix CI failures and keep the branch
current on your own. Triage review feedback, but change nothing for it until
the user approves in writing. Tell the user when the PR is ready to merge.

Almost all review feedback comes from AI review bots. Bots are useful but
often wrong, and acting on every finding bloats the PR with slop. The user
decides which findings get addressed.

## First run: ask about auto-merge

The first time you babysit a PR, before you start watching, ask the user
once with the question tool: "Enable auto-merge for PR #<n> (<link>)?" Say
in the question that GitHub would then merge as soon as required checks and
reviews pass, even if triage items are still open. Options, in order: "No,
notify me when it is ready", "Yes, enable auto-merge". Do not ask again on
later wakes for the same PR.

If the user says yes:

1. Check that the repo allows it:
   `gh repo view <owner/name> --json autoMergeAllowed,squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed`.
   If `autoMergeAllowed` is false, tell the user and continue without it.
2. Use the merge method the repo uses. If more than one is allowed, match
   recent merged PRs.
3. Run `gh pr merge <n> --auto --squash` (or `--merge` or `--rebase`), then
   confirm with `gh pr view <n> --json autoMergeRequest`.

Without a question tool, leave auto-merge off and mention in your first
message that the user can ask for it.

## Waiting

Never write your own watcher, polling loop, or `sleep` loop. Use one watcher
per PR: `watch_pull_request` in T3 Code, `pr-wait` everywhere else. Never run
both on the same PR. Every watcher on a GitHub account shares one rate limit.

### In T3 Code: `watch_pull_request`

Handle existing checks and comments first. Then call `watch_pull_request`
and end your turn. T3 Code wakes you when a check fails, the required checks
pass, someone comments or reviews, or the branch conflicts. The watch stays
on after each wake, so do not call it again.

- **Only the thread that owns the PR watches it.** A delegated child task
  never calls `watch_pull_request`. Do not watch PRs you are not working on.
- **A wake is news, not a merge decision.**
- **"Stopped watching, could not read it"** usually means GitHub's rate
  limit is used up. Run `gh api rate_limit --jq .resources.graphql`. If
  `remaining` is near 0, wait for `reset` with one background command, then
  watch again. Never watch again in a tight loop.

### Everywhere else: `pr-wait`

Use `scripts/pr-wait` from this skill's directory (absolute path):

```bash
pr-wait <pr> [--repo owner/name] --until any-change
```

It prints one line per real event and exits after the first poll with news.
Handle the event, then start it again. It remembers what it already reported,
so nothing is lost or repeated between runs. In Claude Code, run it with the
Monitor tool (`timeout_ms: 3600000`). If it says another pid already watches
the PR, do not start a second one.

With either watcher: when an event needs no action, end your turn without a
message. Never post or say "still waiting".

## CI failures: fix without asking

The user pre-approves fixing CI. For each failed check on the latest head:

1. Read the logs (`gh run view <id> --log-failed`) and find the cause.
2. **Flake or infrastructure** (timeout, runner died, network, rate limit,
   a test that passes on rerun with no related change): rerun once with
   `gh run rerun <id> --failed`. If it fails again, treat it as real.
3. **Caused by this PR:** make the smallest fix. Reproduce the failure
   locally when you can, and run the same check locally before you push.
   Commit and push normally. Never force-push for a CI fix.
4. **Not caused by this PR** (already failing on the base branch, broken
   secrets or CI config you would have to change outside the PR's scope):
   do not fix it. Report it to the user.

A CI fix must not change behavior beyond what the PR already intends, and
must not act on review feedback. If the only fix is a real design change,
stop and ask.

## Review feedback: triage only

Covers every comment, review, and thread from bots and humans that is newer
than your last triage. Without the user's written approval in this thread, do
not:

- change code because of feedback,
- reply to, resolve, or dismiss any comment or thread,
- request or re-request reviews.

### Triage

For each new finding, read the cited code and decide yourself. Do not trust
the bot's severity. Classify it:

- **Fix:** a real defect: a bug in what the PR intends to do, a security
  issue, or doc text that contradicts shipped behavior. Say what breaks and
  the smallest fix.
- **Optional:** correct but not needed: edge cases that do not matter, extra
  tests, small performance costs, style, extra compatibility. Recommend
  rebutting it.
- **Reject:** a false positive. Cite the code or behavior that shows it is
  wrong.
- **Already handled:** fixed by a later commit, or a duplicate of another
  item.

Only Fix items get changed. Recommend rebutting everything else with a short
reason. Never recommend a follow-up PR or issue for an item you don't fix:
the rebuttal is the whole answer. When a reviewer repeats a finding after a
rebuttal, recommend a one-line reply that points back to it, not a fix.

When the only things blocking the PR are a bot repeating a review that
requests changes, or missing human approvals, tell the user and stop. More
pushes would only start another bot round.

Give each item a stable id (R1, R2, ...) that continues across triage rounds.
Record the author, file:line, link, a one-line claim, the class, your
recommendation, and the size of the fix.

### Handing it to the user

When triage is done, bring the user into the thread:

1. Post the triage as a compact table: id, author, location, claim, class,
   recommendation.
2. Ask how to proceed with the harness's question tool (`AskUserQuestion` in
   Claude Code) so the thread shows that it waits on the user. Put the PR
   link and the item ids in the question. Options, in order: "Walk me
   through each item", "Apply my recommendations (<ids>)", "Fix only the
   Fix items", "Do nothing for now". The user can pick Other to name items.
3. Without a question tool, end your turn with the triage table and the
   same options at the top of your message.

A CI failure can still arrive while you wait. Handle it as usual when you
are next woken.

### Item-by-item walkthrough

When the user asks for it, go through the open items one at a time, in id
order. For each item, send one message with:

- **What the reviewer asked:** who left it, a link, and their point in
  plain words. Quote the key line if it helps.
- **What the code does now:** the relevant snippet or file:line, and
  whether the reviewer's claim holds.
- **My recommendation:** the class, what you would do (or why not), and
  the size and risk of the change.

Then stop and let the user ask questions. Answer them, reading more code or
running checks when that settles the question. Change nothing during the
walkthrough. When the user is ready, record one decision for the item with
the question tool: "Implement", "Implement differently" (the user says
how), "Rebut", or "Ignore". Then move to the next item.

After the last item, show a summary of all decisions and implement the
approved ones together, as described below. Do not open issues or PRs for
items you don't fix unless the user asks.

### After approval

Act only on the items the user approved, in the way they approved:

- **Approved fixes:** make the smallest change for each, prove them with
  the relevant checks or tests, and push them together once. Every push
  starts another bot round and can dismiss approvals. Then reply on each
  thread with what changed and resolve it.
- **Approved rebuttal:** reply with the written reason, then resolve the
  thread.
- **Not mentioned:** leave alone. Keep it open in the ledger and list it
  again in the next triage.

Use the `leaving-pr-comments` skill for every comment, including its unslop
pass. Resolve a thread only
after the reply posted. A new push re-triggers bots, so triage what they post
next the same way.

## GitHub rate limits

`gh pr create`, `gh pr view`, and `gh pr checks` use GraphQL. When GraphQL is
used up, the REST limit is separate and usually still has room. Use
`gh api repos/<owner>/<repo>/pulls/<n>` to read a PR, and
`gh api repos/<owner>/<repo>/commits/<sha>/check-runs` for checks.

## Base branch and merging

`pr-wait` reports when new base commits touch this PR's files, and when the
PR becomes BEHIND or DIRTY. `watch_pull_request` reports conflicts only, so
check `mergeStateStatus` yourself whenever checks finish.

### Keeping the branch current: no need to ask

When the PR is BEHIND or DIRTY, update it on your own:

1. `git fetch origin`, then rebase this PR's branch onto the base branch.
2. Resolve conflicts so the PR keeps its intent and the base branch keeps
   its changes.
3. Run the checks that cover the touched files, then push with
   `git push --force-with-lease`. Only ever force-push this PR's own branch.
4. Mention the update in your next message to the user, with any conflicts
   you resolved.

Stop and ask first, with the base commits and files involved, when the base
changes affect what this PR is trying to do:

- they change the same behavior this PR changes, so the result needs a
  decision rather than a mechanical merge,
- they make part or all of this PR redundant,
- they change an API, schema, or contract this PR depends on, so the PR
  needs real rework rather than a small fix,
- a conflict has two reasonable resolutions that behave differently.

If another PR makes this one obsolete, tell the user. Never close the PR
unless they ask.

### Ready to merge: notify the user

Check readiness when checks finish, after a review, and after each push:

```bash
gh pr view <pr> --json state,isDraft,reviewDecision,mergeStateStatus,headRefOid
```

The PR is mergeable when it is open, not a draft, every required check is
green, `reviewDecision` is `APPROVED` (or empty when the repo requires no
reviews), and `mergeStateStatus` is `CLEAN`.

When it first becomes mergeable on a head commit, notify the user once for
that head:

- Send a push notification if the harness has one (`PushNotification` in
  Claude Code): "PR #<n> is ready to merge".
- Post a message that starts with "Ready to merge:", with the PR link, the
  head commit, the checks and approvals, and any open triage items.

If auto-merge is on, skip the ready notification. If you are woken when
GitHub merges the PR, report the merge commit and any triage items that were
still open. T3 Code marks the thread done on merge by itself.

Never merge directly, enable auto-merge, or enter a merge queue unless the
user explicitly asks, either in the first-run question or later. Keep
watching after you notify: a new comment, review, or push can change the
state.

## Stopping

The watch ends on its own when the PR merges or closes. If the user asks you
to stop, call `unwatch_pull_request` in T3 Code, or stop `pr-wait`.
