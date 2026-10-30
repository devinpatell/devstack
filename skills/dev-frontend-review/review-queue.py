#!/usr/bin/env python3
"""Frontend review queue for a code owner.

Lists open PRs that touch the frontend surfaces and says, for each one, whose
move it is: yours (first review, or new commits since your last review),
the author's (your review is current), a co-owner's, or nobody's (drafts,
generated-only or frozen-app-only changes).

Usage:
  python3 -I review-queue.py                  # markdown to stdout
  python3 -I review-queue.py --json           # machine-readable, for an agent
  python3 -I review-queue.py --me devinpatell --co chanhe-amzn,tjfazio
  python3 -I review-queue.py --since-last     # also save a snapshot and list what
                                              # changed since the previous one

Needs an authenticated `gh`. Read-only: it never posts or changes anything.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FE_PATHS = (
    "apps/mobile/",
    "apps/concierge-alpha/service/frontend/",
    "apps/concierge-alpha/ios/",
    "apps/concierge-alpha/android/",
    "packages/design-system/",
    "packages/design-system-tokens/",
    "packages/design-tokens/",
    ".agents/rules/mobile",
    ".agents/rules/frontend.md",
)
FROZEN = ("apps/concierge-alpha/ios/", "apps/concierge-alpha/android/")
GENERATED_MARKERS = ("/generated/", "/Generated/", ".gen.")

QUERY = """
query($endCursor: String) {
  repository(owner: "%(owner)s", name: "%(name)s") {
    pullRequests(states: OPEN, first: 40, after: $endCursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url isDraft reviewDecision createdAt updatedAt mergeable additions deletions changedFiles
        author { login }
        files(first: 100) { nodes { path } }
        reviewRequests(first: 20) { nodes { requestedReviewer { ... on User { login } ... on Team { slug } } } }
        latestOpinionatedReviews(first: 20) { nodes { author { login } state submittedAt commit { oid } } }
        reviewThreads(first: 100) { nodes { isResolved comments(first: 1) { nodes { author { login } } } } }
        timelineItems(last: 1, itemTypes: [READY_FOR_REVIEW_EVENT]) { nodes { ... on ReadyForReviewEvent { createdAt } } }
        commits(last: 1) { nodes { commit { oid committedDate statusCheckRollup { state } } } }
      }
    }
  }
}
"""

BUCKETS = [
    ("mine", "Your PRs"),
    ("first", "Needs your first review"),
    ("repush", "New commits since your last review"),
    ("approved", "You approved; waiting on merge or other gates"),
    ("author", "Waiting on the author"),
    ("coowner", "A co-owner already approved (you are optional)"),
    ("noise", "Generated or frozen-app files only (rubber-stamp or reassign)"),
    ("draft", "Drafts"),
]


def gh_pages(repo: str) -> list[dict]:
    owner, name = repo.split("/")
    cmd = ["gh", "api", "graphql", "--paginate", "-f", "query=" + QUERY % {"owner": owner, "name": name},
           "--jq", ".data.repository.pullRequests.nodes[]"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"gh failed: {out.stderr.strip()}")
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def days(iso: str, now: datetime) -> float:
    return (now - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() / 86400


def classify(pr: dict, me: str, co: set[str]) -> dict | None:
    paths = [f["path"] for f in pr["files"]["nodes"]]
    fe = [p for p in paths if p.startswith(FE_PATHS)]
    if not fe:
        return None
    is_mine = (pr["author"] or {}).get("login") == me
    reviews = {r["author"]["login"]: r for r in pr["latestOpinionatedReviews"]["nodes"] if r["author"]}
    mine = reviews.get(me)
    head = pr["commits"]["nodes"][0]["commit"]
    requested = {(n["requestedReviewer"] or {}).get("login") for n in pr["reviewRequests"]["nodes"]}
    my_open_threads = sum(
        1 for t in pr["reviewThreads"]["nodes"]
        if not t["isResolved"] and t["comments"]["nodes"] and (t["comments"]["nodes"][0]["author"] or {}).get("login") == me
    )
    co_approved = sorted(l for l, r in reviews.items() if l in co and r["state"] == "APPROVED")
    only_noise = all(p.startswith(FROZEN) or any(m in p for m in GENERATED_MARKERS) for p in fe)

    if is_mine:
        bucket = "mine"
    elif pr["isDraft"]:
        bucket = "draft"
    elif mine and mine["state"] == "APPROVED" and mine["commit"]["oid"] == head["oid"]:
        bucket = "approved"
    elif mine and mine["commit"]["oid"] != head["oid"]:
        bucket = "repush"
    elif mine:
        bucket = "author"
    elif co_approved:
        bucket = "coowner"
    elif only_noise:
        bucket = "noise"
    else:
        bucket = "first"

    platforms = sorted({
        "mobile-ios" if p.startswith("apps/mobile/ios/") else
        "mobile-android" if p.startswith("apps/mobile/android/") else
        "web" if p.startswith("apps/concierge-alpha/service/frontend/") else
        "frozen" if p.startswith(FROZEN) else
        "design-system" if p.startswith("packages/design") else
        "rules" if p.startswith(".agents/") else
        "mobile-shared"
        for p in fe
    })
    parity_flag = ("mobile-ios" in platforms) != ("mobile-android" in platforms)
    ready = (pr["timelineItems"]["nodes"] or [{}])[0].get("createdAt") or pr["createdAt"]
    return {
        "bucket": bucket,
        "number": pr["number"],
        "title": pr["title"],
        "url": pr["url"],
        "author": pr["author"]["login"],
        "ready_at": ready,
        "updated_at": pr["updatedAt"],
        "head": head["oid"][:9],
        "head_committed_at": head["committedDate"],
        "my_state": mine["state"] if mine else None,
        "my_review_at": mine["submittedAt"] if mine else None,
        "my_open_threads": my_open_threads,
        "requested_me": me in requested,
        "co_owner_approved": co_approved,
        "review_decision": pr.get("reviewDecision"),
        "changes_requested_by": sorted(l for l, r in reviews.items() if r["state"] == "CHANGES_REQUESTED"),
        "approved_by": sorted(l for l, r in reviews.items()
                              if r["state"] == "APPROVED" and r["commit"]["oid"] == head["oid"]),
        "waiting_on": sorted(x for x in requested if x),
        "ci": (head["statusCheckRollup"] or {}).get("state"),
        "mergeable": pr["mergeable"],
        "lines": pr["additions"] + pr["deletions"],
        "files": pr["changedFiles"],
        "files_truncated": pr["changedFiles"] > 100,
        "platforms": platforms,
        "single_mobile_platform": parity_flag,
    }


def render(rows: list[dict], now: datetime) -> str:
    out = [f"# Frontend review queue — {now:%Y-%m-%d %H:%M} UTC", ""]
    counts = {b: sum(r["bucket"] == b for r in rows) for b, _ in BUCKETS}
    out.append(" · ".join(f"**{label}**: {counts[b]}" for b, label in BUCKETS if counts[b]))
    for b, label in BUCKETS:
        group = [r for r in rows if r["bucket"] == b]
        if not group:
            continue
        group.sort(key=lambda r: r["ready_at"])
        out += ["", f"## {label} ({len(group)})", "",
                "| PR | Author | Waiting | Size | CI | Merge | Platforms | Notes |",
                "|---|---|---|---|---|---|---|---|"]
        for r in group:
            since = r["head_committed_at"] if b == "repush" else r["ready_at"]
            notes = []
            if r["my_open_threads"]:
                notes.append(f"{r['my_open_threads']} of your threads open")
            if r["single_mobile_platform"]:
                notes.append("one mobile platform only")
            if r["co_owner_approved"]:
                notes.append("approved by " + ", ".join(r["co_owner_approved"]))
            if b == "mine":
                if r["changes_requested_by"]:
                    notes.append("changes requested by " + ", ".join(r["changes_requested_by"]))
                if r["approved_by"]:
                    notes.append("approved on head by " + ", ".join(r["approved_by"]))
                if r["waiting_on"]:
                    notes.append("waiting on " + ", ".join(r["waiting_on"]))
            if r["lines"] > 3000:
                notes.append("large")
            out.append(
                f"| [#{r['number']}]({r['url']}) {r['title'][:60]} | {r['author']} | {days(since, now):.1f}d "
                f"| +/-{r['lines']} | {r['ci'] or '-'} | {r['mergeable'].lower()} | {', '.join(r['platforms'])} "
                f"| {'; '.join(notes)} |"
            )
    return "\n".join(out) + "\n"


LABELS = dict(BUCKETS)


def diff_since(rows: list[dict], state_dir: Path, repo: str, now: datetime) -> str:
    """Save today's snapshot and describe what moved since the previous one."""
    state_dir.mkdir(parents=True, exist_ok=True)
    snaps = sorted(state_dir.glob("queue-*.json"))
    stamp = now.strftime("%Y%m%dT%H%M")
    (state_dir / f"queue-{stamp}.json").write_text(json.dumps(rows, indent=1))
    for old in snaps[:-30]:
        old.unlink()
    if not snaps:
        return "## Changed since last run\n\nNo earlier snapshot; this run is the baseline.\n"
    prev = {r["number"]: r for r in json.loads(snaps[-1].read_text())}
    cur = {r["number"]: r for r in rows}
    since = snaps[-1].stem.removeprefix("queue-")
    out = [f"## Changed since last run ({since[:4]}-{since[4:6]}-{since[6:8]} {since[9:11]}:{since[11:]} UTC)", ""]
    for n in sorted(cur.keys() - prev.keys()):
        r = cur[n]
        out.append(f"- New: [#{n}]({r['url']}) {r['title'][:70]} by {r['author']} ({LABELS[r['bucket']]})")
    for n in sorted(cur.keys() & prev.keys()):
        a, b = prev[n], cur[n]
        moves = []
        if a["bucket"] != b["bucket"]:
            moves.append(f"{LABELS[a['bucket']]} → {LABELS[b['bucket']]}")
        if a["head"] != b["head"]:
            moves.append(f"new commits ({a['head']} → {b['head']})")
        if a.get("ci") != b.get("ci") and b.get("ci") in ("FAILURE", "ERROR", "SUCCESS"):
            moves.append(f"CI {a.get('ci') or '-'} → {b['ci']}")
        for who in sorted(set(b.get("co_owner_approved", [])) - set(a.get("co_owner_approved", []))):
            moves.append(f"approved by {who}")
        if moves:
            out.append(f"- [#{n}]({b['url']}) {b['title'][:60]}: " + "; ".join(moves))
    for n in sorted(prev.keys() - cur.keys()):
        r = prev[n]
        st = subprocess.run(["gh", "pr", "view", str(n), "--repo", repo, "--json", "state", "--jq", ".state"],
                            capture_output=True, text=True).stdout.strip().lower() or "gone"
        out.append(f"- {st.capitalize()}: [#{n}]({r['url']}) {r['title'][:70]}")
    if len(out) == 2:
        out.append("Nothing moved.")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default="noor-basal/noor")
    ap.add_argument("--me", default="devinpatell")
    ap.add_argument("--co", default="chanhe-amzn,tjfazio", help="comma-separated co-owners")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--since-last", action="store_true",
                    help="save a snapshot in --state-dir and print what changed since the previous one")
    ap.add_argument("--state-dir", type=Path, default=Path(os.environ.get("DEV_REVIEW_HOME", "~/dev-review")).expanduser() / "state")
    args = ap.parse_args()
    now = datetime.now(timezone.utc)
    co = set(filter(None, args.co.split(",")))
    rows = [r for pr in gh_pages(args.repo) if (r := classify(pr, args.me, co))]
    changes = diff_since(rows, args.state_dir, args.repo, now) if args.since_last else ""
    if args.json:
        json.dump(rows, sys.stdout, indent=1)
    else:
        text = render(rows, now)
        if changes:
            head, _, rest = text.partition("\n\n")
            text = head + "\n\n" + changes + "\n" + rest
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
