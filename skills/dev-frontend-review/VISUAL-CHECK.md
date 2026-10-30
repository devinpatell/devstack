# Visual check: the PR's branch next to its prototype

Dev reviews UI PRs by running the branch and comparing it with the prototype the PR follows.
This file is how the agent does that before Dev looks. The output goes into the review draft. Nothing here gets posted.
`notes/` and `drafts/` paths are in `~/dev-review`.

## When to run it

For a PR whose changed files include UI: `apps/mobile/{ios,android}` views, web components, `*.stories.*`, or design-system tokens and views.
Skip it for logic-only, CI, release, docs and generated-code PRs, and say "visual check: not applicable (no UI change)" in the draft.

## 1. Find what to compare

`pr-context.py` lists the prototype and visual references it found. Resolve each one:

- A Lattice URL: find its package in `notes/prototypes.md` (step 4).
- A prototype named without a URL (for example "the Lattice prototype with `?filterBar=2`", or "`Mobile-Metis-Neo-Prototype` at `970cb92`"): look it up in `notes/prototypes.md`.
- A changed `*.stories.*` file: the story is the web screen to capture.
- An iOS launch flag in the body (`--ui-testing --one-chat-navigation-fixture`): launch the app with it.

The screens to capture are the ones the PR body's screenshots show, or the ones its changed views render.
If you can't tell which prototype screen or app screen the PR changes, don't guess. Add it to the digest's direction questions as "which prototype screen does #N match, and how do I reach it in the app?", and save Dev's answer in `notes/prs/<N>.md`.

## 2. Build the branch

Use a scratch worktree, never Dev's checkout: `git fetch origin pull/<N>/head:pr-<N> && git worktree add /tmp/pr-<N> pr-<N>`.
Build only the clients the PR changes, with the commands from each client's `AGENTS.md`:

- Web Storybook: from `apps/concierge-alpha/service/frontend`, run `npm ci`, then `npx storybook dev -p <free port> --host 127.0.0.1` (`npm run storybook` is fixed to port 6006, which another run may hold).
- Web app: `npm run dev` with the local stack (the `noor-local-dev` skill) only when the screen needs the backend. Otherwise use Storybook.
- iOS: `apps/mobile/ios/AGENTS.md` § Setup and its README § Launch flags. Use `DEVELOPER_DIR=/Applications/Xcode-27.0.0.app/Contents/Developer` with `env -u SDKROOT`, and build for the simulator.
- Android: `./gradlew :app:assembleEnterpriseDebug` from `apps/mobile/android`.

A failed build is a finding. Put the command and the last 30 lines of its output in the draft.

## 3. Capture the app

- iOS and Android: open the device with the T3 device tools (`device_list`, then `device_open` on the simulator or the `noor_api36` emulator), install the build and launch it with the commands `device_open` returns. Take a screenshot of each screen. For a motion change, record a video of it.
- Web: open Storybook in a preview tab at the prototype's viewport size and save a snapshot of each story.

If the device or preview tools aren't available (for example in Codex outside T3), skip the capture and write "visual check: no device tools in this session" in the draft.
Use the same device size for every capture of a screen: iPhone 17 Pro for iOS, the `noor_api36` emulator for Android, and the prototype's frame size for web.
Capture light and dark appearance, and Reduce Motion, only when the PR changes them.

## 4. Capture the prototype

Never open Lattice in the browser. Run the prototype from its source, as the global "Midway-protected websites" rule says:

1. Find the package for the Lattice slug in `notes/prototypes.md`. If it isn't there, find it the way the global rule says and add it.
2. Check it out with the Brazil CLI into `~/workplace/<Package>`, as the global rule says. The source is in `~/workplace/<Package>/src/<Package>`.
3. If the PR names a prototype commit, check that commit out in a scratch worktree of the package (`git -C ~/workplace/<Package>/src/<Package> worktree add /tmp/proto-<N> <commit>`). Otherwise use mainline, and say in the draft that the prototype may have moved on since the PR was built.
4. Serve it on a free localhost port the way its README or `LOCAL-COPY.md` says.
5. Open the localhost URL, with the Lattice URL's hash route, in a preview tab at the same viewport size, and save a snapshot of the matching screen.

If the clone or pull fails, Midway has expired. In a scheduled run, mark the PR "prototype capture needs `mwinit -f`" in the digest and carry on with the next PR. In a live session, ask Dev to run `mwinit -f`, wait until he says it has run, then retry.
Stop the server, remove the worktree and close every tab you opened.

## 5. Compare and report

Put the captures side by side, prototype on the left and the branch on the right, in `~/dev-review/drafts/<N>/visual.html`. Link it from the draft.
List each difference you can see. For each one, give the screen, what the prototype shows, what the branch shows, and whether a rubric rule or the PR's own claim covers it.
Look in particular at:
- spacing, size and radius, compared against the Lobster roles (rubric § 6);
- copy, and the differences between the iOS and Android captures (rubric § 2);
- states the prototype shows that the branch doesn't (empty, loading, error, disabled);
- motion: the duration and the end state. Frame-by-frame motion timing is Dev's own check, so say "motion recorded, not timed" and leave the timing to him.

Mark every difference "seen in capture". Never present a difference as verified against code you haven't read.

## 6. Clean up

Shut down the simulators you started, stop Storybook and dev servers, close the preview tabs and remove the worktree (`git worktree remove /tmp/pr-<N>`).
