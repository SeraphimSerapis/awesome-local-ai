#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Merge only routine bot health refreshes verified by catalog CI."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import catalog


BRANCH = "automation/catalog-health"
REQUIRED_JOBS = {
    "Catalog / ubuntu-latest / Python 3.11",
    "Catalog / windows-latest / Python 3.13",
    "Documentation",
}


def command(*args, root=catalog.ROOT):
    return subprocess.run(args, cwd=root, check=True, capture_output=True, text=True).stdout


def api(repository, path):
    return json.loads(command("gh", "api", f"repos/{repository}/{path}"))


def validate_run(run, jobs, repository):
    catalog.require(run["head_repository"]["full_name"] == repository
                    and run["head_branch"] == BRANCH
                    and run["event"] == "workflow_dispatch"
                    and run["path"] == ".github/workflows/checks.yml"
                    and run["status"] == "completed" and run["conclusion"] == "success",
                    "not a successful catalog run on the repository's health branch")
    catalog.require(re.fullmatch(r"[0-9a-f]{40}", run["head_sha"]) is not None, "invalid head SHA")
    catalog.require(REQUIRED_JOBS <= {job["name"] for job in jobs}
                    and all(job["status"] == "completed" and job["conclusion"] == "success" for job in jobs),
                    "catalog CI jobs are missing, skipped, pending, or failed")


def validate_pr(pr, sha, repository, default_branch):
    catalog.require(pr["state"] == "open" and not pr["draft"]
                    and pr["user"]["login"] == "github-actions[bot]"
                    and pr["head"]["repo"]["full_name"] == repository
                    and pr["base"]["repo"]["full_name"] == repository
                    and pr["head"]["ref"] == BRANCH and pr["base"]["ref"] == default_branch
                    and pr["head"]["sha"] == sha,
                    "PR is not the bot's open health refresh at the tested SHA")


def validate_snapshot(snapshot, projects, today):
    catalog.require(isinstance(snapshot, dict) and set(snapshot) == {p["id"] for p in projects},
                    "snapshot must cover exactly the current catalog")
    for project in projects:
        record = snapshot[project["id"]]
        catalog.validate_health_record(record)
        catalog.require(record["repository"] == project["repository"]
                        and record["status"] == "reachable" and record["checked_at"] == today
                        and record["archived"] is False and record["disabled"] is False
                        and record["canonical_repository"].casefold() == project["repository"].casefold()
                        and (record["last_default_branch_commit"] is None
                             or isinstance(record["last_default_branch_commit"], str)),
                        f'{project["id"]}: stale or flagged observation needs manual review')


def validate_content(root, sha, today):
    base = command("git", "rev-parse", "HEAD", root=root).strip()
    command("git", "merge-base", "--is-ancestor", base, sha, root=root)
    changed = set(command("git", "diff", "--name-only", "--no-renames", base, sha, root=root).splitlines())
    catalog.require("data/health.json" in changed and changed <= {"data/health.json", "README.md"},
                    "changes extend beyond the health snapshot and generated README")
    for path in ["data/health.json", "README.md"]:
        entry = command("git", "ls-tree", sha, "--", path, root=root)
        catalog.require(entry.startswith("100644 blob "), f"{path} must be a regular non-executable file")
    snapshot_text = command("git", "show", f"{sha}:data/health.json", root=root)
    snapshot = json.loads(snapshot_text, object_pairs_hook=catalog.unique_keys)
    taxonomy, projects = catalog.load_catalog(root)
    validate_snapshot(snapshot, projects, today)
    # Render with trusted code and catalog data; never check out or execute the bot branch.
    with tempfile.TemporaryDirectory() as directory:
        staging = Path(directory)
        (staging / "data").mkdir()
        (staging / "data/health.json").write_text(snapshot_text, encoding="utf-8")
        (staging / "README.md").write_text((root / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
        expected = catalog.render_readme(staging, taxonomy, projects)
    actual = command("git", "show", f"{sha}:README.md", root=root)
    catalog.require(actual == expected, "README differs from trusted regeneration")
    return base


def main():
    try:
        event = catalog.read_json(Path(os.environ["GITHUB_EVENT_PATH"]))
        repository = os.environ["GITHUB_REPOSITORY"]
        run_id = os.environ["HEALTH_CI_RUN_ID"]
        catalog.require(re.fullmatch(r"[1-9][0-9]*", run_id) is not None, "invalid CI run ID")
        run = api(repository, f"actions/runs/{run_id}")
        jobs = api(repository, f'actions/runs/{run["id"]}/jobs?filter=latest&per_page=100')
        catalog.require(jobs["total_count"] == len(jobs["jobs"]), "CI job list is incomplete")
        validate_run(run, jobs["jobs"], repository)
        default_branch = event["repository"]["default_branch"]
        owner = repository.split("/")[0]
        prs = api(repository, f"pulls?state=open&base={default_branch}&head={owner}:{BRANCH}")
        catalog.require(len(prs) == 1, "expected one open health PR")
        pr = prs[0]
        sha = run["head_sha"]
        validate_pr(pr, sha, repository, default_branch)
        command("git", "fetch", "--no-tags", "origin", sha)
        today = datetime.now(timezone.utc).date().isoformat()
        base = validate_content(catalog.ROOT, sha, today)
        current_base = api(repository, f"git/ref/heads/{default_branch}")["object"]["sha"]
        catalog.require(current_base == base, "default branch advanced; refresh and rerun CI")
        validate_pr(api(repository, f'pulls/{pr["number"]}'), sha, repository, default_branch)
        command("gh", "pr", "merge", str(pr["number"]), "--repo", repository,
                "--merge", "--match-head-commit", sha)
        print(f'Merged routine health PR #{pr["number"]} at {sha}.')
    except (catalog.CatalogError, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"Health PR left for manual review: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
