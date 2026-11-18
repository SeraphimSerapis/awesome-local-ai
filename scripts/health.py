#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Refresh public GitHub repository observations without reviewing or running projects."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import catalog


class GitHubRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        target = urlsplit(new_url)
        if target.scheme != "https" or target.netloc != "api.github.com":
            raise URLError("refused a redirect outside the GitHub API")
        return super().redirect_request(request, response, code, message, headers, new_url)


def github_api(path, expected_type=dict):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "awesome-local-ai-health",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request("https://api.github.com/" + path, headers=headers)
    with build_opener(GitHubRedirects()).open(request, timeout=20) as response:
        payload = response.read(1_000_001)
    catalog.require(len(payload) <= 1_000_000, "GitHub response exceeds the size limit")
    data = json.loads(payload, object_pairs_hook=catalog.unique_keys)
    type_label = "an array" if expected_type is list else "an object"
    catalog.require(isinstance(data, expected_type), f"GitHub response must be {type_label}")
    return data


def github_metadata(repository):
    name = repository.removeprefix("https://github.com/")
    return github_api("repos/" + name)


def normalize_github_timestamp(value, field):
    catalog.require(isinstance(value, str) and bool(value), f"{field} is missing")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise catalog.CatalogError(f"{field} must be an ISO-8601 timestamp") from error
    catalog.require(parsed.tzinfo is not None, f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def github_branch_commit(repository, default_branch):
    name = repository.removeprefix("https://github.com/")
    ref = quote(default_branch, safe="")
    try:
        # Query the commits list endpoint with per_page=1 so large head-commit diffs never exceed 1 MB.
        commits = github_api(f"repos/{name}/commits?sha={ref}&per_page=1", expected_type=list)
    except HTTPError as error:
        if error.code == 409:
            error.close()
            return None
        raise
    if not commits:
        return None
    entry = commits[0]
    catalog.require(isinstance(entry, dict), "GitHub commit list entry must be an object")
    commit = entry.get("commit")
    catalog.require(isinstance(commit, dict), "GitHub commit response is missing commit metadata")
    committer = commit.get("committer")
    author = commit.get("author")
    raw_date = (
        (committer.get("date") if isinstance(committer, dict) else None)
        or (author.get("date") if isinstance(author, dict) else None)
    )
    return normalize_github_timestamp(raw_date, "GitHub default-branch commit timestamp")


def observe(repository, previous, today, fetch=github_metadata, fetch_commit=None):
    if fetch_commit is None and fetch is github_metadata:
        fetch_commit = github_branch_commit
    record = {
        "repository": repository, "checked_at": today, "status": "check-failed",
        "detail": None, "last_successful_check": None, "canonical_repository": None,
        "archived": None, "disabled": None, "last_push": None,
        "last_default_branch_commit": None,
    }
    if previous and previous["repository"] == repository:
        record.update(previous)
        record.setdefault("last_default_branch_commit", None)
        record.update(checked_at=today, status="check-failed", detail=None)
    repo_fetched = False
    try:
        metadata = fetch(repository)
        catalog.require(isinstance(metadata, dict), "GitHub response must be an object")
        if metadata.get("private") is True:
            record.update(status="unavailable", detail="Repository is private; public access is unavailable.")
        else:
            catalog.require(metadata.get("private") is False, "GitHub public visibility is missing")
            repo_fetched = True
            default_branch = metadata.get("default_branch")
            catalog.require(
                default_branch is None or (isinstance(default_branch, str) and bool(default_branch.strip())),
                "GitHub default_branch must be a non-empty string or null",
            )
            default_commit = None
            if (
                fetch_commit is not None
                and metadata.get("disabled") is False
                and metadata.get("pushed_at") is not None
                and default_branch is not None
            ):
                default_commit = fetch_commit(repository, default_branch)
                if default_commit is not None:
                    default_commit = normalize_github_timestamp(
                        default_commit, "GitHub default-branch commit timestamp"
                    )
            successful = dict(
                record,
                status="reachable",
                detail=None,
                last_successful_check=today,
                canonical_repository=metadata["html_url"],
                archived=metadata["archived"],
                disabled=metadata["disabled"],
                last_push=metadata["pushed_at"],
                last_default_branch_commit=default_commit,
            )
            catalog.validate_health_record(successful)
            record = successful
    except HTTPError as error:
        try:
            if not repo_fetched and error.code in {404, 410, 451}:
                record.update(status="unavailable", detail=f"HTTP {error.code}; repository may be missing, private, or restricted.")
            else:
                record["detail"] = f"HTTP {error.code}; check failed, not evidence that the project is gone."
        finally:
            error.close()
    except (URLError, OSError, ValueError, KeyError, TypeError) as error:
        record["detail"] = f"Check failed with {type(error).__name__}; retry later."
    catalog.validate_health_record(record)
    return record


def load_previous_health(root, projects):
    path = root / "data/health.json"
    if not path.exists():
        return {}
    observations = catalog.read_json(path)
    catalog.require(isinstance(observations, dict), "health must be an object keyed by project ID")
    repositories = {project["id"]: project["repository"] for project in projects}
    current = {}
    for identifier, raw in observations.items():
        catalog.require(catalog.SLUG.fullmatch(identifier) is not None, "invalid health project ID")
        catalog.require(isinstance(raw, dict), f"health.{identifier}: health observation has missing or unexpected fields")
        record = dict({"last_default_branch_commit": None}, **raw)
        try:
            catalog.validate_health_record(record)
        except catalog.CatalogError as error:
            raise catalog.CatalogError(f"health.{identifier}: {error}") from error
        if record["repository"] == repositories.get(identifier):
            current[identifier] = record
    return current


def refresh(projects, previous, today, fetch=github_metadata, fetch_commit=None):
    return {
        project["id"]: observe(project["repository"], previous.get(project["id"]), today, fetch, fetch_commit)
        for project in projects
    }


def write_snapshot(path, observations):
    # Replace only after a complete write; an interrupted request never truncates the prior snapshot.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(json.dumps(observations, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        _, projects = catalog.load_catalog(catalog.ROOT)
        previous = load_previous_health(catalog.ROOT, projects)
        today = datetime.now(timezone.utc).date().isoformat()
        observations = refresh(projects, previous, today)
        write_snapshot(catalog.ROOT / "data/health.json", observations)
        counts = {status: sum(record["status"] == status for record in observations.values())
                  for status in ["reachable", "unavailable", "check-failed"]}
        print(f"Checked {len(observations)} repositories: {counts}")
    except (catalog.CatalogError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
