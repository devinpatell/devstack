---
name: leaving-pr-comments
description: Use whenever leaving comments on GitHub.
---

# Leaving PR comments

Write GitHub messages in the user's voice. Do not add an AI or bot warning,
model attribution, or "responding on behalf of" notice unless the user asks
for one. This applies to PR comments, review bodies, inline review comments,
replies, and PR descriptions.

Before posting, check the entire comment, including quoted text and
attachments, for secrets and private details.

Before posting, also edit the reply against every rule in
the sibling `../unslop/SKILL.md`. Read that file without invoking the skill.
Leave quoted text from others unchanged.

Write the comment itself in a direct style:

- Lead with the conclusion.
- Cite the relevant code, behavior, check, or reproduction.
- Keep it concise and avoid filler, canned thanks, or status narration.
- Distinguish verified facts from judgment.

Preview the final Markdown before posting to check quoting and blank lines.
After posting, verify that GitHub returned the comment or review URL.
Resolve a review thread only after its response was posted successfully.
