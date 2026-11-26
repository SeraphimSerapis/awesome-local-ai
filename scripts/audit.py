#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Read-only compliance, staleness, and PR triage auditor for Awesome Local AI. Python 3.11+, stdlib only."""

import argparse
import base64
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import catalog  # noqa: E402
import health  # noqa: E402

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
RAW_GITHUB_URL_RE = re.compile(
    r"^https://raw\.githubusercontent\.com/([^/?#]+)/([^/?#]+)/([0-9a-f]{40})/([^?#]+)$"
)
ROOT_LICENSE_RE = re.compile(
    r"^(?:LICENSE|LICENCE|COPYING)(?:[.-][A-Za-z0-9._-]+)?$",
    re.IGNORECASE,
)
ROOT_NOTICE_RE = re.compile(r"^NOTICE(?:[.-][A-Za-z0-9._-]+)?$", re.IGNORECASE)
ROOT_README_RE = re.compile(r"^README(?:\.[A-Za-z0-9._-]+)?$", re.IGNORECASE)
ZERO_TAG_RE = re.compile(r"^v?0\.0\.0$", re.IGNORECASE)
LINK_LAST_RE = re.compile(r'<https://api\.github\.com/([^>]+)>;\s*rel="last"')
SPDX_TOKEN_RE = re.compile(r"[A-Za-z0-9.+-]+")
SPDX_OPERATORS = frozenset({"AND", "OR", "WITH"})
TEXT_DOC_SUFFIXES = frozenset({"", ".md", ".markdown", ".txt", ".rst", ".adoc"})

DISCLOSURE_RULES = (
    (
        "telemetry",
        re.compile(r"\btelemetry\b", re.IGNORECASE),
        re.compile(r"\btelemetry\b", re.IGNORECASE),
    ),
    (
        "analytics",
        re.compile(r"\banalytics\b", re.IGNORECASE),
        re.compile(r"\banalytics\b|\btelemetry\b", re.IGNORECASE),
    ),
    (
        "update",
        re.compile(
            r"\b(?:auto[- ]?update\w*|check(?:s|ing)? for updates?|software update\w*|update check\w*|updater)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bupdate\w*\b", re.IGNORECASE),
    ),
    (
        "sign in",
        re.compile(r"\b(?:sign[- ]?in|log[- ]?in|account required)\b", re.IGNORECASE),
        re.compile(r"\bsign[- ]?in\b|\blog[- ]?in\b|\baccount\b|\bauth", re.IGNORECASE),
    ),
    (
        "api key",
        re.compile(r"\bapi[- ]?keys?\b", re.IGNORECASE),
        re.compile(r"\bapi[- ]?keys?\b|\btoken\b|\bcredential", re.IGNORECASE),
    ),
    (
        "experimental",
        re.compile(r"\bexperimental\b", re.IGNORECASE),
        re.compile(r"\bexperimental\b|\bpreview\b|\bbeta\b|\balpha\b", re.IGNORECASE),
    ),
    (
        "preview",
        re.compile(r"\bpreview\b", re.IGNORECASE),
        re.compile(r"\bpreview\b|\bexperimental\b|\bbeta\b|\balpha\b|\bearly\b", re.IGNORECASE),
    ),
    (
        "commons clause",
        re.compile(r"\bcommons[- ]clause\b", re.IGNORECASE),
        re.compile(r"\bcommons[- ]clause\b|\bnotice\b", re.IGNORECASE),
    ),
)


class AuditRuntimeError(RuntimeError):
    """Raised on usage, git, or transient/auth GitHub API errors (exit code 2)."""


@dataclass(frozen=True)
class Finding:
    severity: str
    scope: str
    check: str
    message: str


def repo_owner_name(repository):
    tail = repository.removeprefix("https://github.com/")
    owner, repo = tail.split("/", 1)
    return owner, repo


def parse_raw_canonical_url(url, owner, repo):
    match = RAW_GITHUB_URL_RE.fullmatch(url)
    if match is None:
        return None
    raw_owner, raw_repo, sha, file_path = match.groups()
    if raw_owner.casefold() != owner.casefold() or raw_repo.casefold() != repo.casefold():
        return None
    return sha, file_path


def extract_spdx_ids(expression):
    if not expression:
        return set()
    return {
        token
        for token in SPDX_TOKEN_RE.findall(expression)
        if token not in SPDX_OPERATORS
    }


