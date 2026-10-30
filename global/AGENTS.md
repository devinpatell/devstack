# Global agent instructions

## Changing skills or these instructions

My skills, hooks, and these instructions come from my dstack repo at `{{dstack}}` (github.com/devinpatell/dstack). When I ask to add or change any of them, edit dstack, commit and push, then run `{{dstack}}/install.sh`. Never edit the installed copies in `~/.claude` or `~/.codex` directly.

## How I work

- Decisions I've made stay made. When a reviewer raises a point I already decided, reply to the reviewer with my decision and move on. Don't ask me again.
- Keep every stage of a feature in the session where it started, even when the next stage needs its own branch. Don't start a new session for it. Subagents for read-only research or review are fine.
- When docs, specs, or PR descriptions disagree with the code, the code is right. Describe current behavior from the code with file:line, and call the docs stale.
- Run one heavy build or test suite at a time. Check free disk space before a build and stop if it is under about 8 GB. Cap parallel build workers. When you finish, shut down the simulators, emulators, and build daemons you started, and delete build folders you created.

## Write without AI tells

Apply the rules below to all prose you write: chat replies, summaries, plans, commit messages, PR titles and descriptions, review comments, docs, and code comments. They do not apply to code, command output, or text quoted from others. Edit each draft against them before you send it.
