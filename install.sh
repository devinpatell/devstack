#!/bin/bash
# Link dstack into Claude Code and Codex. Safe to run again.
set -euo pipefail
repo="$(cd "$(dirname "$0")" && pwd)"

# link <source> <dest>: moves a real file or directory at <dest> aside first.
link() {
  if [ -e "$2" ] && [ ! -L "$2" ]; then mv "$2" "$2.bak.$(date +%s)"; fi
  mkdir -p "$(dirname "$2")"
  ln -sfn "$1" "$2"
}

for dir in "$repo"/skills/*/; do
  name=$(basename "$dir")
  link "$repo/skills/$name" ~/.claude/skills/"$name"
  link "$repo/skills/$name" ~/.codex/skills/"$name"
done
# Global instructions: AGENTS.md plus the unslop rules, so the rules live only in the skill.
mkdir -p "$repo/.generated"
{ cat "$repo/AGENTS.md"; echo; sed -n '/^## Patterns to detect and fix/,$p' "$repo/skills/unslop/SKILL.md"; } > "$repo/.generated/AGENTS.md"
link "$repo/.generated/AGENTS.md" ~/.claude/CLAUDE.md
link "$repo/.generated/AGENTS.md" ~/.codex/AGENTS.md
link "$repo/hooks/babysit-new-pr.sh" ~/.claude/hooks/babysit-new-pr.sh

# Register the new-PR hook in Claude Code settings if it is missing.
settings=~/.claude/settings.json
[ -f "$settings" ] || echo '{}' > "$settings"
if ! grep -q babysit-new-pr.sh "$settings"; then
  tmp=$(mktemp)
  jq '.hooks.PostToolUse += [{"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/babysit-new-pr.sh", "timeout": 10}]}]' "$settings" > "$tmp"
  mv "$tmp" "$settings"
fi

echo "dstack linked from $repo"
