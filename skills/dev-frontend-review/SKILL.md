---
name: dev-frontend-review
description: Dev's frontend review assistant for noor-basal/noor. Runs his morning digest of open frontend PRs, saves his notes and direction calls about PRs, drafts first reviews and re-reviews in his voice against his rubric, and runs the branch on web, iOS and Android next to the prototype. Use when Dev says "digest", "what's waiting on me", "triage my queue", "note for #N", "review #N", "re-review #N", "visual check #N" or "finish visuals".
---

# Dev's frontend review

The scripts and rubric sit next to this file. Run them by path, with an authenticated `gh`: for example `python3 -I <this skill's directory>/review-queue.py`.
Dev's notes, queue snapshots and drafts live in `~/dev-review` (override with `DEV_REVIEW_HOME`). Every `notes/`, `state/` and `drafts/` path below is relative to it.
Nothing in this skill posts to GitHub, merges, or re-requests a review until Dev says so in writing.
Notes about teammates' PRs stay in `~/dev-review`. Never commit them to a repository, including devstack.

| File | What it is |
|---|---|
| `review-queue.py` | Open frontend PRs grouped by whose turn it is, including Dev's own. `--since-last` saves a snapshot in `~/dev-review/state/` and lists what moved since the last one. |
| `pr-context.py N` | Everything for one PR: Dev's notes, prototype references, files by surface, CI, verdicts, Dev's earlier reviews and open threads, and what changed since his last review. |
| `REVIEW-RUBRIC.md` | Dev's standing rules, each with the PR where he applied it, and the shape of his reviews. |
| `VISUAL-CHECK.md` | How to run the branch next to the prototype. |
| `notes/prs/<N>.md` | Dev's direction calls for one PR. |
| `notes/series/<name>.md` | Rules shared by a series of PRs. The first line lists them: `PRs: #16040 #16042`. |
| `notes/decisions.md` | Calls that apply beyond one PR. Newest first. |
| `notes/prototypes.md` | Where each named prototype lives. |
| `drafts/<N>/` | Review drafts and visual captures waiting for Dev. |

## Mode 1: morning digest

Runs on a schedule on weekdays, or when Dev says "digest".

1. Run `python3 -I <skill dir>/review-queue.py --since-last`, then `--json` for the details.
2. For every PR in "New commits since your last review", run `pr-context.py N` and draft the re-review (Mode 3). Run the visual check on those with UI changes.
3. Write the digest as one message, in this order:
   1. **What moved**: the "Changed since last run" list, in one line per PR.
   2. **Re-reviews ready**: each PR, whether the new commits answer Dev's open requests (done, partly, not done), and the path to its draft in `drafts/<N>/`.
   3. **First reviews**, oldest first, split into "needs you" (new UX, architecture, cross-platform features, design-system changes), "could go to a co-owner" (release, CI and signing to @chanhe-amzn; One Chat and navigation to @tjfazio) and "rubber-stamp" (generated clients, frozen-app-only, docs-only).
   4. **Drafts to give direction on now**: drafts with a UI or architecture choice that is cheaper to steer before the author builds further. One line each on the choice.
   5. **Your PRs**: who blocks each, failing checks, and requests Dev hasn't answered.
   6. **Direction questions**: numbered, at most five, for the PRs at the top of "needs you". Each one asks for a decision only Dev can make (scope, reuse or build, defer or not, which prototype screen). Dev answers by number in the thread.
   7. **Needs you**: anything the agent couldn't finish, such as "prototype capture needs `mwinit -f`" or a build that failed for an environment reason.
4. Keep it short. Link every PR. Don't paste drafts into the digest.

## Mode 2: save Dev's notes

When Dev says "note for #N: ...", answers a direction question, or states a call about a PR in any session:

- A call about one PR goes in `notes/prs/<N>.md`, as a dated line with his words. Keep his wording.
- A call about a series goes in `notes/series/<name>.md`. Create the file with its `PRs:` line if it doesn't exist.
- A call that applies to future PRs ("icons round up on a tie", "no dark treatment without design sign-off") also goes in `notes/decisions.md`, with the date and the PR.
- A prototype location goes in `notes/prototypes.md`.

Tell Dev in one line where you saved it. When a note contradicts an earlier one, replace the earlier one and say so.
After Dev posts a review, read it and add any new standing decision to `notes/decisions.md`.

## Mode 3: draft a review for PR #N

1. `mkdir -p ~/dev-review/drafts/<N> && python3 -I <skill dir>/pr-context.py N > ~/dev-review/drafts/<N>/context.md` and read all of it. Dev's notes come first and override the rubric where they differ.
2. Read `REVIEW-RUBRIC.md`.
3. Check out the PR head in a scratch worktree (`git fetch origin pull/<N>/head:pr-<N> && git worktree add /tmp/pr-<N> pr-<N>`). Read the specs and ADRs the PR touches or cites.
4. **Re-review:** grade only against Dev's earlier requests and acceptance criteria, item by item (done, not done, partly), with evidence. Raise a new blocker only if the new commits introduced it, or it is a correctness or security defect a user would hit. Say which.
5. **First review:** walk the rubric sections in order. Cheap checks to run:
   - parity: for every changed `apps/mobile/ios` file, find the Android counterpart, and the reverse. Diff user-facing strings across the two apps;
   - removals: `git grep -n -i` the retired names under `apps/mobile`;
   - design system: literals in changed web and mobile UI lines against `.agents/rules/frontend.md` and the mobile appearance docs; `node packages/design-system/build.mjs --verify` if the catalog changed;
   - hygiene: new files under `docs/` or `.agents/plans/`, review-evidence media, added `AGENTS.md` lines, spec sections that narrate review history;
   - flaky tests: in changed test files, grep for fixed sleeps (`sleep`, `Thread.sleep`, `setTimeout`, `waitForTimeout`, `asyncAfter`), `delay(` inside `runTest`, real clocks (`Date.now`, `Instant.now`, `Date()`), positional or CSS selectors, and new retries or skips. Check the PR's CI history for checks that failed and then passed on the same head;
   - PR body: screenshots from both apps for UI changes, and the tests actually run.
6. **Visual check:** for a UI change, follow `VISUAL-CHECK.md` and add its findings to the draft.
7. Write the draft to `drafts/<N>/review.md` in the shape at the end of the rubric. Every blocking item has `file:line` and the exact fix. Mark anything you inferred but didn't verify. If the PR needs more than one round, also draft the acceptance-criteria comment.
8. List the direction questions separately. Don't decide them in the draft, so the review doesn't need a later "Correction".
9. Stop. Post only after Dev approves the draft.

## Mode 4: finish visuals

When Dev says "finish visuals" after running `mwinit -f`: rerun step 4 of `VISUAL-CHECK.md` for every PR the digest marked "prototype capture needs `mwinit -f`", update each `drafts/<N>/visual.html`, and report which PRs now have both captures.
