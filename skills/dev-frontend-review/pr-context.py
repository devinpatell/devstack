#!/usr/bin/env python3
"""Build the review context bundle an agent needs for one PR.

Prints markdown with: Dev's notes for the PR (notes/prs/<N>.md, any
notes/series/*.md that lists it, notes/decisions.md), prototype and visual
references found in the PR, PR metadata and body, changed files grouped by surface,
an iOS/Android parity hint, other reviewers' current verdicts, every review
and comment you have already left (including any acceptance-criteria
checklist), your unresolved threads, and what changed since your last review.

Usage:
  python3 -I pr-context.py 15078 > /tmp/pr-15078.md
  python3 -I pr-context.py 15078 --me devinpatell

Read-only. Feed the output to the agent together with REVIEW-RUBRIC.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Notes, snapshots and drafts live outside the repo, in DEV_REVIEW_HOME (default ~/dev-review).
HOME = Path(os.environ.get("DEV_REVIEW_HOME", "~/dev-review")).expanduser()
NOTES = HOME / "notes"

QUERY = """
query($n: Int!) { repository(owner: "%(owner)s", name: "%(name)s") { pullRequest(number: $n) {
  number title url state isDraft body createdAt mergeable additions deletions changedFiles
  author { login } baseRefName headRefName
  files(first: 100) { nodes { path additions deletions } }
  latestOpinionatedReviews(first: 30) { nodes { author { login } state submittedAt commit { oid } } }
  reviews(first: 100) { nodes { author { login } state submittedAt body commit { oid } } }
  comments(first: 100) { nodes { author { login } body createdAt } }
  reviewThreads(first: 100) { nodes { isResolved isOutdated path line
    comments(first: 20) { nodes { author { login } body createdAt } } } }
  commits(last: 100) { nodes { commit { oid messageHeadline committedDate } } }
  headCommit: commits(last: 1) { nodes { commit { oid statusCheckRollup { state
    contexts(first: 100) { nodes { ... on CheckRun { name conclusion } ... on StatusContext { context state } } } } } } }
} } }
"""

SURFACES = [
    ("apps/mobile/ios/", "Mobile iOS"),
    ("apps/mobile/android/", "Mobile Android"),
    ("apps/mobile/", "Mobile shared/docs"),
    ("apps/concierge-alpha/service/frontend/", "Web"),
    ("apps/concierge-alpha/ios/", "Frozen iOS app"),
    ("apps/concierge-alpha/android/", "Frozen Android app"),
    ("packages/design-system", "Design system"),
    ("packages/api-schema/", "API schema"),
    (".agents/spec/", "Spec"),
    (".agents/", "Agent rules/skills"),
    ("", "Other"),
]


def gql(repo: str, n: int) -> dict:
    owner, name = repo.split("/")
    out = subprocess.run(["gh", "api", "graphql", "-f", "query=" + QUERY % {"owner": owner, "name": name},
                          "-F", f"n={n}"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"gh failed: {out.stderr.strip()}")
    return json.loads(out.stdout)["data"]["repository"]["pullRequest"]


def compare(repo: str, base: str, head: str) -> list[dict]:
    out = subprocess.run(["gh", "api", f"repos/{repo}/compare/{base}...{head}", "--jq",
                          "[.files[] | {filename, status, additions, deletions}]"], capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else []


def login(x: dict | None) -> str:
    return (x or {}).get("login", "ghost")


def notes_for(n: int) -> list[tuple[str, str]]:
    found = []
    own = NOTES / "prs" / f"{n}.md"
    if own.exists():
        found.append((f"notes/prs/{n}.md", own.read_text()))
    for f in sorted((NOTES / "series").glob("*.md")):
        text = f.read_text()
        first = text.splitlines()[0] if text else ""
        if re.search(rf"#{n}\b", first):
            found.append((f"notes/series/{f.name}", text))
    dec = NOTES / "decisions.md"
    if dec.exists() and re.search(r"^- ", dec.read_text(), re.M):
        found.append(("notes/decisions.md", dec.read_text()))
    return found


URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
PROTO_HOSTS = ("lattice.dxd.amazon.dev", "figma.com")


def visual_refs(body: str, paths: list[str]) -> list[str]:
    refs = []
    urls = sorted(set(URL_RE.findall(body)))
    for u in urls:
        if any(h in u for h in PROTO_HOSTS) or re.search(r"(?i)proto|storybook", u):
            refs.append(f"- Prototype or design link: {u}")
    for m in sorted(set(re.findall(r"Mobile-Metis-Neo-Prototype(?:[ @`]*(?:commit )?`?([0-9a-f]{7,40}))?", body))):
        refs.append(f"- Prototype source: `Mobile-Metis-Neo-Prototype`" + (f" at `{m}`" if m else " (no commit named)"))
    for flag in sorted(set(re.findall(r"(?<![\w-])--(?:ui-testing|[a-z][a-z-]*-fixture[a-z-]*)\b", body))):
        refs.append(f"- iOS launch flag named in the body: `{flag}`")
    stories = [p for p in paths if re.search(r"\.stories\.(tsx?|jsx?|mdx)$", p)]
    for p in stories:
        refs.append(f"- Changed Storybook file: `{p}`")
    images = len(re.findall(r"user-attachments/assets/|\.(?:png|jpe?g|gif)\b", body))
    videos = len(re.findall(r"\.(?:mp4|mov|webm)\b", body))
    refs.append(f"- Media in the PR body: {images} image link(s), {videos} video link(s)")
    if not any(r.startswith(("- Prototype", "- Changed Storybook")) for r in refs):
        refs.insert(0, "- No prototype link or Storybook change found. Ask the author which prototype "
                       "screen this matches before running the visual check, or mark it not applicable.")
    return refs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("number", type=int)
    ap.add_argument("--repo", default="noor-basal/noor")
    ap.add_argument("--me", default="devinpatell")
    a = ap.parse_args()
    pr = gql(a.repo, a.number)
    head = pr["headCommit"]["nodes"][0]["commit"]
    w = sys.stdout.write

    w(f"# PR #{pr['number']}: {pr['title']}\n\n{pr['url']}\n\n")
    w(f"- Author: @{login(pr['author'])} · {pr['state']}{' (draft)' if pr['isDraft'] else ''} · "
      f"{pr['headRefName']} → {pr['baseRefName']} · head `{head['oid'][:9]}`\n")
    w(f"- Size: +{pr['additions']}/-{pr['deletions']} in {pr['changedFiles']} files"
      f"{' (file list truncated at 100)' if pr['changedFiles'] > 100 else ''} · mergeable: {pr['mergeable'].lower()}\n")
    rollup = head["statusCheckRollup"] or {}
    failing = [c.get("name") or c.get("context") for c in (rollup.get("contexts") or {}).get("nodes", [])
               if (c.get("conclusion") or c.get("state")) in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED")]
    w(f"- CI: {rollup.get('state', 'unknown')}{' — failing: ' + ', '.join(failing) if failing else ''}\n")
    verdicts = [f"@{login(r['author'])} {r['state']}{'' if r['commit']['oid'] == head['oid'] else ' (older head)'}"
                for r in pr["latestOpinionatedReviews"]["nodes"]]
    w(f"- Current verdicts: {', '.join(verdicts) or 'none'}\n\n")

    notes = notes_for(pr["number"])
    w(f"## Dev's notes ({len(notes)})\n\n")
    if not notes:
        w("None yet. Direction calls Dev makes about this PR go in `notes/prs/%d.md`.\n\n" % pr["number"])
    for name, text in notes:
        w(f"### {name}\n\n{text.strip()}\n\n")

    w("## Prototype and visual references\n\n")
    w("\n".join(visual_refs(pr["body"] or "", [f["path"] for f in pr["files"]["nodes"]])) + "\n\n")

    groups: dict[str, list[str]] = defaultdict(list)
    for f in pr["files"]["nodes"]:
        label = next(l for prefix, l in SURFACES if f["path"].startswith(prefix))
        groups[label].append(f"`{f['path']}` +{f['additions']}/-{f['deletions']}")
    w("## Files by surface\n\n")
    for _, label in SURFACES:
        if groups[label]:
            w(f"**{label}** ({len(groups[label])})\n" + "".join(f"- {x}\n" for x in groups[label]) + "\n")
    ios, android = bool(groups["Mobile iOS"]), bool(groups["Mobile Android"])
    if ios != android:
        w(f"> Parity hint: only {'iOS' if ios else 'Android'} changed under `apps/mobile`. "
          "Check whether the PR body justifies a single-platform change.\n\n")
    if groups["Frozen iOS app"] or groups["Frozen Android app"]:
        w("> Frozen-app hint: the PR edits `apps/concierge-alpha/{ios,android}`. Only bug fixes belong there.\n\n")

    w("## PR body\n\n" + (pr["body"] or "_empty_").strip() + "\n\n")

    mine = sorted([("review " + r["state"], r["submittedAt"], r["body"], r["commit"]["oid"])
                   for r in pr["reviews"]["nodes"] if login(r["author"]) == a.me and r["body"].strip()]
                  + [("comment", c["createdAt"], c["body"], None)
                     for c in pr["comments"]["nodes"] if login(c["author"]) == a.me], key=lambda x: x[1])
    w(f"## What @{a.me} already said ({len(mine)})\n\n")
    for kind, at, body, oid in mine:
        w(f"### {kind} · {at[:16]}{' · at `' + oid[:9] + '`' if oid else ''}\n\n{body.strip()}\n\n")

    open_threads = [t for t in pr["reviewThreads"]["nodes"] if not t["isResolved"] and t["comments"]["nodes"]]
    w(f"## Unresolved review threads ({len(open_threads)})\n\n")
    for t in open_threads:
        first = t["comments"]["nodes"][0]
        w(f"### `{t['path']}:{t['line']}` · started by @{login(first['author'])}{' · outdated' if t['isOutdated'] else ''}\n\n")
        for c in t["comments"]["nodes"]:
            w(f"- @{login(c['author'])}: {c['body'].strip()[:1200]}\n")
        w("\n")

    others = [c for c in pr["comments"]["nodes"] if login(c["author"]) != a.me]
    if others:
        w(f"## Other discussion ({len(others)}, latest 15, truncated)\n\n")
        for c in others[-15:]:
            w(f"- @{login(c['author'])} {c['createdAt'][:16]}: {c['body'].strip()[:800]}\n")
        w("\n")

    my_reviews = [r for r in pr["reviews"]["nodes"] if login(r["author"]) == a.me and r["commit"]]
    if my_reviews:
        last = max(my_reviews, key=lambda r: r["submittedAt"])
        base = last["commit"]["oid"]
        new = [c["commit"] for c in pr["commits"]["nodes"] if c["commit"]["committedDate"] > last["submittedAt"]]
        w(f"## Since your last review (at `{base[:9]}`, {last['submittedAt'][:16]})\n\n")
        if base == head["oid"]:
            w("No new commits.\n")
        else:
            for c in new:
                w(f"- `{c['oid'][:9]}` {c['messageHeadline']}\n")
            pr_paths = {f["path"] for f in pr["files"]["nodes"]}
            changed = compare(a.repo, base, head["oid"])
            own = [f for f in changed if f["filename"] in pr_paths]
            w(f"\nPR files changed between `{base[:9]}` and `{head['oid'][:9]}`: {len(own)} "
              f"({len(changed) - len(own)} other files came in from merging the base branch and are omitted):\n")
            for f in own[:150]:
                w(f"- {f['status']} `{f['filename']}` +{f['additions']}/-{f['deletions']}\n")
            w(f"\nFull incremental diff: `gh api repos/{a.repo}/compare/{base}...{head['oid']} "
              "-H 'Accept: application/vnd.github.diff'`\n")


if __name__ == "__main__":
    main()
