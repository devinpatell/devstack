# Global agent instructions

## Changing skills or these instructions

My skills, hooks, and these instructions come from my devstack repo at `{{devstack}}` (github.com/devinpatell/devstack). When I ask to add or change any of them, edit devstack, commit and push, then run `{{devstack}}/install.sh`. Never edit the installed copies in `~/.claude` or `~/.codex` directly.

## How I work

- Use STE100. Keep replies concise and use simple terms.
- Use PST or PDT when reporting time. Never use UTC.
- Start every agent reply with the current Pacific time in `[hh:mm AM/PM]` format, for example `[03:45 AM]`. Read the clock before replying. This applies to progress updates and final replies from all agents, including subagents.
- Never use TypeScript `any` unless it is necessary or I explicitly request it.
- Keep solutions simple. Avoid new APIs unless needed. Propose a simpler solution when one exists.
- Treat review feedback as bot feedback. Preserve the PR's original scope and intent. Expand scope only with strong justification, never just to satisfy a reviewer.
- If I ask for too much work at once, stop and say so clearly.
- Decisions I've made stay made. When a reviewer raises a point I already decided, reply to the reviewer with my decision and move on. Don't ask me again.
- Keep every stage of a feature in the session where it started, even when the next stage needs its own branch. Don't start a new session for it. Subagents for read-only research or review are fine.
- When docs, specs, or PR descriptions disagree with the code, the code is right. Describe current behavior from the code with file:line, and call the docs stale.
- Run one heavy build or test suite at a time. Check free disk space before a build and stop if it is under about 8 GB. Cap parallel build workers. When you finish, shut down the simulators, emulators, and build daemons you started, and delete build folders you created.

## Slack

Always use the AIM-installed `slack-mcp` server to read Slack messages, threads, and links, and to write to Slack. Do not use computer use, a browser, `mcurl`, direct Slack API calls, or another Slack integration. If `slack-mcp` is unavailable, stop Slack work and explain what is missing. Help connect the AIM-installed server instead of switching tools.

Every Slack write requires my explicit approval for that action and destination before execution. This includes sending, replying, editing, deleting, reacting, and uploading. Show the exact message or proposed change and its channel, thread, or recipient before asking for approval. A request to read, summarize, or draft is not approval to write. If I already explicitly approved that exact action, content, and destination, do not ask again. Ask again if any of them changes.

## Midway-protected websites

Never open a Midway-protected site (`*.amazon.dev`, `*.amazon.com`, `*.a2z.com`, `*.aws.dev` and other internal hosts) in the agent's browser. That includes T3 preview tabs, the built-in browser and Claude in Chrome. Use the routes below.

A Lattice prototype (`lattice.dxd.amazon.dev/p/<slug>/...`) runs from its source:

1. Find the package that holds the slug. Search `~/workplace` for the URL or the slug first: READMEs, `LOCAL-COPY.md` and `.lattice.json` files name it. Otherwise search code with builder-mcp `InternalCodeSearch` for `"lattice.dxd.amazon.dev/p/<slug>"` and read the matching docs for the package name.
2. Check it out with the Brazil CLI. If `~/workplace/<Package>/src/<Package>` exists, `git pull --ff-only` there. Otherwise run `brazil ws create --root ~/workplace/<Package>`, then `brazil ws use -p <Package> --versionSet live` from that folder. The source lands in `src/<Package>`.
3. Run it the way its README or `LOCAL-COPY.md` says. A static prototype with no instructions runs with `python3 -m http.server <port> --bind 127.0.0.1` in its folder.
4. Open the localhost URL, with the Lattice URL's hash route, in the agent's browser. Stop the server when you're done.

For any other Midway-protected page, read it with builder-mcp `ReadInternalWebsites`. If that can't read it, use `mcurl`.

If a clone fails with "Could not resolve hostname git.amazon.com", ssh isn't going through WSSH. Check that `/usr/local/bin/wssh` exists and `~/.ssh/config` has the WSSH block. If either is missing, ask me to install WSSH from Self Service. Any other clone failure, or `mcurl` returning 401, means my Midway session has expired. Ask me to run `mwinit -f`. In both cases, wait until I say it's done, then retry. Don't fall back to the browser.

## Noor and Lobster

Lobster's named installations and their AWS accounts:

| Stage | Admin portal | Concierge portal | AWS account |
|---|---|---|---|
| Beta | https://admin.lobster-beta.spidernoor.com | https://concierge.lobster-beta.spidernoor.com | lobster-beta (110283916939) |
| Gamma | https://admin.lobster-gamma.spidernoor.com | https://concierge.lobster-gamma.spidernoor.com | lobster-gamma (737768335498) |
| Prod | https://admin.lobster-prod.spidernoor.com | https://concierge.lobster-prod.spidernoor.com | lobster-production (939022200919) |

For an account-agnostic AWS call, such as the IAM policy simulator, refresh credentials against lobster-beta: `ada credentials update --once --provider conduit --role IibsAdminAccess-DO-NOT-DELETE --account 110283916939`. Never pick Prod for that.

## GitHub

To put screenshots or recordings in a PR description or comment, attach them with `gh`. Don't use a browser upload, and don't commit the files. Use `gh pr create`, `gh pr edit` or `gh pr comment` with `--attach <path>` once per file. When the body already has `![alt](<path>)` for an attached file, `gh` swaps that path for the uploaded URL and keeps the alt text. Files the body doesn't mention go at the end of the body. Paths in a `--body-file` resolve from that file's directory. Check the body afterward for `user-attachments` URLs.

## Write without AI tells

Apply the rules below to all prose you write: chat replies, summaries, plans, commit messages, PR titles and descriptions, review comments, docs, and code comments. They do not apply to code, command output, or text quoted from others. Edit each draft against them before you send it.