def _extract_commit_datetime(entry):
    if not isinstance(entry, dict):
        return None
    commit = entry.get("commit")
    if not isinstance(commit, dict):
        return None
    committer = commit.get("committer")
    author = commit.get("author")
    raw_date = (
        (committer.get("date") if isinstance(committer, dict) else None)
        or (author.get("date") if isinstance(author, dict) else None)
    )
    if not isinstance(raw_date, str) or not raw_date:
        return None
    normalized = health.normalize_github_timestamp(raw_date, "GitHub commit timestamp")
    return datetime.strptime(normalized, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _decode_contents_text(payload):
    if not isinstance(payload, dict) or payload.get("type") != "file":
        return None
    if payload.get("encoding") != "base64":
        return None
    encoded = payload.get("content")
    if not isinstance(encoded, str):
        return None
    try:
        raw = base64.b64decode(encoded, validate=False)
    except ValueError:
        return None
    return raw.decode("utf-8", errors="replace")


def _is_scannable_doc(path):
    filename = path.rsplit("/", 1)[-1]
    if ROOT_LICENSE_RE.fullmatch(filename):
        return False
    suffix = Path(filename).suffix.lower()
    return suffix in TEXT_DOC_SUFFIXES


def scan_disclosure_keywords(doc_texts, limitations):
    limitations_blob = "\n".join(limitations)
    found = []
    for label, doc_pattern, limit_pattern in DISCLOSURE_RULES:
        if any(doc_pattern.search(text) for text in doc_texts):
            if not limit_pattern.search(limitations_blob):
                found.append(label)
    return found


class GitHubClient:
    """Thin wrapper over health.github_api_with_headers preserving api.github.com security guarantees."""

    def _call(self, path, expected_type=dict, allow_codes=()):
        try:
            return health.github_api_with_headers(path, expected_type=expected_type)
        except HTTPError as error:
            code = error.code
            try:
                if code in allow_codes:
                    return None, {"_http_status": code}
                raise AuditRuntimeError(f"GitHub API HTTP {code} for {path}") from error
            finally:
                error.close()
        except catalog.CatalogError as error:
            raise AuditRuntimeError(f"GitHub API failure for {path}: {error}") from error
        except (URLError, OSError, TimeoutError, ValueError) as error:
            raise AuditRuntimeError(f"GitHub API failure for {path}: {type(error).__name__}") from error

    def get_repo(self, owner_repo):
        data, headers = self._call(f"repos/{owner_repo}", expected_type=dict, allow_codes=(404, 410, 451))
        if data is None:
            return None, headers["_http_status"]
        return data, 200

    def get_commits(self, owner_repo, branch, per_page=10):
        ref = quote(branch, safe="")
        data, headers = self._call(
            f"repos/{owner_repo}/commits?sha={ref}&per_page={per_page}",
            expected_type=list,
            allow_codes=(409,),
        )
        if data is None:
            return [], {}
        return data, headers

    def get_commits_by_path(self, api_path):
        data, headers = self._call(api_path, expected_type=list, allow_codes=(409,))
        if data is None:
            return [], {}
        return data, headers

    def get_root_tree(self, owner_repo, branch):
        ref = quote(branch, safe="")
        data, _ = self._call(
            f"repos/{owner_repo}/git/trees/{ref}",
            expected_type=dict,
            allow_codes=(404, 409),
        )
        return data

    def compare(self, owner_repo, base_sha, head_branch):
        ref = quote(head_branch, safe="")
        # Request page=2 with per_page=1 so GitHub omits files[] patches and large diffs stay under 1 MB.
        data, headers = self._call(
            f"repos/{owner_repo}/compare/{base_sha}...{ref}?per_page=1&page=2",
            expected_type=dict,
            allow_codes=(404, 422),
        )
        if data is None:
            return None, headers["_http_status"]
        return data, 200

    def get_contents(self, owner_repo, file_path, ref):
        quoted_path = quote(file_path, safe="/")
        quoted_ref = quote(ref, safe="")
        data, _ = self._call(
            f"repos/{owner_repo}/contents/{quoted_path}?ref={quoted_ref}",
            expected_type=dict,
            allow_codes=(404,),
        )
        return data

    def get_contents_list(self, owner_repo, dir_path, ref):
        quoted_path = quote(dir_path, safe="/")
        quoted_ref = quote(ref, safe="")
        data, _ = self._call(
            f"repos/{owner_repo}/contents/{quoted_path}?ref={quoted_ref}",
            expected_type=list,
            allow_codes=(404,),
        )
        return data

    def get_latest_release(self, owner_repo):
        data, _ = self._call(
            f"repos/{owner_repo}/releases/latest",
            expected_type=dict,
            allow_codes=(404,),
        )
        return data

    def get_tags(self, owner_repo, per_page=1):
        data, _ = self._call(
            f"repos/{owner_repo}/tags?per_page={per_page}",
            expected_type=list,
            allow_codes=(404,),
        )
        return data or []

    def get_releases(self, owner_repo, per_page=10):
        data, _ = self._call(
            f"repos/{owner_repo}/releases?per_page={per_page}",
            expected_type=list,
            allow_codes=(404,),
        )
        return data or []

    def get_contributors(self, owner_repo, per_page=5):
        data, _ = self._call(
            f"repos/{owner_repo}/contributors?per_page={per_page}",
            expected_type=list,
            allow_codes=(404,),
        )
        return data or []


def _git_diff_paths(root, base_ref, diff_filter=None, pathspec=None):
    merge_base = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    diff_range = [f"{base_ref}...HEAD"] if merge_base.returncode == 0 else [base_ref, "HEAD"]
    cmd = ["git", "diff", "--name-only"]
    if diff_filter:
        cmd.append(f"--diff-filter={diff_filter}")
    cmd.extend(diff_range)
    if pathspec:
        cmd.extend(["--", pathspec])
    try:
        result = subprocess.run(cmd, cwd=root, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise AuditRuntimeError(f"git diff against {base_ref} failed: {error}") from error
    return set(result.stdout.splitlines())


def _validate_changelog_file_compat(root):
    if hasattr(catalog, "validate_changelog_file"):
        catalog.validate_changelog_file(root)
        return
    changelog_path = root / "CHANGELOG.md"
    catalog.require(changelog_path.is_file(), "CHANGELOG.md is missing")
    catalog.compile_changelog(changelog_path.read_text(encoding="utf-8"), [], catalog.current_utc_monday())


def run_offline_checks(
    root,
    today,
    selected_ids=None,
    base_ref=None,
    warn_stale_days=90,
    fail_stale_days=180,
    warn_review_days=90,
    include_health_staleness=True,
):
    findings = []
    try:
        taxonomy, projects = catalog.load_catalog(root)
    except catalog.CatalogError as error:
        findings.append(Finding("ERROR", "catalog", "catalog-load", str(error)))
        return findings, None, [], {}

    health_data = {}
    try:
        health_data = catalog.load_health(root, projects)
    except catalog.CatalogError as error:
        findings.append(Finding("ERROR", "catalog", "health-load", str(error)))
        try:
            health_data = health.load_previous_health(root, projects)
        except catalog.CatalogError:
            health_data = {}

    try:
        catalog.load_changelog_fragments(root)
    except catalog.CatalogError as error:
        findings.append(Finding("ERROR", "catalog", "changelog-fragments", str(error)))

    try:
        _validate_changelog_file_compat(root)
    except catalog.CatalogError as error:
        findings.append(Finding("ERROR", "catalog", "changelog-file", str(error)))

    # Taxonomy hygiene (0-entry and 1-entry IDs)
    field_map = [
        ("categories", "category"),
        ("use_cases", "use_cases"),
        ("platforms", "platforms"),
        ("hardware", "hardware"),
    ]
    for tax_key, proj_key in field_map:
        counts = {key: 0 for key in taxonomy[tax_key]}
        for project in projects:
            value = project[proj_key]
            if isinstance(value, list):
                for item in value:
                    if item in counts:
                        counts[item] += 1
            elif value in counts:
                counts[value] += 1
        zero_ids = sorted(key for key, count in counts.items() if count == 0)
        one_ids = sorted(key for key, count in counts.items() if count == 1)
        if zero_ids:
            if tax_key == "categories":
                findings.append(
                    Finding(
                        "INFO",
                        "catalog",
                        "taxonomy-empty-category",
                        f"Open categories with 0 entries: {', '.join(zero_ids)}",
                    )
                )
            else:
                findings.append(
                    Finding(
                        "WARN",
                        "catalog",
                        "taxonomy-unused",
                        f"Unused taxonomy {tax_key} IDs (0 entries): {', '.join(zero_ids)}",
                    )
                )
        if one_ids and tax_key in {"categories", "use_cases"}:
            findings.append(
                Finding(
                    "INFO",
                    "catalog",
                    "taxonomy-single-use",
                    f"Single-entry taxonomy {tax_key} IDs (1 entry): {', '.join(one_ids)}",
                )
            )

    # Multi-repo owner grouping (Criterion 6)
    owners = defaultdict(list)
    for project in projects:
        owner, _ = repo_owner_name(project["repository"])
        owners[owner.casefold()].append(project["id"])
    multi_owners = {owner: sorted(ids) for owner, ids in owners.items() if len(ids) >= 2}

    scope_projects = projects
    if selected_ids is not None:
        scope_set = set(selected_ids)
        scope_projects = [project for project in projects if project["id"] in scope_set]

    for owner, ids in sorted(multi_owners.items()):
        if selected_ids is None or any(pid in selected_ids for pid in ids):
            findings.append(
                Finding(
                    "INFO",
                    "catalog",
                    "companion-repos",
                    f"Owner '{owner}' has {len(ids)} catalog entries ({', '.join(ids)}); verify Criterion 6 independence",
                )
            )

    # Health coverage and freshness (>14d), plus offline staleness/review age
    for project in scope_projects:
        pid = project["id"]
        obs = health_data.get(pid)
        if obs is None:
            findings.append(
                Finding("WARN", pid, "health-missing", "Missing from data/health.json; run scripts/health.py")
            )
        else:
            checked_age = (today - date.fromisoformat(obs["checked_at"])).days
            if checked_age > 14:
                findings.append(
                    Finding("WARN", pid, "health-stale", f'Health observation is {checked_age}d old (checked_at {obs["checked_at"]})')
                )
            if include_health_staleness:
                if obs["status"] != "reachable":
                    findings.append(
                        Finding("ERROR", pid, "health-status", f'Health status is {obs["status"]}: {obs["detail"]}')
                    )
                if obs["archived"] is True:
                    findings.append(Finding("ERROR", pid, "archived", "Health snapshot marks repository archived"))
                if obs["disabled"] is True:
                    findings.append(Finding("ERROR", pid, "disabled", "Health snapshot marks repository disabled"))
                canonical = obs.get("canonical_repository")
                if canonical and canonical.casefold() != project["repository"].casefold():
                    findings.append(
                        Finding("ERROR", pid, "redirect", f"Health snapshot observed redirect to {canonical}")
                    )
                commit_ts = obs.get("last_default_branch_commit")
                if commit_ts:
                    commit_age = (today - date.fromisoformat(commit_ts[:10])).days
                    if commit_age >= fail_stale_days:
                        findings.append(
                            Finding(
                                "ERROR",
                                pid,
                                "stale-commit",
                                f"Last default-branch commit {commit_ts[:10]} is {commit_age}d old (>= {fail_stale_days}d)",
                            )
                        )
                    elif commit_age >= warn_stale_days:
                        findings.append(
                            Finding(
                                "WARN",
                                pid,
                                "stale-commit",
                                f"Last default-branch commit {commit_ts[:10]} is {commit_age}d old (>= {warn_stale_days}d)",
                            )
                        )
        if include_health_staleness:
            review_age = (today - date.fromisoformat(project["last_reviewed"])).days
            if review_age > warn_review_days:
                findings.append(
                    Finding(
                        "WARN",
                        pid,
                        "stale-review",
                        f'last_reviewed {project["last_reviewed"]} is {review_age}d old (> {warn_review_days}d)',
                    )
                )

    # PR fragment hygiene under --base-ref
    if base_ref is not None:
        changed_proj_files = _git_diff_paths(root, base_ref, pathspec="data/projects/")
        changed_fragments = _git_diff_paths(root, base_ref, diff_filter="ACMR", pathspec="changelog.d/")
        changed_json_fragments = [p for p in changed_fragments if p.endswith(".json")]
        changed_changelog = _git_diff_paths(root, base_ref, pathspec="CHANGELOG.md")
        if changed_proj_files and not changed_json_fragments:
            findings.append(
                Finding(
                    "WARN",
                    "catalog",
                    "pr-changelog-fragment",
                    "data/projects/ changed without adding or updating a changelog.d/*.json fragment",
                )
            )
        if changed_proj_files and changed_changelog:
            findings.append(
                Finding(
                    "WARN",
                    "catalog",
                    "pr-changelog-direct-edit",
                    "CHANGELOG.md was edited alongside data/projects/; use changelog.d/ fragments on PR branches",
                )
            )

    return findings, taxonomy, projects, health_data


def _audit_live_repo(
    scope,
    repository,
    client,
    today,
    project=None,
    warn_stale_days=90,
    fail_stale_days=180,
    warn_review_days=90,
    max_drift_commits=100,
    collect_companion=False,
):
    findings = []
    owner, repo = repo_owner_name(repository)
    owner_repo = f"{owner}/{repo}"
    summary = {
        "scope": scope,
        "repository": repository,
        "reachable": False,
        "canonical_repository": None,
        "archived": None,
        "disabled": None,
        "fork": None,
        "stars": None,
        "forks": None,
        "default_branch": None,
        "github_license": None,
        "last_default_branch_commit": None,
        "commit_span_days": None,
        "distinct_commit_days": None,
        "repo_age_days": None,
        "latest_tag": None,
        "max_ahead_by": None,
        "has_root_license": None,
        "has_root_notice": None,
    }

    metadata, status_code = client.get_repo(owner_repo)
    if metadata is None:
        findings.append(
            Finding("ERROR", scope, "reachability", f"Repository returned HTTP {status_code} (missing, private, or restricted)")
        )
        return findings, summary, None
    if metadata.get("private") is True:
        findings.append(Finding("ERROR", scope, "reachability", "Repository is private"))
        return findings, summary, None

    summary["reachable"] = True
    canonical = metadata.get("html_url")
    summary["canonical_repository"] = canonical
    summary["archived"] = bool(metadata.get("archived"))
    summary["disabled"] = bool(metadata.get("disabled"))
    summary["fork"] = bool(metadata.get("fork"))
    summary["stars"] = metadata.get("stargazers_count")
    summary["forks"] = metadata.get("forks_count")
    default_branch = metadata.get("default_branch")
    summary["default_branch"] = default_branch
    license_obj = metadata.get("license") or {}
    github_spdx = license_obj.get("spdx_id") if isinstance(license_obj, dict) else None
    summary["github_license"] = github_spdx

    if summary["archived"]:
        findings.append(Finding("ERROR", scope, "archived", "Repository is archived on GitHub"))
    if summary["disabled"]:
        findings.append(Finding("ERROR", scope, "disabled", "Repository is disabled on GitHub"))
    if canonical and canonical.casefold() != repository.casefold():
        findings.append(Finding("ERROR", scope, "redirect", f"Repository redirects to {canonical}"))
    if summary["fork"]:
        findings.append(Finding("WARN", scope, "fork", "Repository is a GitHub fork; verify canonical repository (Criterion 1)"))
    if metadata.get("size") == 0 and metadata.get("pushed_at") is None:
        findings.append(Finding("ERROR", scope, "empty-repo", "Repository appears empty (Criterion 1)"))

    # License drift check (GitHub Licensee returns deprecated short IDs like AGPL-3.0 for AGPL-3.0-only)
    if project is not None:
        recorded_spdx = project["license"]["spdx"]
        if github_spdx and github_spdx != "NOASSERTION":
            recorded_ids = extract_spdx_ids(recorded_spdx)
            accepted_github_ids = {
                github_spdx,
                f"{github_spdx}-only",
                f"{github_spdx}-or-later",
            }
            if not (recorded_ids & accepted_github_ids):
                findings.append(
                    Finding(
                        "WARN",
                        scope,
                        "license-drift",
                        f"GitHub detected license {github_spdx}, but catalog records {recorded_spdx}",
                    )
                )

    # Repo created_at age (Criterion 4)
    created_raw = metadata.get("created_at")
    if isinstance(created_raw, str) and created_raw:
        created_norm = health.normalize_github_timestamp(created_raw, "GitHub created_at")
        created_date = date.fromisoformat(created_norm[:10])
        repo_age_days = (today - created_date).days
        summary["repo_age_days"] = repo_age_days
        if repo_age_days < 14:
            findings.append(
                Finding("ERROR", scope, "history-age", f"Repository age is {repo_age_days}d (< 14d, Criterion 4)")
            )

    # 14-day multi-day commit history (Criterion 4) & staleness
    if default_branch:
        commits, headers = client.get_commits(owner_repo, default_branch, per_page=10)
        dates = [dt for dt in (_extract_commit_datetime(entry) for entry in commits) if dt is not None]
        if not dates:
            findings.append(
                Finding("ERROR", scope, "commit-history", f"No commits found on default branch {default_branch}")
            )
        else:
            latest_dt = max(dates)
            earliest_dt = min(dates)
            distinct_days = {dt.date() for dt in dates}
            if (latest_dt.date() - earliest_dt.date()).days < 14 or len(distinct_days) < 2:
                link_header = headers.get("link", "")
                match = LINK_LAST_RE.search(link_header)
                if match is not None:
                    last_path = match.group(1)
                    repo_id = metadata.get("id")
                    allowed_prefixes = [f"repos/{owner_repo}/commits"]
                    if isinstance(repo_id, int) and not isinstance(repo_id, bool):
                        allowed_prefixes.append(f"repositories/{repo_id}/commits")
                    lowered = last_path.casefold()
                    if any(
                        lowered == prefix.casefold() or lowered.startswith(prefix.casefold() + "?")
                        for prefix in allowed_prefixes
                    ):
                        last_commits, _ = client.get_commits_by_path(last_path)
                        last_dates = [
                            dt
                            for dt in (_extract_commit_datetime(entry) for entry in last_commits)
                            if dt is not None
                        ]
                        if last_dates:
                            earliest_dt = min(earliest_dt, min(last_dates))
                            distinct_days.update(dt.date() for dt in last_dates)
            span_days = (latest_dt.date() - earliest_dt.date()).days
            summary["last_default_branch_commit"] = latest_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            summary["commit_span_days"] = span_days
            summary["distinct_commit_days"] = len(distinct_days)
            if span_days < 14:
                findings.append(
                    Finding(
                        "ERROR",
                        scope,
                        "commit-span",
                        f"Public commit span on {default_branch} is {span_days}d (< 14d, Criterion 4)",
                    )
                )
            if len(distinct_days) < 2:
                findings.append(
                    Finding(
                        "ERROR",
                        scope,
                        "commit-days",
                        f"Public commits span only {len(distinct_days)} distinct UTC day(s) (< 2, Criterion 4)",
                    )
                )
            stale_days = (today - latest_dt.date()).days
            if stale_days >= fail_stale_days:
                findings.append(
                    Finding(
                        "ERROR",
                        scope,
                        "stale-commit",
                        f"Last default-branch commit {latest_dt.date().isoformat()} is {stale_days}d old (>= {fail_stale_days}d); review for removal",
                    )
                )
            elif stale_days >= warn_stale_days:
                findings.append(
                    Finding(
                        "WARN",
                        scope,
                        "stale-commit",
                        f"Last default-branch commit {latest_dt.date().isoformat()} is {stale_days}d old (>= {warn_stale_days}d)",
                    )
                )

    # Top-level LICENSE/COPYING and NOTICE check (Criterion 5)
    root_readme_path = None
    if default_branch:
        tree_data = client.get_root_tree(owner_repo, default_branch)
        tree_items = tree_data.get("tree", []) if isinstance(tree_data, dict) else []
        root_blobs = [
            item["path"]
            for item in tree_items
            if isinstance(item, dict) and item.get("type") == "blob" and isinstance(item.get("path"), str)
        ]
        root_licenses = [name for name in root_blobs if ROOT_LICENSE_RE.fullmatch(name)]
        root_notices = [name for name in root_blobs if ROOT_NOTICE_RE.fullmatch(name)]
        root_readmes = sorted(name for name in root_blobs if ROOT_README_RE.fullmatch(name))
        if root_readmes:
            root_readme_path = root_readmes[0]
        summary["has_root_license"] = bool(root_licenses)
        summary["has_root_notice"] = bool(root_notices)
        if not root_licenses:
            findings.append(
                Finding("ERROR", scope, "root-license", "No top-level LICENSE or COPYING file in repository root (Criterion 5)")
            )
        if root_notices:
            notice_label = ", ".join(sorted(root_notices))
            already_cited = False
            if project is not None:
                all_urls = " ".join(source["url"] for source in project["sources"])
                all_limits = " ".join(project["limitations"])
                already_cited = bool(re.search(r"\bnotice\b", all_urls + " " + all_limits, re.IGNORECASE))
            if not already_cited:
                findings.append(
                    Finding(
                        "INFO",
                        scope,
                        "root-notice",
                        f"Repository root contains {notice_label}; check for bundled third-party license terms",
                    )
                )

    # Pinned SHA reachability, drift, file existence, and advisory disclosure scan (Criterion 7)
    doc_texts = []
    if project is not None and default_branch:
        pinned_urls = [project["license"]["url"]] + [source["url"] for source in project["sources"]]
        unique_shas = []
        unique_files = []
        seen_shas = set()
        seen_files = set()
        for url in pinned_urls:
            parsed = parse_raw_canonical_url(url, owner, repo)
            if parsed is None:
                continue
            sha, file_path = parsed
            if sha not in seen_shas:
                seen_shas.add(sha)
                unique_shas.append(sha)
            if (sha, file_path) not in seen_files:
                seen_files.add((sha, file_path))
                unique_files.append((sha, file_path))

        review_age_days = (today - date.fromisoformat(project["last_reviewed"])).days
        max_ahead = None
        for sha in unique_shas:
            compare_data, cmp_status = client.compare(owner_repo, sha, default_branch)
            if compare_data is None:
                findings.append(
                    Finding(
                        "ERROR",
                        scope,
                        "pinned-sha",
                        f"Pinned commit {sha[:12]} is unreachable from {default_branch} (HTTP {cmp_status})",
                    )
                )
                continue
            ahead_by = compare_data.get("ahead_by", 0)
            if isinstance(ahead_by, int):
                max_ahead = ahead_by if max_ahead is None else max(max_ahead, ahead_by)
                if ahead_by > max_drift_commits:
                    findings.append(
                        Finding(
                            "WARN",
                            scope,
                            "sha-drift",
                            f"Pinned commit {sha[:12]} is {ahead_by} commits behind {default_branch} (> {max_drift_commits})",
                        )
                    )
                if review_age_days > warn_review_days and ahead_by > 0:
                    findings.append(
                        Finding(
                            "WARN",
                            scope,
                            "review-drift",
                            f'last_reviewed {project["last_reviewed"]} is {review_age_days}d old with {ahead_by} commits since {sha[:12]}',
                        )
                    )
        summary["max_ahead_by"] = max_ahead

        for sha, file_path in unique_files:
            contents = client.get_contents(owner_repo, file_path, sha)
            if contents is None:
                findings.append(
                    Finding(
                        "ERROR",
                        scope,
                        "pinned-file",
                        f"Pinned file {file_path} not found at commit {sha[:12]}",
                    )
                )
                continue
            if _is_scannable_doc(file_path):
                decoded = _decode_contents_text(contents)
                if decoded:
                    doc_texts.append(decoded)
    elif project is None and default_branch and root_readme_path:
        contents = client.get_contents(owner_repo, root_readme_path, default_branch)
        decoded = _decode_contents_text(contents) if contents else None
        if decoded:
            doc_texts.append(decoded)

    if doc_texts:
        limitations = project["limitations"] if project is not None else []
        undisclosed = scan_disclosure_keywords(doc_texts, limitations)
        if undisclosed:
            findings.append(
                Finding(
                    "INFO",
                    scope,
                    "disclosure-scan",
                    f"Advisory: pinned docs mention {', '.join(undisclosed)} (verify whether limitations should disclose)",
                )
            )

    # Release / tag check (Criterion 3)
    latest_release = client.get_latest_release(owner_repo)
    tag_name = None
    if isinstance(latest_release, dict) and isinstance(latest_release.get("tag_name"), str):
        tag_name = latest_release["tag_name"]
    else:
        tags = client.get_tags(owner_repo, per_page=1)
        if tags and isinstance(tags[0], dict) and isinstance(tags[0].get("name"), str):
            tag_name = tags[0]["name"]
    summary["latest_tag"] = tag_name
    if tag_name is None:
        findings.append(
            Finding("INFO", scope, "release-tag", "No tagged release or tag found; verify stable-toolchain source build manually (Criterion 3)")
        )
    elif ZERO_TAG_RE.fullmatch(tag_name):
        findings.append(
            Finding("ERROR", scope, "release-tag", f"Latest tag is {tag_name}; 0.0.0 stubs do not qualify (Criterion 3)")
        )

    # Companion-repo adoption signals (Criterion 6)
    companion_entry = None
    if collect_companion and default_branch:
        releases = client.get_releases(owner_repo, per_page=10)
        workflows = client.get_contents_list(owner_repo, ".github/workflows", default_branch)
        contributors = client.get_contributors(owner_repo, per_page=5)
        companion_entry = {
            "id": scope,
            "repository": repository,
            "stars": summary["stars"],
            "forks": summary["forks"],
            "releases_sampled": len(releases),
            "has_ci_workflows": bool(workflows),
            "contributors_sampled": len(contributors),
        }

    return findings, summary, companion_entry


def run_audit(
    root=catalog.ROOT,
    client=None,
    today=None,
    project_ids=(),
    base_ref=None,
    repo_url=None,
    offline=False,
    warn_stale_days=90,
    fail_stale_days=180,
    warn_review_days=90,
    max_drift_commits=100,
):
    today = datetime.now(timezone.utc).date() if today is None else today
    client = GitHubClient() if client is None else client

    if repo_url is not None:
        if (
            catalog.REPOSITORY.fullmatch(repo_url) is None
            or repo_url.lower().endswith(".git")
        ):
            raise AuditRuntimeError("--repo must be a canonical https://github.com/owner/repo URL")
        findings = []
        projects = []
        try:
            _, projects = catalog.load_catalog(root)
        except catalog.CatalogError:
            projects = []
        owner, _ = repo_owner_name(repo_url)
        same_repo = [p["id"] for p in projects if p["repository"].casefold() == repo_url.casefold()]
        if same_repo:
            findings.append(
                Finding("ERROR", repo_url, "duplicate-repo", f"Repository is already listed as {', '.join(same_repo)}")
            )
        same_owner = sorted(
            p["id"]
            for p in projects
            if repo_owner_name(p["repository"])[0].casefold() == owner.casefold()
            and p["repository"].casefold() != repo_url.casefold()
        )
        if same_owner:
            findings.append(
                Finding(
                    "WARN",
                    repo_url,
                    "companion-repos",
                    f"Owner '{owner}' already has catalog entries: {', '.join(same_owner)} (verify Criterion 6 independence)",
                )
            )
        project_summaries = []
        companion_groups = {}
        if offline:
            findings.append(Finding("INFO", repo_url, "offline", "Live GitHub checks skipped (--offline)"))
        else:
            live_findings, summary, companion_entry = _audit_live_repo(
                repo_url,
                repo_url,
                client,
                today,
                project=None,
                warn_stale_days=warn_stale_days,
                fail_stale_days=fail_stale_days,
                warn_review_days=warn_review_days,
                max_drift_commits=max_drift_commits,
                collect_companion=bool(same_owner),
            )
            findings.extend(live_findings)
            project_summaries.append(summary)
            if companion_entry is not None:
                companion_groups[owner.casefold()] = [companion_entry]
        return _build_report(today, offline, findings, project_summaries, companion_groups)

    if base_ref is not None and SHA40_RE.fullmatch(base_ref) is None:
        raise AuditRuntimeError("--base-ref must be a lowercase 40-hex commit SHA")

    # Determine selected project IDs for offline scoping and live execution
    selected_ids = None
    preliminary_projects = []
    try:
        _, preliminary_projects = catalog.load_catalog(root)
    except catalog.CatalogError:
        preliminary_projects = []

    if project_ids:
        known = {project["id"] for project in preliminary_projects}
        unknown = [pid for pid in project_ids if pid not in known]
        if preliminary_projects and unknown:
            raise AuditRuntimeError(f"unknown project ID(s): {', '.join(unknown)}")
        selected_ids = list(dict.fromkeys(project_ids))
    elif base_ref is not None and preliminary_projects:
        try:
            changed = catalog.changed_projects(root, preliminary_projects, base_ref)
        except (catalog.CatalogError, OSError, subprocess.CalledProcessError) as error:
            raise AuditRuntimeError(f"failed to resolve changed projects against {base_ref}: {error}") from error
        selected_ids = [project["id"] for project in changed]

    findings, _, projects, _ = run_offline_checks(
        root,
        today,
        selected_ids=selected_ids,
        base_ref=base_ref,
        warn_stale_days=warn_stale_days,
        fail_stale_days=fail_stale_days,
        warn_review_days=warn_review_days,
        include_health_staleness=offline,
    )

    owners = defaultdict(list)
    for project in projects:
        owner, _ = repo_owner_name(project["repository"])
        owners[owner.casefold()].append(project["id"])
    multi_owner_set = {owner for owner, ids in owners.items() if len(ids) >= 2}

    target_projects = projects
    if selected_ids is not None:
        id_order = {pid: idx for idx, pid in enumerate(selected_ids)}
        target_projects = sorted(
            (project for project in projects if project["id"] in id_order),
            key=lambda project: id_order[project["id"]],
        )

    project_summaries = []
    companion_groups = defaultdict(list)
    if not offline:
        for project in target_projects:
            owner, _ = repo_owner_name(project["repository"])
            is_multi = owner.casefold() in multi_owner_set
            live_findings, summary, companion_entry = _audit_live_repo(
                project["id"],
                project["repository"],
                client,
                today,
                project=project,
                warn_stale_days=warn_stale_days,
                fail_stale_days=fail_stale_days,
                warn_review_days=warn_review_days,
                max_drift_commits=max_drift_commits,
                collect_companion=is_multi,
            )
            findings.extend(live_findings)
            project_summaries.append(summary)
            if companion_entry is not None:
                companion_groups[owner.casefold()].append(companion_entry)

    return _build_report(today, offline, findings, project_summaries, dict(companion_groups))


def _build_report(today, offline, findings, project_summaries, companion_groups):
    severity_rank = {"ERROR": 0, "WARN": 1, "INFO": 2}
    ordered_findings = sorted(
        findings,
        key=lambda item: (severity_rank.get(item.severity, 9), item.scope, item.check, item.message),
    )
    errors = sum(item.severity == "ERROR" for item in ordered_findings)
    warnings = sum(item.severity == "WARN" for item in ordered_findings)
    infos = sum(item.severity == "INFO" for item in ordered_findings)
    return {
        "generated_at": today.isoformat(),
        "offline": offline,
        "summary": {
            "errors": errors,
            "warnings": warnings,
            "info": infos,
            "projects_checked": len(project_summaries),
        },
        "findings": [asdict(item) for item in ordered_findings],
        "projects": project_summaries,
        "companion_groups": companion_groups,
    }


def _escape_md(value):
    return str(value).replace("|", "\\|")


def format_text(report):
    summary = report["summary"]
    mode = "offline" if report["offline"] else "live"
    lines = [
        f'Catalog audit ({mode}, {report["generated_at"]}): '
        f'{summary["errors"]} error(s), {summary["warnings"]} warning(s), {summary["info"]} info; '
        f'{summary["projects_checked"]} repo(s) queried live.',
    ]
    if report["findings"]:
        lines.append("")
        for item in report["findings"]:
            lines.append(f'[{item["severity"]}] {item["scope"]} ({item["check"]}): {item["message"]}')
    if report["companion_groups"]:
        lines.extend(["", "Companion-repo adoption signals:"])
        for owner, items in sorted(report["companion_groups"].items()):
            lines.append(f"  Owner {owner}:")
            for entry in items:
                ci_label = "yes" if entry["has_ci_workflows"] else "no"
                lines.append(
                    f'    - {entry["id"]}: stars={entry["stars"]}, forks={entry["forks"]}, '
                    f'releases={entry["releases_sampled"]}, ci={ci_label}, '
                    f'contributors={entry["contributors_sampled"]}'
                )
    return "\n".join(lines) + "\n"


def format_markdown(report):
    summary = report["summary"]
    mode = "offline" if report["offline"] else "live"
    lines = [
        f'## Catalog audit ({mode}, {report["generated_at"]})',
        "",
        f'- Errors: {summary["errors"]}',
        f'- Warnings: {summary["warnings"]}',
        f'- Info: {summary["info"]}',
        f'- Repositories queried live: {summary["projects_checked"]}',
    ]
    if report["findings"]:
        lines.extend([
            "",
            "### Findings",
            "",
            "| Severity | Scope | Check | Message |",
            "| --- | --- | --- | --- |",
        ])
        for item in report["findings"]:
            lines.append(
                f'| {item["severity"]} | `{_escape_md(item["scope"])}` | `{_escape_md(item["check"])}` | {_escape_md(item["message"])} |'
            )
    if report["companion_groups"]:
        lines.extend([
            "",
            "### Companion-repo adoption signals",
            "",
            "| Owner | Project | Stars | Forks | Releases (<=10) | CI workflows | Contributors (<=5) |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for owner, items in sorted(report["companion_groups"].items()):
            for entry in items:
                ci_label = "yes" if entry["has_ci_workflows"] else "no"
                lines.append(
                    f'| `{_escape_md(owner)}` | `{_escape_md(entry["id"])}` | {entry["stars"]} | {entry["forks"]} | '
                    f'{entry["releases_sampled"]} | {ci_label} | {entry["contributors_sampled"]} |'
                )
    return "\n".join(lines) + "\n"


def format_json(report):
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        nargs="+",
        action="extend",
        default=[],
        metavar="ID",
        help="Audit only the named catalog project ID(s)",
    )
    parser.add_argument(
        "--base-ref",
        metavar="SHA",
        help="Scope live checks to projects changed since this 40-hex commit SHA and check PR fragment hygiene",
    )
    parser.add_argument(
        "--repo",
        metavar="URL",
        help="Triage a standalone candidate GitHub repository URL (https://github.com/owner/repo)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run only local offline checks without GitHub API requests",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--warn-stale-days",
        type=int,
        default=90,
        help="Warn when last default-branch commit is at least this many days old (default: 90)",
    )
    parser.add_argument(
        "--fail-stale-days",
        type=int,
        default=180,
        help="Error when last default-branch commit is at least this many days old (default: 180)",
    )
    parser.add_argument(
        "--warn-review-days",
        type=int,
        default=90,
        help="Warn when last_reviewed is older than this many days with upstream drift (default: 90)",
    )
    parser.add_argument(
        "--max-drift-commits",
        type=int,
        default=100,
        help="Warn when a pinned commit is more than this many commits behind default branch (default: 100)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on warnings in addition to errors",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 2

    if args.repo and (args.project or args.base_ref):
        print("Error: --repo cannot be combined with --project or --base-ref", file=sys.stderr)
        return 2
    if (
        args.warn_stale_days < 0
        or args.fail_stale_days < 0
        or args.warn_review_days < 0
        or args.max_drift_commits < 0
        or args.fail_stale_days < args.warn_stale_days
    ):
        print("Error: invalid threshold values", file=sys.stderr)
        return 2

    try:
        report = run_audit(
            root=catalog.ROOT,
            project_ids=args.project,
            base_ref=args.base_ref,
            repo_url=args.repo,
            offline=args.offline,
            warn_stale_days=args.warn_stale_days,
            fail_stale_days=args.fail_stale_days,
            warn_review_days=args.warn_review_days,
            max_drift_commits=args.max_drift_commits,
        )
    except AuditRuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    formatter = {"text": format_text, "markdown": format_markdown, "json": format_json}[args.format]
    sys.stdout.write(formatter(report))
    if report["summary"]["errors"] > 0:
        return 1
    if args.strict and report["summary"]["warnings"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
