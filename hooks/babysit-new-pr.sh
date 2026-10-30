#!/bin/bash
# PostToolUse hook (Bash): after `gh pr create` succeeds, tell Claude to babysit the new PR.
input=$(cat)
cmd=$(jq -r '.tool_input.command // ""' <<<"$input")
grep -qE '(^|[^[:alnum:]_-])gh[[:space:]]+pr[[:space:]]+create([[:space:]]|$)' <<<"$cmd" || exit 0

out=$(jq -r '.tool_response | if type == "object" then ((.stdout // "") + "\n" + (.stderr // "")) else tostring end' <<<"$input")
url=$(grep -oE 'https://github\.com/[^/[:space:]]+/[^/[:space:]]+/pull/[0-9]+' <<<"$out" | tail -1)
[ -n "$url" ] || exit 0

jq -n --arg url "$url" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: ("A new pull request was created: " + $url + ". The user wants every new PR babysat. After you link it and finish any other work, use the babysit-pr skill on it: fix CI failures on your own, triage review feedback without acting on it until the user approves in writing, and never merge unless asked. If you are a delegated child task, skip this and leave the PR to the parent thread.")
  }
}'
