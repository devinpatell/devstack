---
name: walkthrough
description: Walk the user through an explanation, plan, question, or change one step at a time, and wait for explicit consent before each next step. Use when the user says "walk me through", "step by step", or "one step at a time".
---

# Walkthrough

Break what you are telling or asking the user into steps. Explain one step at
a time in plain words. Move to the next step only when the user explicitly
says to.

## Start

1. Split the subject into steps. Each step covers one idea or one decision.
   Use as many steps as the subject needs.
2. Order the steps so each one builds on the ones before it. If the order
   does not matter, say so.
3. Show the numbered step titles, one line each, so the user can see the
   whole path. Then present step 1.

## Each step

Write each step for someone new to the topic:

- **What it is.** Explain it in simple terms. Define each term the first time
  you use it, and show a short example or snippet when that is clearer than
  prose.
- **Why it matters.** Say what it affects, or what goes wrong without it.
- **What happens next.** Say what you would do, or what the user has to
  decide, and give your recommendation.

Keep a step short enough to read in a minute. Then end your turn with
"Step <n> of <total>. Ask anything, ask for changes, or say next."

## Between steps

- **Questions.** Answer them, then ask again whether to move on. Reading
  code, docs, or logs to answer a question is fine.
- **Changes.** Revise the step and show the new version. If the change
  affects later steps, update the step list and say what changed.
- **Consent.** Only clear consent moves you forward: "next", "yes", "go
  ahead", "approved", or similar. A question, "ok", "I see", "hmm", or a
  comment is not consent. If you are unsure, ask.

Do not act on a step before consent. That means no edits, commits, pushes,
messages, or other commands with side effects. When the user consents to a
step that includes an action, do that action, report the result in a line
or two, then present the next step.

## End

After the last step, list each step with what the user decided and what you
did. If the user says stop at any point, stop and give the same summary for
the steps covered so far.
