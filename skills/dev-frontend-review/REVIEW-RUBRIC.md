# How Dev reviews frontend PRs

The standing rules @devinpatell applies to PRs under `apps/mobile`, the Noor web client
(`apps/concierge-alpha/service/frontend`), `packages/design-system*` and the frozen
`apps/concierge-alpha/{ios,android}` apps. Extracted from his reviews on the
frontend PRs merged between 2026-10-01 and 2026-10-30.

Use it two ways: an agent drafts a review against it, and an author can check a PR
against it before asking for review. Each rule names a PR where Dev applied it.

## 1. Scope and direction come first

- **The ADRs decide where code goes.** New client behaviour goes in `apps/mobile` and
  Noor web, never in the frozen `apps/concierge-alpha/{ios,android}` apps; only bug fixes
  land there (#12812). One Noor backend, no runtime backend switch; a feature Noor can't
  serve yet sits behind an off-by-default developer-options flag (#12822).
- **Reuse before building.** A second implementation of something that exists is
  blocking: reuse the existing Card Studio deck and topic card instead of a new Studio
  (#14263); bring over the old app's environment picker instead of inventing one (#13509).
- **Don't change shared production components for one feature.** Build new chrome inside
  the feature's own folder; `ui/Button`, `ui/Chip`, `ui/LoadingDots` ship everywhere
  (Storybook series, #16006).
- **One concern per PR.** Unrelated changes are split out with the bug they fix named
  (Settings admission gate in #14111). Shared changes land once, in one PR, and siblings
  rebase onto it (`useSpringVar`, `preview.ts` in the Storybook series).
- **Product decisions are stated, not left to the author.** When Dev changes direction he
  says so plainly ("Change of direction", "there is no Activity on web") and the review
  is regraded against the new decision (#12702, #13974).

## 2. iOS and Android change together

- Same states, copy, flow and timings on both apps; only visual styling may differ
  (`.agents/rules/ux-parity.md`). He diffs strings, chevrons, badges, headings and
  disabled styling across the two apps (#15078, #14031, #12822).
- One table of exact strings, states and timings goes in the design, implemented on both
  (#12822).
- A single-platform PR needs a stated reason in the body; "follow-up" for the other
  platform does not pass when parity is in scope (#14263 OC-10).

## 3. Removal means deletion

- Retiring a feature deletes its code, models, tests, docs, config keys, entitlements,
  build targets, dependencies and debug/preview screens in the same PR (#12702, #12886,
  #12915, #12991).
- These count as code to delete: anything behind a constant `false`, code only reachable
  from a test, an adapter that rejects calls nobody makes, a model kept so old data stays
  readable, an "unavailable" placeholder screen.
- **Done check:** `git grep` for the retired names under `apps/mobile` returns nothing but
  the minimal compatibility filter, and the PR lists each kept hit with its reason.

## 4. Don't ship code nothing uses

- Add code in the PR that uses it, with tests. Unused hooks, generated types, props,
  HTTP tooling and helpers come out (refresh hooks in #12822, `triggerProps` in #16006,
  replay tooling in #12911, `NativeOfflineInteractionGate` in #13222).
- Remove conditions that can no longer be false (`chatLocked` in #13222).

## 5. Legacy local data isn't worth new code

- No migration, recovery, startup scans or erasure plumbing for files a retired feature
  left on the device. If an old record would break startup, drop it on read with the
  smallest filter (#12886, #12915, #14111).
- Keep compatibility only when a user would otherwise be stuck (a saved onboarding step
  id that no longer exists, #12886).

## 6. Design system and tokens

- Bind to the Lobster role when one matches; round a size between two roles to the
  nearest role (ties go larger for icons, one step down for type, as agreed on the card
  chrome) (#13297, #13974).
- Use a value Lobster already publishes instead of recreating it (the 50 % scrim, the
  2 px focus stroke) (#13974).
- A literal stays only if it is a kind the exception record already lists, with its
  `frontend.md` row. Motion endpoints are named constants in the component's motion
  module. Don't sum roles to hit a number; use the literal with a row (#16006).
- No per-instance `<style>` elements; use Tailwind variants (#15494).
- Don't invent a treatment design didn't make (dark mode in #15494); contrast failures go
  back to design rather than being corrected at runtime.
- Motion matches the prototype source: named curves, durations within ±10 %, springs from
  generated `NeoMotion` tokens, Reduce Motion snaps to the end state (#14263 OC-4–OC-10).
  Dev verifies by recording both at 120 Hz and comparing frame by frame (#16006).

## 7. Correctness he checks by hand

- Ownership and stale callbacks: a new callback identity is not a new owner; read latest
  callbacks from a ref (#15494). Re-check the current account after an await before acting
  (#14031).
- Errors are never swallowed: no `catch { }` around a create; show the fixed user message
  and keep it on screen (#14031).
- Failure states always have an exit (Sign out) and a support message, the same on both
  apps (#14031).
- Retry rules are explicit: create only when nothing exists; teardown states stay
  read-only (#14031).
- A required check that fails on this head is a blocker, with the job and log named
  (#13522). Instrumented tests that aren't in CI still have to pass (#13222).
- Tests use the real production component, not a test-only branch in production code
  (the file-backed journal in #15078).
- Tests are not flaky: no fixed sleeps, real clocks, shared state, real network in unit
  tests or fragile selectors; no retries or skips to get green. New or changed tests pass
  on repeated runs (20 for unit/component, 5 for UI journeys).

## 8. Security he won't defer

- Redirect and callback trust: scope App Links / associated domains to the right build,
  no committed signing keys, PKCE or code binding before a redirect is trusted (#12822).
- Keep allowlists; removing one is a decision for its owners, not a PR side effect
  (S3 bucket allowlist in #14111).
- Credential types are redacted from logs and `description` (#12822).
- Legal text, the Privacy Policy and font licensing need their owner's sign-off recorded
  in the PR (#13297, #13974).

## 9. Repository hygiene

- `AGENTS.md` keeps only facts an agent needs before editing; reference detail goes in the
  sibling README (`.agents/rules/content-organization.md`) (#12822, #12911, #15494).
- No working notes, run reports, review scores, plans or demo media in the repo.
  Screenshots and videos go in the PR body as uploads (#12911, #14111, #15494, #13509).
- Specs and docs describe current behaviour only: no review-round history, approval
  narration, "owner requested", or "PENDING" (#15078, #12915). A bug fix doesn't need a
  spec (#13222). Spec status matches reality (#12822).
- Don't edit `governance/` from a component PR (#16006).
- No self-expiring notes in always-loaded files (#12679).

## 10. The PR body

- Says what changed and what was run, on which head. No review-round history or approval
  disclaimers.
- UI PRs carry screenshots or a recording from **both** iOS and Android covering the
  states he lists (#14111, #15078), taken from the real screen, not a test harness.
- Android and iOS builds/tests actually run before asking for review; "deferred" or
  "toolchain unavailable" isn't accepted (#14111).

## How a Dev review is shaped

1. One line: verdict and what's good, specifically ("The session code is careful: …").
2. **Done since my last review:** the items that landed, so the author sees progress.
3. **Blocking**, numbered, each with `file:line`, what's wrong, and the exact fix
   (suggestion blocks inline where a line-level fix exists).
4. **Optional / non-blocking**, clearly labelled, "fine in this PR or a follow-up".
5. On a PR expected to take more than one round, a separate **Acceptance criteria**
   comment: "Done means" checklist plus "General rules I review against". Once posted,
   he grades against it and doesn't add new asks ("I'll approve without adding new asks").
6. Coordination notes when sibling PRs touch the same files.
7. Approval restates what was verified and lists any before-merge items.

Tone: direct, specific, polite ("Thanks"), no hedging. Bot ("council") findings are
labelled as such and verified before being repeated ("This is the council's finding; I
haven't verified it myself").
