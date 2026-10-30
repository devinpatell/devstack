# Global agent instructions

## Changing skills or these instructions

My skills, hooks, and these instructions come from my dstack repo at `{{dstack}}` (github.com/devinpatell/dstack). When I ask to add or change any of them, edit dstack, commit and push, then run `{{dstack}}/install.sh`. Never edit the installed copies in `~/.claude` or `~/.codex` directly.

## How I work

- Decisions I've made stay made. When a reviewer raises a point I already decided, reply to the reviewer with my decision and move on. Don't ask me again.
- Keep every stage of a feature in the session where it started, even when the next stage needs its own branch. Don't start a new session for it. Subagents for read-only research or review are fine.
- When docs, specs, or PR descriptions disagree with the code, the code is right. Describe current behavior from the code with file:line, and call the docs stale.
- Run one heavy build or test suite at a time. Check free disk space before a build and stop if it is under about 8 GB. Cap parallel build workers. When you finish, shut down the simulators, emulators, and build daemons you started, and delete build folders you created.

## Midway-protected websites

Never open a Midway-protected site (`*.amazon.dev`, `*.amazon.com`, `*.a2z.com`, `*.aws.dev` and other internal hosts) in the agent's browser. That includes T3 preview tabs, the built-in browser and Claude in Chrome. Use the routes below.

A Lattice prototype (`lattice.dxd.amazon.dev/p/<slug>/...`) runs from its source:

1. Find the package that holds the slug. Search `~/workplace` for the URL or the slug first: READMEs, `LOCAL-COPY.md` and `.lattice.json` files name it. Otherwise search code with builder-mcp `InternalCodeSearch` for `"lattice.dxd.amazon.dev/p/<slug>"` and read the matching docs for the package name.
2. If `~/workplace/<Package>` exists, `git pull --ff-only` it. Otherwise `git clone ssh://git.amazon.com/pkg/<Package> ~/workplace/<Package>`.
3. Run it the way its README or `LOCAL-COPY.md` says. A static prototype with no instructions runs with `python3 -m http.server <port> --bind 127.0.0.1` in its folder.
4. Open the localhost URL, with the Lattice URL's hash route, in the agent's browser. Stop the server when you're done.

For any other Midway-protected page, read it with builder-mcp `ReadInternalWebsites`. If that can't read it, use `mcurl`.

If a clone fails or `mcurl` returns 401, my Midway session has expired. Ask me to run `mwinit -f`, wait until I say it has run, then retry. Don't fall back to the browser.

## Write without AI tells

Apply the rules below to all prose you write: chat replies, summaries, plans, commit messages, PR titles and descriptions, review comments, docs, and code comments. They do not apply to code, command output, or text quoted from others. Edit each draft against them before you send it.
