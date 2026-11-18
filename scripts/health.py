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
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import catalog


class GitHubRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        target = urlsplit(new_url)
        if target.scheme != "https" or target.netloc != "api.github.com":
            raise URLError("refused a redirect outside the GitHub API")
        return super().redirect_request(request, response, code, message, headers, new_url)


def github_metadata(repository):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "awesome-local-ai-health",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    name = repository.removeprefix("https://github.com/")
    request = Request("https://api.github.com/repos/" + name, headers=headers)
    with build_opener(GitHubRedirects()).open(request, timeout=20) as response:
        payload = response.read(1_000_001)
    catalog.require(len(payload) <= 1_000_000, "GitHub response exceeds the size limit")
    metadata = json.loads(payload, object_pairs_hook=catalog.unique_keys)
    catalog.require(isinstance(metadata, dict), "GitHub response must be an object")
    return metadata


def observe(repository, previous, today, fetch=github_metadata):
    record = {
        "repository": repository, "checked_at": today, "status": "check-failed",
        "detail": None, "last_successful_check": None, "canonical_repository": None,
        "archived": None, "disabled": None, "last_push": None,
    }
    if previous and previous["repository"] == repository:
        record.update(previous)
        record.update(checked_at=today, status="check-failed", detail=None)
    try:
        metadata = fetch(repository)
        catalog.require(isinstance(metadata, dict), "GitHub response must be an object")
        if metadata.get("private") is True:
            record.update(status="unavailable", detail="Repository is private; public access is unavailable.")
        else:
            catalog.require(metadata.get("private") is False, "GitHub public visibility is missing")
            successful = dict(record, status="reachable", detail=None, last_successful_check=today,
                              canonical_repository=metadata["html_url"], archived=metadata["archived"],
                              disabled=metadata["disabled"], last_push=metadata["pushed_at"])
            catalog.validate_health_record(successful)
            record = successful
    except HTTPError as error:
        try:
            if error.code in {404, 410, 451}:
                record.update(status="unavailable", detail=f"HTTP {error.code}; repository may be missing, private, or restricted.")
            else:
                record["detail"] = f"HTTP {error.code}; check failed, not evidence that the project is gone."
        finally:
            error.close()
    except (URLError, OSError, ValueError, KeyError, TypeError) as error:
        record["detail"] = f"Check failed ({type(error).__name__}); retry later."
    catalog.validate_health_record(record)
    return record


def refresh(projects, previous, today, fetch=github_metadata):
    return {project["id"]: observe(project["repository"], previous.get(project["id"]), today, fetch)
            for project in projects}


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
        previous = catalog.load_health(catalog.ROOT, projects)
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
