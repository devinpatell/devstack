# dstack

My agent skills and global instructions for Claude Code and Codex.

## Skills

| Skill | Say | What it does |
|---|---|---|
| `babysit-pr` | "babysit" (or automatic after `gh pr create`) | Watches a PR. Fixes CI and keeps the branch current on its own. Triages review feedback but acts only on written approval. Asks about auto-merge once, and reports when the PR is ready to merge. |
| `better-call-sol` | "better call sol" | Reviews a change with GPT Sol in a loop until both agents agree. |
| `leaving-pr-comments` | (automatic) | Formats and unslops comments posted on my behalf. |
| `walkthrough` | "walk me through", "step by step" | Explains anything one step at a time in plain words, and waits for my explicit consent before each next step. |
| `unslop` | `/unslop` | Removes AI writing patterns from text. |

`global/AGENTS.md` holds the global instructions that go to every laptop. `install.sh` appends the rules from `skills/unslop/SKILL.md` to it and writes the result to `.generated/AGENTS.md`, so both tools apply unslop to every reply. Edit the rules only in the skill.

`hooks/babysit-new-pr.sh` is a Claude Code hook. After `gh pr create` succeeds, it tells Claude to run `babysit-pr` on the new PR. Codex has no equivalent.

The root `AGENTS.md` (loaded by `CLAUDE.md`) holds the instructions for agents working on this repo.

## Install

```bash
gh repo clone devinpatell/dstack ~/workplace/dstack
~/workplace/dstack/install.sh
```

The script symlinks each skill into `~/.claude/skills` and `~/.codex/skills`, links the generated `AGENTS.md` to `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md`, and registers the hook in `~/.claude/settings.json`. If a real file is already at one of those paths, the script renames it to `*.bak.<time>` first.

Skill edits take effect right away, because the installed files are links. Run `install.sh` again after adding a skill or changing `global/AGENTS.md` or the unslop rules. To sync another machine, run `git pull`, then `install.sh`.

## Requirements

- An authenticated `gh` and `jq`.
- `python3` for `babysit-pr`'s `pr-wait` script.

## Credits

`babysit-pr`, `leaving-pr-comments`, and `better-call-sol` (from `sol-loop`) started from [tstack](https://github.com/t3dotgg/tstack) at commit `1085050` by Theo Browne. `unslop` is from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan. Both are MIT licensed. See `licenses/`.
