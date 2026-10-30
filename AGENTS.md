# dstack

This repo holds my agent skills and global instructions for Claude Code and Codex. These instructions are for agents working on the repo itself. The global instructions deployed to every laptop are in `global/AGENTS.md`.

## Layout

- `skills/<name>/SKILL.md`: one directory per skill, with any helper files next to it.
- `global/AGENTS.md`: the global instructions, without the unslop rules. `install.sh` replaces `{{dstack}}` with the path to this clone.
- `hooks/`: Claude Code hooks. `install.sh` registers them in `~/.claude/settings.json`.
- `install.sh`: links skills and hooks into `~/.claude` and `~/.codex`, and builds `.generated/AGENTS.md`.
- `licenses/`: MIT notices for skills that came from tstack and pstack. Keep them.

## Rules

- The unslop rules live only in `skills/unslop/SKILL.md`. Never copy them into `global/AGENTS.md`. `install.sh` appends them.
- Never edit `.generated/`. `install.sh` rewrites it on every run.
- Every skill must work in both Claude Code and Codex. Name tools generically ("the question tool") or give both names, and say what to do when a tool is missing.
- Frontmatter needs `name` and a `description` that says when to use the skill.
- When you add, rename, or remove a skill, update the skill table in `README.md`. When a skill comes from another repo, credit it in `README.md` and add its license to `licenses/`.
- After any change, run `./install.sh` and check that the links in `~/.claude` and `~/.codex` point into this repo.
- Keep `install.sh` safe to run again. It must never overwrite a real file without moving it aside first.
