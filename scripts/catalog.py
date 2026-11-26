#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate the catalog, compile changelog fragments, and generate README and catalog index outputs. Python 3.11+, no dependencies."""

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import difflib
import ipaddress
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

from spdx_osi import OSI_LICENSES, SPDX_EXCEPTIONS

ROOT = Path(__file__).resolve().parent.parent
START = "<!-- catalog:start -->"
END = "<!-- catalog:end -->"
CATALOG_INDEX = "data/catalog.json"
MODE_SHORT = {
    "local": "Local",
    "local-client": "Client",
}
HEALTH_FLAG_LABELS = {
    "unchecked": "Not checked yet",
    "unavailable": "Unavailable",
    "check-failed": "Check failed",
    "archived": "Archived",
    "disabled": "Disabled",
    "redirected": "Redirected",
}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
DNS_TLD = re.compile(r"(?:[a-z]{2,63}|xn--[a-z0-9-]{1,58}[a-z0-9])")
GITHUB_OWNER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
GITHUB_REPO = re.compile(r"(?![.]{1,2}$)[A-Za-z0-9_.-]+")
COMMIT_SHA = re.compile(r"[0-9a-f]{40}")
REPOSITORY = re.compile(
    rf"https://github\.com/{GITHUB_OWNER.pattern}/{GITHUB_REPO.pattern}"
)
LICENSE_FILENAME = re.compile(r"(?:LICENSE|LICENCE|COPYING)(?:[.-][A-Za-z0-9._-]+)?", re.IGNORECASE)
SPDX_TOKEN = re.compile(r"\(|\)|[A-Za-z0-9.+-]+")
MARKDOWN_LINK = re.compile(r"\[((?:\\.|[^\[\]\\])*)\]\(([^)]*)\)")
WEEK_HEADING = re.compile(r"## Week of (\d{4}-\d{2}-\d{2})")
CHANGELOG_SECTIONS = ("Added", "Updated", "Removed")
CHANGELOG_FIELDS = {"section", "entry"}
TAXONOMY_COUNTED_SECTIONS = ("categories", "use_cases", "platforms", "hardware")
FIELDS = {
    "id", "name", "repository", "description", "category", "use_cases",
    "platforms", "hardware", "local_mode", "compatibility", "limitations",
    "license", "sources", "last_reviewed",
}
HEALTH_FIELDS = {
    "repository", "checked_at", "status", "detail", "last_successful_check",
    "canonical_repository", "archived", "disabled", "last_push",
    "last_default_branch_commit",
}
EXTERNAL_VERIFY_TOOLS = (
    ("markdownlint", "npx", "markdownlint-cli2@0.18.1"),
    ("typos", "typos", "v1.52.2"),
    ("lychee", "lychee", "v0.24.2"),
)


class CatalogError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CatalogError(message)


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except (OSError, ValueError) as error:
        raise CatalogError(f"{path}: {error}") from error


def write_text_atomic(path, content):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False, newline="\n"
        ) as output:
            temporary = Path(output.name)
            output.write(content)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def text(value, field, max_length=600):
    require(isinstance(value, str), f"{field} must be a string")
    require(0 < len(value) <= max_length, f"{field} must contain 1..{max_length} characters")
    require(value == value.strip(), f"{field} must not have surrounding whitespace")
    require(all(ord(char) >= 32 and ord(char) != 127 for char in value),
            f"{field} must be single-line text without control characters")


def plain_text(value, field, *, min_length=1, max_length=600, allow_urls=True):
    text(value, field, max_length)
    require(len(value) >= min_length, f"{field} must contain at least {min_length} characters")
    require(not re.match(r"^(?:[-*+]|\d+\.)(?:\s|$)", value),
            f"{field} must not start with a list marker")
    require(not re.search(r"(?<!\\)!\[", value), f"{field} must not contain Markdown images")
    require(MARKDOWN_LINK.search(value) is None,
            f"{field} must not contain Markdown links; put URLs in sources")
    if not allow_urls:
        require(not re.search(r"https?://", value, re.IGNORECASE),
                f"{field} must not contain URLs; put URLs in sources")


def url(value, field):
    text(value, field, 1000)
    require(not re.search(r"[\s<>\[\]()\\\"`]", value), f"{field} contains unsafe URL characters")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise CatalogError(f"{field}: {error}") from error
    require(parsed.scheme == "https" and bool(parsed.hostname), f"{field} must be an HTTPS URL")
    hostname = parsed.hostname
    require(
        parsed.username is None
        and parsed.password is None
        and port is None
        and parsed.netloc.casefold() == hostname,
        f"{field} must not contain credentials or a custom port",
    )
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        labels = hostname.split(".")
        require(
            len(labels) >= 2
            and all(DNS_LABEL.fullmatch(label) is not None for label in labels)
            and DNS_TLD.fullmatch(labels[-1]) is not None
            and hostname != "localhost"
            and not hostname.endswith(".localhost"),
            f"{field} must point to public documentation",
        )
    else:
        require(
            address.is_global and not (
                address.is_loopback
                or address.is_private
                or address.is_link_local
                or address.is_unspecified
                or address.is_multicast
                or address.is_reserved
            ),
            f"{field} must point to public documentation",
        )


def github_repo_parts(repository_url):
    owner, repo = repository_url.removeprefix("https://github.com/").split("/", 1)
    return owner, repo


def parse_raw_github_url(value, field):
    url(value, field)
    parsed = urlsplit(value)
    require(
        parsed.netloc == "raw.githubusercontent.com",
        f"{field} must use canonical lowercase https://raw.githubusercontent.com",
    )
    require(
        parsed.query == "" and parsed.fragment == "",
        f"{field} must not contain a query string or fragment",
    )
    require(
        not re.search(r"%(?:2f|5c|2e)", parsed.path, re.IGNORECASE),
        f"{field} must not contain encoded path separators or traversal segments",
    )
    require(
        parsed.path.startswith("/"),
        f"{field} must be https://raw.githubusercontent.com/<owner>/<repo>/<40-hex-sha>/<path>",
    )
    parts = parsed.path[1:].split("/")
    require(
        len(parts) >= 4 and all(part not in {"", ".", ".."} for part in parts),
        f"{field} must be https://raw.githubusercontent.com/<owner>/<repo>/<40-hex-sha>/<path>",
    )
    owner, repo, sha, *path_segments = parts
    require(
        GITHUB_OWNER.fullmatch(owner) is not None
        and GITHUB_REPO.fullmatch(repo) is not None
        and not repo.casefold().endswith(".git"),
        f"{field} must point to a canonical GitHub owner and repository",
    )
    require(
        COMMIT_SHA.fullmatch(sha) is not None,
        f"{field} must pin a lowercase 40-hex commit SHA",
    )
    return owner, repo, sha, path_segments


def validate_spdx(value):
    require(
        isinstance(value, str),
        "license.spdx must be an OSI-approved SPDX license string, not null",
    )
    text(value, "license.spdx", 100)
    require(
        re.fullmatch(r"[A-Za-z0-9.+() -]+", value) is not None
        and "  " not in value
        and "( " not in value
        and " )" not in value
        and "()" not in value
        and re.search(r"[^ (]\(", value) is None
        and re.search(r"\)[^ )]", value) is None,
        "license.spdx must be a valid SPDX expression",
    )
    tokens = SPDX_TOKEN.findall(value)
    require(bool(tokens), "license.spdx must be a valid SPDX expression")

    def parse_expr(pos):
        pos = parse_term(pos)
        while pos < len(tokens) and tokens[pos] in {"AND", "OR"}:
            pos = parse_term(pos + 1)
        return pos

    def parse_term(pos):
        require(pos < len(tokens), "license.spdx has an incomplete SPDX expression")
        if tokens[pos] == "(":
            pos = parse_expr(pos + 1)
            require(
                pos < len(tokens) and tokens[pos] == ")",
                "license.spdx has unbalanced parentheses in SPDX expression",
            )
            return pos + 1
        license_id = tokens[pos]
        require(
            license_id not in {"AND", "OR", "WITH", ")"},
            f"license.spdx has unexpected SPDX token: {license_id}",
        )
        require(
            license_id in OSI_LICENSES,
            f"license.spdx must use OSI-approved SPDX identifiers (rejected: {license_id})",
        )
        pos += 1
        if pos < len(tokens) and tokens[pos] == "WITH":
            pos += 1
            require(
                pos < len(tokens),
                "license.spdx WITH requires a valid SPDX exception identifier",
            )
            exception_id = tokens[pos]
            require(
                exception_id in SPDX_EXCEPTIONS,
                f"license.spdx WITH must use a valid SPDX exception (rejected: {exception_id})",
            )
            pos += 1
            require(
                pos >= len(tokens) or tokens[pos] != "WITH",
                "license.spdx cannot chain multiple WITH SPDX exceptions",
            )
        return pos

    end = parse_expr(0)
    if end != len(tokens):
        raise CatalogError(f"license.spdx has unexpected trailing SPDX token: {tokens[end]}")


def string_list(value, field, choices=None, nonempty=False):
    require(isinstance(value, list), f"{field} must be an array")
    require(not nonempty or bool(value), f"{field} must not be empty")
    for item in value:
        text(item, field)
        if choices is not None:
            require(item in choices, f"unknown {field} value: {item}")
    require(len(set(value)) == len(value), f"{field} contains duplicates")


def load_taxonomy(root):
    taxonomy = read_json(root / "data/taxonomy.json")
    require(isinstance(taxonomy, dict), "taxonomy must be an object")
    require(set(taxonomy) == {"categories", "use_cases", "platforms", "hardware", "local_modes"},
            "taxonomy has missing or unexpected fields")
    for field, choices in taxonomy.items():
        require(isinstance(choices, dict) and bool(choices), f"taxonomy {field} must be a nonempty object")
        for key, label in choices.items():
            require(SLUG.fullmatch(key) is not None, f"invalid taxonomy ID: {key}")
            text(label, f"taxonomy {field}.{key}", 100)
    require(set(taxonomy["local_modes"]) == {"local", "local-client"},
            "local_modes must retain the two documented meanings")
    return taxonomy


def validate_project(project, path, taxonomy, *, check_filename=True):
    require(isinstance(project, dict), "entry must be an object")
    require(set(project) == FIELDS,
            f"missing fields: {sorted(FIELDS - set(project))}; unexpected fields: {sorted(set(project) - FIELDS)}")
    text(project["id"], "id", 80)
    require(SLUG.fullmatch(project["id"]) is not None, "id must be a lowercase hyphenated slug")
    if check_filename:
        require(path.name == project["id"] + ".json", "filename must match id")
    plain_text(project["name"], "name", max_length=80, allow_urls=False)
    plain_text(project["description"], "description", min_length=15, max_length=180, allow_urls=False)
    require(
        project["description"].endswith(".") and not project["description"].endswith(".."),
        "description must end with a single period",
    )
    require(
        re.search(r"[!?]\s+\S|(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)\.\s+[A-Z]", project["description"]) is None,
        "description must be a single sentence",
    )
    url(project["repository"], "repository")
    require(REPOSITORY.fullmatch(project["repository"]) is not None,
            "repository must be a canonical https://github.com/owner/repo URL")
    require(not project["repository"].casefold().endswith(".git"), "repository must not end with .git")
    repo_owner, repo_name = github_repo_parts(project["repository"])
    repo_key = (repo_owner.casefold(), repo_name.casefold())
    for field, choices in [("category", "categories"), ("local_mode", "local_modes")]:
        text(project[field], field, 80)
        require(project[field] in taxonomy[choices], f"unknown {field}: {project[field]}")
    for field in ["use_cases", "platforms", "hardware"]:
        string_list(project[field], field, taxonomy[field], nonempty=field == "use_cases")
    platforms = set(project["platforms"])
    hardware = set(project["hardware"])
    require(not hardware or bool(platforms),
            "hardware tags require at least one physically tested platform")
    if "dgx-spark" in hardware:
        require("linux" in platforms, "dgx-spark hardware requires linux in platforms")
    if "apple-silicon" in hardware:
        require(bool(platforms & {"macos", "linux", "ios", "ipados"}),
                "apple-silicon hardware requires macos, linux, ios, or ipados in platforms")
    string_list(project["compatibility"], "compatibility")
    for item in project["compatibility"]:
        plain_text(item, "compatibility", allow_urls=True)
    string_list(project["limitations"], "limitations", nonempty=True)
    for item in project["limitations"]:
        plain_text(item, "limitations", allow_urls=True)
    license_info = project["license"]
    require(isinstance(license_info, dict) and set(license_info) == {"spdx", "url"},
            "license must contain spdx and url")
    validate_spdx(license_info["spdx"])
    lic_owner, lic_repo, _, lic_path = parse_raw_github_url(license_info["url"], "license.url")
    require(
        (lic_owner.casefold(), lic_repo.casefold()) == repo_key,
        "license.url must match the project's canonical repository",
    )
    require(
        len(lic_path) == 1 and LICENSE_FILENAME.fullmatch(lic_path[0]) is not None,
        "license.url must point to a top-level LICENSE or COPYING file",
    )
    sources = project["sources"]
    require(isinstance(sources, list) and bool(sources), "sources must be a nonempty array")
    license_url_folded = license_info["url"].casefold()
    seen_source_urls = set()
    has_canonical_raw_source = False
    for source in sources:
        require(isinstance(source, dict) and set(source) == {"url", "note"},
                "each source must contain url and note")
        source_url = source["url"]
        url(source_url, "source.url")
        plain_text(source["note"], "source.note", allow_urls=True)
        folded = source_url.casefold()
        require(folded != license_url_folded, "sources must not duplicate license.url")
        require(folded not in seen_source_urls, "sources contains duplicate URLs")
        seen_source_urls.add(folded)
        parsed = urlsplit(source_url)
        if parsed.hostname == "raw.githubusercontent.com":
            src_owner, src_repo, _, _ = parse_raw_github_url(source_url, "source.url")
            if (src_owner.casefold(), src_repo.casefold()) == repo_key:
                has_canonical_raw_source = True
        elif parsed.hostname in {"github.com", "www.github.com"}:
            commit_parts = parsed.path[1:].split("/") if parsed.path.startswith("/") else []
            is_commit_url = (
                parsed.netloc == "github.com"
                and parsed.query == ""
                and parsed.fragment == ""
                and len(commit_parts) == 4
                and GITHUB_OWNER.fullmatch(commit_parts[0]) is not None
                and GITHUB_REPO.fullmatch(commit_parts[1]) is not None
                and not commit_parts[1].casefold().endswith(".git")
                and commit_parts[2] == "commit"
                and COMMIT_SHA.fullmatch(commit_parts[3]) is not None
            )
            require(
                is_commit_url,
                "source.url GitHub evidence must use a 40-hex commit-pinned raw.githubusercontent.com URL (or /commit/<40-hex>)",
            )
    require(
        has_canonical_raw_source,
        "sources must include at least one 40-hex commit-pinned raw.githubusercontent.com file from the project's canonical repository",
    )
    text(project["last_reviewed"], "last_reviewed", 10)
    try:
        reviewed = date.fromisoformat(project["last_reviewed"])
    except ValueError as error:
        raise CatalogError("last_reviewed must be YYYY-MM-DD") from error
    require(reviewed.isoformat() == project["last_reviewed"] and reviewed <= datetime.now(timezone.utc).date(),
            "last_reviewed must be YYYY-MM-DD and not in the future")


def validate_example_project(root, taxonomy):
    path = root / "examples/project.json"
    if not path.exists():
        return
    require(path.is_file(), "examples/project.json must be a regular file")
    try:
        example = read_json(path)
        validate_project(example, path, taxonomy, check_filename=False)
    except CatalogError as error:
        raise CatalogError(f"examples/project.json: {error}") from error


def load_catalog(root=ROOT):
    taxonomy = load_taxonomy(root)
    projects_dir = root / "data/projects"
    require(projects_dir.is_dir(), "data/projects must be a directory")
    paths = []
    for entry in sorted(projects_dir.iterdir()):
        require(
            entry.is_file() and entry.suffix == ".json",
            f"data/projects/{entry.name}: project records must be .json files",
        )
        paths.append(entry)
    require(bool(paths), "catalog must contain at least one project")
    projects = []
    seen = {field: set() for field in ["id", "name", "repository"]}
    for path in paths:
        try:
            project = read_json(path)
            validate_project(project, path, taxonomy)
            for field, values in seen.items():
                value = project[field].casefold()
                require(value not in values, f"duplicate {field}: {project[field]}")
                values.add(value)
        except CatalogError as error:
            raise CatalogError(f"{path.name}: {error}") from error
        projects.append(project)
    return taxonomy, sorted(projects, key=lambda project: (project["name"].casefold(), project["id"]))


def taxonomy_usage_counts(taxonomy, projects):
    counts = {section: Counter() for section in TAXONOMY_COUNTED_SECTIONS}
    for project in projects:
        counts["categories"][project["category"]] += 1
        for section in ("use_cases", "platforms", "hardware"):
            for key in project[section]:
                counts[section][key] += 1
    for section in TAXONOMY_COUNTED_SECTIONS:
        for key in taxonomy[section]:
            counts[section].setdefault(key, 0)
    return counts


def validate_new_taxonomy_ids(root, taxonomy, projects, base_ref):
    require(COMMIT_SHA.fullmatch(base_ref) is not None, "base-ref must be a full commit SHA")
    merge_base = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        cwd=root, capture_output=True, text=True,
    )
    ref = merge_base.stdout.strip() if merge_base.returncode == 0 else base_ref
    shown = subprocess.run(
        ["git", "show", f"{ref}:data/taxonomy.json"],
        cwd=root, capture_output=True, text=True,
    )
    if shown.returncode != 0:
        return
    try:
        base_taxonomy = json.loads(shown.stdout, object_pairs_hook=unique_keys)
    except ValueError as error:
        raise CatalogError(f"base data/taxonomy.json at {ref}: {error}") from error
    counts = taxonomy_usage_counts(taxonomy, projects)
    for section in TAXONOMY_COUNTED_SECTIONS:
        base_keys = set(base_taxonomy.get(section, {})) if isinstance(base_taxonomy, dict) else set()
        for key in sorted(set(taxonomy[section]) - base_keys):
            count = counts[section][key]
            require(
                count >= 2,
                f"new taxonomy {section} ID '{key}' requires at least 2 qualifying projects (found {count})",
            )


def markdown(value):
    return re.sub(r"([\\`*_{}\[\]<>|])", r"\\\1", value)


def markdown_prose(value):
    parts = re.split(r"(https?://[^\s,;)\]>]+)", value)
    rendered = []
    for index, part in enumerate(parts):
        if index % 2 == 1:
            stripped = part.rstrip(".")
            trailing = part[len(stripped):]
            fence = "``" if "`" in stripped else "`"
            pad = " " if stripped.startswith("`") or stripped.endswith("`") else ""
            rendered.append(f"{fence}{pad}{stripped}{pad}{fence}{markdown(trailing)}")
        else:
            rendered.append(markdown(part))
    return "".join(rendered)


def project_anchor(project):
    return f'project-{project["id"]}'


def project_anchor_link(project):
    return f'[{markdown(project["name"])}](#{project_anchor(project)})'


def project_link(project):
    return f'[{markdown(project["name"])}]({project["repository"]})'


def health_date(value, field):
    text(value, field, 10)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise CatalogError(f"{field} must be YYYY-MM-DD") from error
    require(parsed.isoformat() == value and parsed <= datetime.now(timezone.utc).date(),
            f"{field} must be YYYY-MM-DD and not in the future")


def health_timestamp(value, field):
    text(value, field, 20)
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise CatalogError(f"{field} must be a UTC GitHub timestamp") from error
    require(parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value,
            f"{field} must be a UTC GitHub timestamp")


def validate_health_record(record):
    require(isinstance(record, dict) and set(record) == HEALTH_FIELDS,
            "health observation has missing or unexpected fields")
    for field in ["repository", "canonical_repository"]:
        value = record[field]
        if field == "canonical_repository" and value is None:
            continue
        url(value, f"health.{field}")
        require(REPOSITORY.fullmatch(value) is not None and not value.casefold().endswith(".git"),
                f"health.{field} must be a canonical GitHub repository URL")
    health_date(record["checked_at"], "health.checked_at")
    require(isinstance(record["status"], str) and record["status"] in {"reachable", "unavailable", "check-failed"},
            "invalid health status")
    if record["detail"] is not None:
        text(record["detail"], "health.detail")
    for field in ["archived", "disabled"]:
        require(record[field] is None or type(record[field]) is bool,
                f"health.{field} must be a boolean or null")
    for field in ["last_push", "last_default_branch_commit"]:
        if record[field] is not None:
            health_timestamp(record[field], f"health.{field}")
    successful = record["last_successful_check"]
    if successful is None:
        require(
            all(
                record[field] is None
                for field in [
                    "canonical_repository", "archived", "disabled",
                    "last_push", "last_default_branch_commit",
                ]
            ),
            "health metadata requires a successful observation",
        )
    else:
        health_date(successful, "health.last_successful_check")
        require(successful <= record["checked_at"], "successful health check cannot follow the latest attempt")
        require(all(record[field] is not None for field in ["canonical_repository", "archived", "disabled"]),
                "successful health observation needs repository flags")
    if record["status"] == "reachable":
        require(successful == record["checked_at"] and record["detail"] is None,
                "reachable health status requires a successful check on the attempt date")
    else:
        require(record["detail"] is not None, "unsuccessful health check needs an explanation")


def load_health(root, projects):
    path = root / "data/health.json"
    if not path.exists():
        return {}
    observations = read_json(path)
    require(isinstance(observations, dict), "health must be an object keyed by project ID")
    repositories = {project["id"]: project["repository"] for project in projects}
    current = {}
    for identifier, record in observations.items():
        require(SLUG.fullmatch(identifier) is not None, "invalid health project ID")
        try:
            validate_health_record(record)
        except CatalogError as error:
            raise CatalogError(f"health.{identifier}: {error}") from error
        require(identifier in repositories, f"health.{identifier}: unknown or removed project ID")
        require(
            record["repository"] == repositories[identifier],
            f"health.{identifier}: repository does not match project record; remove stale health entry",
        )
        current[identifier] = record
    return current


def health_flags(project, observation):
    if observation is None:
        return ["unchecked"]
    flags = []
    if observation["status"] == "unavailable":
        flags.append("unavailable")
    elif observation["status"] == "check-failed":
        flags.append("check-failed")
    if observation["archived"] is True:
        flags.append("archived")
    if observation["disabled"] is True:
        flags.append("disabled")
    canonical = observation.get("canonical_repository")
    if canonical and canonical.casefold() != project["repository"].casefold():
        flags.append("redirected")
    return flags


def actionable_health_flags(flags):
    return [flag for flag in flags if flag != "unchecked"]


def latest_health_date(health):
    dates = [record["checked_at"] for record in health.values() if record.get("checked_at")]
    return max(dates) if dates else None


def health_activity_dates(observation):
    if not observation or not observation.get("last_successful_check"):
        return None, None
    default_commit = (
        observation["last_default_branch_commit"][:10]
        if observation.get("last_default_branch_commit")
        else None
    )
    push_date = observation["last_push"][:10] if observation.get("last_push") else None
    return default_commit, push_date


def table_activity_cell(project, observation=None):
    record_link = f'[JSON](data/projects/{project["id"]}.json)'
    flags = health_flags(project, observation)
    if flags:
        label = ", ".join(HEALTH_FLAG_LABELS[flag] for flag in flags)
        return f"**{label}**; {record_link}"
    default_commit, push_date = health_activity_dates(observation)
    shown = default_commit or push_date or "Not reported"
    return f"{shown}; {record_link}"


def category_alert_line(project, observation):
    flags = actionable_health_flags(health_flags(project, observation))
    if not flags:
        return None
    parts = []
    if observation["status"] == "unavailable":
        parts.append(f'Unavailable on {observation["checked_at"]}: {markdown_prose(observation["detail"])}')
    elif observation["status"] == "check-failed":
        parts.append(f'Check failed on {observation["checked_at"]}: {markdown_prose(observation["detail"])}')
    if observation["archived"] is True:
        parts.append(f'Marked archived on GitHub as of {observation["last_successful_check"]}.')
    if observation["disabled"] is True:
        parts.append(f'Marked disabled on GitHub as of {observation["last_successful_check"]}.')
    canonical = observation.get("canonical_repository")
    if canonical and canonical.casefold() != project["repository"].casefold():
        slug = canonical.removeprefix("https://github.com/")
        parts.append(f"Repository redirect observed to [{markdown(slug)}]({canonical}); review the catalog URL.")
    if observation["status"] != "reachable" and observation.get("last_successful_check"):
        parts.append(f'Prior metadata retained from {observation["last_successful_check"]}.')
    return f'> - **{markdown(project["name"])}:** {" ".join(parts)}'


def project_detail_lines(project, observation=None, snapshot_date=None):
    meta = [f'reviewed {project["last_reviewed"]}']
    flags = health_flags(project, observation)
    if observation is None:
        meta.append("repository not checked yet")
    else:
        default_commit, push_date = health_activity_dates(observation)
        if default_commit and push_date and default_commit != push_date:
            meta.append(f"default-branch commit {default_commit}, push {push_date}")
        elif default_commit:
            meta.append(f"last commit {default_commit}")
        elif push_date:
            meta.append(f"last push {push_date}")
        elif observation.get("last_successful_check"):
            meta.append("activity not reported")
        if observation["checked_at"] != snapshot_date or actionable_health_flags(flags):
            meta.append(f'checked {observation["checked_at"]}')
    meta.append(f'[record](data/projects/{project["id"]}.json)')
    lines = [f'- **{markdown(project["name"])}**, ' + "; ".join(meta)]

    if observation is not None and actionable_health_flags(flags):
        status_bits = []
        if observation["status"] != "reachable":
            status_label = observation["status"].replace("check-failed", "check failed")
            status_bits.append(f'Status: {status_label}, {markdown_prose(observation["detail"])}')
            if observation.get("last_successful_check"):
                status_bits.append(f'Metadata retained from {observation["last_successful_check"]}.')
        if observation["archived"] is True:
            status_bits.append("Archived on GitHub.")
        if observation["disabled"] is True:
            status_bits.append("Disabled on GitHub.")
        canonical = observation.get("canonical_repository")
        if canonical and canonical.casefold() != project["repository"].casefold():
            slug = canonical.removeprefix("https://github.com/")
            status_bits.append(f"Redirected to [{markdown(slug)}]({canonical}).")
        lines.append(f'  - **Repository status:** {" ".join(status_bits)}')

    for label, field in [("Compatibility", "compatibility"), ("Limitations", "limitations")]:
        items = project[field]
        if len(items) == 1:
            lines.append(f"  - **{label}:** {markdown_prose(items[0])}")
        elif len(items) > 1:
            lines.append(f"  - **{label}:**")
            for item in items:
                lines.append(f"    - {markdown_prose(item)}")
    return lines


def validate_changelog_fragment(fragment):
    require(isinstance(fragment, dict), "changelog fragment must be an object")
    require(set(fragment) == CHANGELOG_FIELDS,
            f"missing fields: {sorted(CHANGELOG_FIELDS - set(fragment))}; "
            f"unexpected fields: {sorted(set(fragment) - CHANGELOG_FIELDS)}")
    text(fragment["section"], "section", 20)
    require(fragment["section"] in CHANGELOG_SECTIONS,
            f"section must be one of {', '.join(CHANGELOG_SECTIONS)}")
    entry = fragment["entry"]
    text(entry, "entry")
    require(not re.match(r"^(?:[-*+]|\d+\.|#+)(?:\s|$)", entry),
            "entry must not start with a list marker or heading")
    require(not re.search(r"(?<!\\)!\[", entry), "entry must not contain Markdown images")
    urls = []
    for match in MARKDOWN_LINK.finditer(entry):
        label, target = match.groups()
        text(label, "entry link label", 100)
        url(target, "entry link")
        urls.append(target)
    remainder = MARKDOWN_LINK.sub("", entry)
    require("](" not in remainder, "entry contains a malformed Markdown link")
    require(not re.search(r"(?:https?|javascript|data|file):", remainder, re.IGNORECASE),
            "entry URLs must use [label](https://...) Markdown links")
    require("<" not in remainder and ">" not in remainder,
            "entry must not contain raw HTML or autolinks")
    return sorted(set(urls))


def load_changelog_fragments(root=ROOT):
    directory = root / "changelog.d"
    if not directory.exists():
        return []
    require(directory.is_dir(), "changelog.d must be a directory")
    fragments = []
    seen = set()
    for path in sorted(directory.iterdir()):
        if path.name == ".gitkeep":
            require(path.is_file(), "changelog.d/.gitkeep must be a regular file")
            continue
        require(path.is_file() and path.suffix == ".json",
                f"changelog.d/{path.name}: changelog fragments must be .json files")
        require(len(path.stem) <= 80 and SLUG.fullmatch(path.stem) is not None,
                f"changelog.d/{path.name}: filename must be a lowercase hyphenated slug")
        try:
            raw = read_json(path)
            urls = validate_changelog_fragment(raw)
            key = (raw["section"], raw["entry"].casefold())
            require(key not in seen, f"duplicate changelog entry: {raw['entry']}")
            seen.add(key)
        except CatalogError as error:
            raise CatalogError(f"changelog.d/{path.name}: {error}") from error
        fragments.append({
            "slug": path.stem,
            "path": path,
            "section": raw["section"],
            "entry": raw["entry"],
            "urls": urls,
        })
    return fragments


def current_utc_monday():
    today = datetime.now(timezone.utc).date()
    return (today - timedelta(days=today.weekday())).isoformat()


def monday_for_date(value):
    return (value - timedelta(days=value.weekday())).isoformat()


def parse_week(value):
    text(value, "week", 10)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise CatalogError("week must be YYYY-MM-DD") from error
    require(parsed.isoformat() == value and parsed.weekday() == 0,
            "week must be a Monday in YYYY-MM-DD form")
    return value


def parse_week_sections(lines, week_label):
    sections = {name: [] for name in CHANGELOG_SECTIONS}
    seen_sections = set()
    current = None
    for raw_line in lines:
        if not raw_line.strip():
            continue
        if raw_line.startswith("### "):
            heading = raw_line[4:]
            require(heading in CHANGELOG_SECTIONS,
                    f"Week of {week_label}: unknown changelog subsection: {heading}")
            require(heading not in seen_sections,
                    f"Week of {week_label}: duplicate changelog subsection: {heading}")
            seen_sections.add(heading)
            current = heading
            continue
        require(current is not None and raw_line.startswith("- "),
                f"Week of {week_label}: unexpected line outside bullet list: {raw_line}")
        sections[current].append(raw_line)
    for name in seen_sections:
        require(bool(sections[name]), f"Week of {week_label}: empty subsection: {name}")
    return sections


def parse_changelog_document(changelog_text):
    preamble = []
    week_blocks = []
    seen_weeks = set()
    current_week = None
    current_lines = []
    for line in changelog_text.splitlines():
        if line.startswith("## "):
            match = WEEK_HEADING.fullmatch(line)
            require(match is not None, f"unexpected changelog heading: {line}")
            heading_week = parse_week(match.group(1))
            require(heading_week not in seen_weeks, f"duplicate changelog week: {heading_week}")
            if current_week is not None:
                require(
                    heading_week < current_week,
                    f"changelog weeks must be in descending order: {heading_week} after {current_week}",
                )
                week_blocks.append((current_week, current_lines))
            seen_weeks.add(heading_week)
            current_week = heading_week
            current_lines = []
        elif current_week is None:
            preamble.append(line)
        else:
            current_lines.append(line)
    if current_week is not None:
        week_blocks.append((current_week, current_lines))
    preamble_text = "\n".join(preamble).strip()
    require(preamble_text.startswith("# "), "CHANGELOG.md must start with a top-level heading")
    return preamble_text, week_blocks


def validate_changelog_file(root=ROOT):
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.exists():
        return
    require(changelog_path.is_file(), "CHANGELOG.md must be a regular file")
    _, week_blocks = parse_changelog_document(changelog_path.read_text(encoding="utf-8"))
    for block_week, block_lines in week_blocks:
        sections = parse_week_sections(block_lines, block_week)
        require(
            any(sections.values()),
            f"Week of {block_week}: week section must not be empty",
        )


def compile_changelog(changelog_text, fragments, week):
    week = parse_week(week)
    preamble_text, week_blocks = parse_changelog_document(changelog_text)
    if not fragments:
        return changelog_text
    existing = {name: [] for name in CHANGELOG_SECTIONS}
    target_index = None
    for index, (block_week, block_lines) in enumerate(week_blocks):
        if block_week == week:
            existing = parse_week_sections(block_lines, week)
            target_index = index
            break
    rendered_sections = [f"## Week of {week}"]
    for section in CHANGELOG_SECTIONS:
        bullets = list(existing[section])
        seen_bullets = {bullet.casefold() for bullet in bullets}
        incoming = sorted(
            (f'- {fragment["entry"]}' for fragment in fragments if fragment["section"] == section),
            key=lambda item: (item.casefold(), item),
        )
        for bullet in incoming:
            if bullet.casefold() not in seen_bullets:
                bullets.append(bullet)
                seen_bullets.add(bullet.casefold())
        if bullets:
            rendered_sections.append(f"### {section}\n\n" + "\n".join(bullets))
    target_block = "\n\n".join(rendered_sections)
    rendered_blocks = []
    inserted = False
    for index, (block_week, block_lines) in enumerate(week_blocks):
        if index == target_index:
            rendered_blocks.append(target_block)
            inserted = True
        else:
            if target_index is None and not inserted and block_week < week:
                rendered_blocks.append(target_block)
                inserted = True
            body = "\n".join(block_lines).strip()
            require(bool(body), f"Week of {block_week}: week section must not be empty")
            rendered_blocks.append(f"## Week of {block_week}\n\n{body}")
    if not inserted:
        rendered_blocks.append(target_block)
    return preamble_text + "\n\n" + "\n\n".join(rendered_blocks) + "\n"


def fragment_commit_date(root, fragment_path):
    if not shutil.which("git"):
        return None
    relative = f"changelog.d/{fragment_path.name}"
    result = subprocess.run(
        ["git", "log", "-1", "--diff-filter=A", "--format=%cI", "--", relative],
        cwd=root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    stamp = result.stdout.strip()
    if not stamp:
        return None
    try:
        parsed = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).date()
    return parsed.date()


def update_changelog(root=ROOT, week=None, fragments=None, *, by_commit_date=False, dry_run=False):
    require(not (by_commit_date and week is not None), "cannot combine --week with --by-commit-date")
    fragments = load_changelog_fragments(root) if fragments is None else fragments
    changelog_path = root / "CHANGELOG.md"
    require(changelog_path.is_file(), "CHANGELOG.md is missing")
    original = changelog_path.read_text(encoding="utf-8")
    if by_commit_date:
        grouped = {}
        fallback_week = current_utc_monday()
        for fragment in fragments:
            committed = fragment_commit_date(root, fragment["path"])
            target_week = monday_for_date(committed) if committed is not None else fallback_week
            grouped.setdefault(target_week, []).append(fragment)
        if not fragments:
            return 0, [], ""
        compiled = original
        weeks = sorted(grouped)
        for target_week in weeks:
            compiled = compile_changelog(compiled, grouped[target_week], target_week)
    else:
        target_week = current_utc_monday() if week is None else parse_week(week)
        compiled = compile_changelog(original, fragments, target_week)
        weeks = [target_week]
        if not fragments:
            return 0, weeks, ""
    diff_text = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            compiled.splitlines(keepends=True),
            fromfile="CHANGELOG.md",
            tofile="CHANGELOG.md",
        )
    )
    if dry_run:
        return len(fragments), weeks, diff_text
    write_text_atomic(changelog_path, compiled)
    for fragment in fragments:
        fragment["path"].unlink()
    return len(fragments), weeks, diff_text


def catalog_markdown(taxonomy, projects, health=None):
    health = {} if health is None else health
    snapshot_date = latest_health_date(health)
    lines = ["## Find tools by task", ""]
    for key, label in taxonomy["use_cases"].items():
        matches = sorted(
            (project for project in projects if key in project["use_cases"]),
            key=lambda project: (project["name"].casefold(), project["id"]),
        )
        if not matches:
            continue
        lines.append(f"- **{markdown(label)}:**")
        for index, project in enumerate(matches):
            suffix = "," if index < len(matches) - 1 else ""
            lines.append(f"  {project_anchor_link(project)}{suffix}")
    lines.append("")

    populated = []
    empty = []
    for category, label in taxonomy["categories"].items():
        matches = [project for project in projects if project["category"] == category]
        if matches:
            populated.append((category, label, matches))
        else:
            empty.append((category, label))

    lines.extend(["## Browse by category", ""])
    for category, label, _ in populated:
        lines.append(f"- [{markdown(label)}](#{category})")
    if empty:
        empty_links = ", ".join(f"[{markdown(label)}](#{cat})" for cat, label in empty)
        lines.append(f"- [Open categories](#open-categories): {empty_links}")
    lines.append("")

    snapshot_note = (
        f" from [the health snapshot](data/health.json), last updated {snapshot_date},"
        if snapshot_date
        else " from [the health snapshot](data/health.json)"
    )
    lines.extend([
        "Mode: **Local** runs the main AI workload locally; **Client** connects to a separate local model server or hardware runtime. "
        "Platforms and hardware reflect physically tested targets; `Not recorded` means unverified, not universal support. "
        f"Activity shows the latest observed default-branch commit date{snapshot_note} or a bold alert when unchecked or flagged. "
        "Expand the notes block under each category for compatibility, limitations, and human documentation-review dates.",
        "",
    ])

    for category, label, matches in populated:
        lines.extend([f'<a id="{category}"></a>', "", f"### {markdown(label)}", ""])
        lines.extend([
            "| Project | Summary | Mode | Platforms | Hardware | License | Activity |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        alerts = []
        for project in matches:
            observation = health.get(project["id"])
            platforms = ", ".join(taxonomy["platforms"][key] for key in project["platforms"]) or "Not recorded"
            hardware = ", ".join(taxonomy["hardware"][key] for key in project["hardware"]) or "Not recorded"
            license_name = project["license"]["spdx"]
            row = " | ".join([
                f'<a id="{project_anchor(project)}"></a>{project_link(project)}',
                markdown_prose(project["description"]),
                MODE_SHORT[project["local_mode"]],
                markdown(platforms),
                markdown(hardware),
                f'[{markdown(license_name)}]({project["license"]["url"]})',
                table_activity_cell(project, observation),
            ])
            lines.append(f"| {row} |")
            alert = category_alert_line(project, observation)
            if alert:
                alerts.append(alert)
        lines.append("")
        if alerts:
            lines.extend(["> **Repository alerts:**", ">"])
            lines.extend(alerts)
            lines.append("")
        lines.extend([
            "<details>",
            "<summary>Compatibility, limitations, and review notes</summary>",
            "",
        ])
        for project in matches:
            lines.extend(project_detail_lines(project, health.get(project["id"]), snapshot_date))
            lines.append("")
        lines.extend(["</details>", ""])

    if empty:
        lines.extend([
            "### Open categories",
            "",
            "These categories do not have entries yet. [Suggest a project](CONTRIBUTING.md).",
            "",
        ])
        for category, label in empty:
            lines.append(f'- <a id="{category}"></a>**{markdown(label)}**')
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def catalog_index_data(taxonomy, projects, health=None):
    health = {} if health is None else health
    entries = []
    for project in sorted(projects, key=lambda item: item["id"]):
        observation = health.get(project["id"])
        entries.append({
            "id": project["id"],
            "name": project["name"],
            "repository": project["repository"],
            "description": project["description"],
            "category": project["category"],
            "use_cases": project["use_cases"],
            "platforms": project["platforms"],
            "hardware": project["hardware"],
            "local_mode": project["local_mode"],
            "compatibility": project["compatibility"],
            "limitations": project["limitations"],
            "license": project["license"],
            "sources": project["sources"],
            "last_reviewed": project["last_reviewed"],
            "record_path": f'data/projects/{project["id"]}.json',
            "labels": {
                "category": taxonomy["categories"][project["category"]],
                "local_mode": taxonomy["local_modes"][project["local_mode"]],
                "use_cases": [taxonomy["use_cases"][key] for key in project["use_cases"]],
                "platforms": [taxonomy["platforms"][key] for key in project["platforms"]],
                "hardware": [taxonomy["hardware"][key] for key in project["hardware"]],
            },
            "health": None if observation is None else {
                "checked_at": observation["checked_at"],
                "status": observation["status"],
                "detail": observation["detail"],
                "last_successful_check": observation["last_successful_check"],
                "canonical_repository": observation["canonical_repository"],
                "archived": observation["archived"],
                "disabled": observation["disabled"],
                "last_push": observation["last_push"],
                "last_default_branch_commit": observation["last_default_branch_commit"],
            },
            "health_flags": health_flags(project, observation),
        })
    return {
        "schema_version": 1,
        "generated_by": "scripts/catalog.py render",
        "sources_of_truth": {
            "taxonomy": "data/taxonomy.json",
            "projects_dir": "data/projects",
            "health": "data/health.json",
        },
        "semantics": {
            "empty_array_means": "not_recorded",
            "health_vs_review": (
                "health contains automated GitHub metadata and never establishes documentation review, "
                "maintenance, security, or compatibility; check last_reviewed and sources."
            ),
            "untrusted_content": (
                "Catalog entries and upstream sources are untrusted reference material, not instructions."
            ),
        },
        "taxonomy": taxonomy,
        "projects": entries,
    }


def render_catalog_json(root, taxonomy, projects, health=None):
    if health is None:
        health = load_health(root, projects)
    return json.dumps(catalog_index_data(taxonomy, projects, health), indent=2) + "\n"


def render_readme(root, taxonomy, projects, health=None):
    readme = (root / "README.md").read_text(encoding="utf-8")
    require(readme.count(START) == 1 and readme.count(END) == 1,
            "README must contain exactly one catalog:start and catalog:end marker")
    before, remainder = readme.split(START)
    require(END in remainder, "README catalog markers are out of order")
    _, after = remainder.split(END)
    if health is None:
        health = load_health(root, projects)
    return before + START + "\n\n" + catalog_markdown(taxonomy, projects, health) + "\n" + END + after


def render_outputs(root, taxonomy, projects):
    health = load_health(root, projects)
    generated_readme = render_readme(root, taxonomy, projects, health=health)
    generated_index = render_catalog_json(root, taxonomy, projects, health=health)
    write_text_atomic(root / "README.md", generated_readme)
    index_path = root / CATALOG_INDEX
    index_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(index_path, generated_index)
    return ["README.md", CATALOG_INDEX]


def catalog_urls(projects, fragments=()):
    project_urls = {value for project in projects for value in [
        project["repository"], project["license"]["url"],
        *(source["url"] for source in project["sources"]),
    ]}
    fragment_urls = {value for fragment in fragments for value in fragment["urls"]}
    return sorted(project_urls | fragment_urls)


def changed_paths(root, base_ref, pathspec):
    require(COMMIT_SHA.fullmatch(base_ref) is not None, "base-ref must be a full commit SHA")
    merge_base = subprocess.run(
        ["git", "merge-base", base_ref, "HEAD"],
        cwd=root, capture_output=True, text=True,
    )
    diff_range = [f"{base_ref}...HEAD"] if merge_base.returncode == 0 else [base_ref, "HEAD"]
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", *diff_range, "--", pathspec],
        cwd=root, check=True, capture_output=True, text=True,
    )
    return set(result.stdout.splitlines())


def changed_projects(root, projects, base_ref):
    changed = changed_paths(root, base_ref, "data/projects/")
    return [project for project in projects if f'data/projects/{project["id"]}.json' in changed]


def changed_changelog_fragments(root, fragments, base_ref):
    changed = changed_paths(root, base_ref, "changelog.d/")
    return [fragment for fragment in fragments if f'changelog.d/{fragment["slug"]}.json' in changed]


def build_status_report(
    root,
    taxonomy,
    projects,
    health,
    fragments,
    *,
    stale_review_days=60,
    inactive_days=90,
    today=None,
):
    require(stale_review_days >= 0, "stale-review-days must be non-negative")
    require(inactive_days >= 0, "inactive-days must be non-negative")
    today = datetime.now(timezone.utc).date() if today is None else today
    fallback_week = monday_for_date(today)

    pending_fragments = []
    for fragment in fragments:
        committed = fragment_commit_date(root, fragment["path"])
        pending_fragments.append({
            "slug": fragment["slug"],
            "section": fragment["section"],
            "commit_date": committed.isoformat() if committed else None,
            "week": monday_for_date(committed) if committed else fallback_week,
        })

    missing_health = []
    flagged_health = []
    stale_reviews = []
    quiet_projects = []
    owners = {}

    for project in projects:
        pid = project["id"]
        owner, _ = github_repo_parts(project["repository"])
        owners.setdefault(owner.casefold(), []).append(pid)

        observation = health.get(pid)
        activity_date = None
        if observation is None:
            missing_health.append(pid)
        else:
            reasons = []
            if observation["status"] != "reachable":
                reasons.append(f'status={observation["status"]}')
            if observation["archived"]:
                reasons.append("archived")
            if observation["disabled"]:
                reasons.append("disabled")
            canonical = observation["canonical_repository"]
            if canonical and canonical.casefold() != project["repository"].casefold():
                reasons.append(f"redirect->{canonical}")
            if reasons:
                flagged_health.append({"id": pid, "reasons": reasons})
            raw_activity = observation["last_default_branch_commit"] or observation["last_push"]
            if raw_activity:
                activity_date = date.fromisoformat(raw_activity[:10])
                inactivity_age = (today - activity_date).days
                if inactivity_age >= inactive_days:
                    quiet_projects.append({
                        "id": pid,
                        "last_commit": activity_date.isoformat(),
                        "age_days": inactivity_age,
                    })

        reviewed = date.fromisoformat(project["last_reviewed"])
        review_age = (today - reviewed).days
        post_review_drift = (activity_date - reviewed).days if activity_date and activity_date > reviewed else 0
        if review_age >= stale_review_days:
            stale_reviews.append({
                "id": pid,
                "last_reviewed": project["last_reviewed"],
                "age_days": review_age,
                "last_commit": activity_date.isoformat() if activity_date else None,
                "post_review_drift_days": post_review_drift,
            })

    counts = taxonomy_usage_counts(taxonomy, projects)
    empty_categories = sorted(k for k, c in counts["categories"].items() if c == 0)
    unused_tags = []
    single_use_tags = []
    for section in TAXONOMY_COUNTED_SECTIONS:
        for key in sorted(taxonomy[section]):
            count = counts[section][key]
            if count == 0 and section != "categories":
                unused_tags.append((section, key))
            elif count == 1:
                owner_ids = [
                    p["id"]
                    for p in projects
                    if (p["category"] == key if section == "categories" else key in p[section])
                ]
                single_use_tags.append((section, key, owner_ids[0]))

    shared_owners = [
        {"owner": owner, "projects": sorted(pids)}
        for owner, pids in sorted(owners.items())
        if len(pids) >= 2
    ]

    return {
        "today": today.isoformat(),
        "project_count": len(projects),
        "health_count": len(health),
        "pending_fragments": pending_fragments,
        "missing_health": sorted(missing_health),
        "flagged_health": flagged_health,
        "stale_reviews": sorted(stale_reviews, key=lambda item: (-item["age_days"], item["id"])),
        "quiet_projects": sorted(quiet_projects, key=lambda item: (-item["age_days"], item["id"])),
        "empty_categories": empty_categories,
        "unused_tags": unused_tags,
        "single_use_tags": single_use_tags,
        "shared_owners": shared_owners,
        "stale_review_days": stale_review_days,
        "inactive_days": inactive_days,
    }


def format_status_report(report):
    lines = [
        f'Catalog status ({report["today"]}): {report["project_count"]} projects, '
        f'{report["health_count"]}/{report["project_count"]} health checked, '
        f'{len(report["pending_fragments"])} pending changelog fragments.',
        "",
        "Pending changelog.d fragments:",
    ]
    if report["pending_fragments"]:
        for item in report["pending_fragments"]:
            committed = item["commit_date"] or "uncommitted"
            lines.append(
                f'  - changelog.d/{item["slug"]}.json [{item["section"]}] '
                f'(added: {committed}, week: {item["week"]})'
            )
    else:
        lines.append("  (none)")

    lines.extend(["", "Health coverage & flags:"])
    if report["missing_health"]:
        lines.append("  - Missing from data/health.json: " + ", ".join(report["missing_health"]))
    if report["flagged_health"]:
        for item in report["flagged_health"]:
            lines.append(f'  - Flagged {item["id"]}: {", ".join(item["reasons"])}')
    if not report["missing_health"] and not report["flagged_health"]:
        lines.append("  (all entries checked and clean)")

    lines.extend(["", f'Stale reviews (>= {report["stale_review_days"]}d):'])
    if report["stale_reviews"]:
        for item in report["stale_reviews"]:
            drift = (
                f', commit {item["last_commit"]} (+{item["post_review_drift_days"]}d after review)'
                if item["post_review_drift_days"] > 0
                else ""
            )
            lines.append(
                f'  - {item["id"]}: reviewed {item["last_reviewed"]} ({item["age_days"]}d ago){drift}'
            )
    else:
        lines.append("  (none)")

    lines.extend(["", f'Quiet projects (>= {report["inactive_days"]}d since last commit):'])
    if report["quiet_projects"]:
        for item in report["quiet_projects"]:
            lines.append(f'  - {item["id"]}: last commit {item["last_commit"]} ({item["age_days"]}d ago)')
    else:
        lines.append("  (none)")

    lines.extend(["", "Taxonomy hygiene:"])
    if report["empty_categories"]:
        lines.append("  - Empty categories (open buckets): " + ", ".join(report["empty_categories"]))
    if report["unused_tags"]:
        lines.append(
            "  - Unused non-category tags (0 entries): "
            + ", ".join(f"{section}.{key}" for section, key in report["unused_tags"])
        )
    if report["single_use_tags"]:
        lines.append(
            "  - Single-use taxonomy IDs (1 entry): "
            + ", ".join(f"{section}.{key} ({pid})" for section, key, pid in report["single_use_tags"])
        )
    if not report["empty_categories"] and not report["unused_tags"] and not report["single_use_tags"]:
        lines.append("  (all taxonomy IDs have >= 2 entries)")

    lines.extend(["", "Shared-owner clusters (>= 2 repos):"])
    if report["shared_owners"]:
        for item in report["shared_owners"]:
            lines.append(f'  - {item["owner"]}: {", ".join(item["projects"])}')
    else:
        lines.append("  (none)")

    return "\n".join(lines)


def remove_projects(root, ids, reason, slug=None):
    require(bool(ids), "at least one project ID is required")
    require(len(set(ids)) == len(ids), "duplicate project IDs specified")
    taxonomy, projects = load_catalog(root)
    by_id = {project["id"]: project for project in projects}
    missing = [pid for pid in ids if pid not in by_id]
    require(not missing, f"unknown project ID(s): {', '.join(missing)}")
    require(len(projects) - len(ids) >= 1, "cannot remove all projects from the catalog")

    plain_text(reason, "reason", max_length=400)
    reason_clean = reason if reason[-1] in ".!?" else reason + "."

    fragment_slug = f"remove-{'-'.join(ids)}" if slug is None else slug
    require(
        len(fragment_slug) <= 80 and SLUG.fullmatch(fragment_slug) is not None,
        "changelog slug must be a lowercase hyphenated slug of at most 80 characters; pass --slug",
    )
    fragment_dir = root / "changelog.d"
    fragment_path = fragment_dir / f"{fragment_slug}.json"
    require(not fragment_path.exists(), f"changelog.d/{fragment_slug}.json already exists; pass --slug")

    removed = [by_id[pid] for pid in ids]
    def escape_label(name):
        return re.sub(r"([\\\[\]])", r"\\\1", name)

    links = [
        f'[{escape_label(project["name"])}]({project["repository"]})'
        for project in removed
    ]
    if len(removed) == 1:
        entry_text = f"{links[0]}, {reason_clean}"
    else:
        entry_text = f"Removed {', '.join(links)}: {reason_clean}"
    fragment_payload = {"section": "Removed", "entry": entry_text}
    validate_changelog_fragment(fragment_payload)

    touched_tags = {section: set() for section in TAXONOMY_COUNTED_SECTIONS}
    for project in removed:
        touched_tags["categories"].add(project["category"])
        for section in ("use_cases", "platforms", "hardware"):
            touched_tags[section].update(project[section])

    for pid in ids:
        (root / "data/projects" / f"{pid}.json").unlink()

    health_path = root / "data/health.json"
    removed_health = []
    if health_path.exists():
        raw_health = read_json(health_path)
        require(isinstance(raw_health, dict), "health must be an object keyed by project ID")
        removed_health = [pid for pid in ids if pid in raw_health]
        if removed_health:
            for pid in removed_health:
                raw_health.pop(pid, None)
            write_text_atomic(health_path, json.dumps(raw_health, indent=2, sort_keys=True) + "\n")

    fragment_dir.mkdir(exist_ok=True)
    write_text_atomic(fragment_path, json.dumps(fragment_payload, indent=2) + "\n")

    taxonomy, remaining = load_catalog(root)
    rendered = render_outputs(root, taxonomy, remaining)

    counts = taxonomy_usage_counts(taxonomy, remaining)
    low_tags = []
    for section in TAXONOMY_COUNTED_SECTIONS:
        for key in sorted(touched_tags[section]):
            count = counts[section][key]
            if count <= 1:
                low_tags.append((section, key, count))

    return {
        "removed": ids,
        "removed_health": removed_health,
        "fragment": f"changelog.d/{fragment_slug}.json",
        "rendered": rendered,
        "low_tags": low_tags,
    }


def run_check(root, base_ref=None):
    taxonomy, projects = load_catalog(root)
    health = load_health(root, projects)
    fragments = load_changelog_fragments(root)
    validate_changelog_file(root)
    validate_example_project(root, taxonomy)
    if base_ref is not None:
        validate_new_taxonomy_ids(root, taxonomy, projects, base_ref)
    generated_readme = render_readme(root, taxonomy, projects, health=health)
    require(
        generated_readme == (root / "README.md").read_text(encoding="utf-8"),
        "README is stale; run python3 scripts/catalog.py render",
    )
    generated_index = render_catalog_json(root, taxonomy, projects, health=health)
    index_path = root / CATALOG_INDEX
    require(
        index_path.is_file() and generated_index == index_path.read_text(encoding="utf-8"),
        "data/catalog.json is stale; run python3 scripts/catalog.py render",
    )
    return taxonomy, projects, fragments


def markdown_files(root):
    excluded = {".git", "node_modules", "lychee"}
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.md")
        if path.is_file() and excluded.isdisjoint(path.parts)
    )


def run_verify(root, *, strict=False, skip_external=False):
    results = []

    try:
        _, projects, fragments = run_check(root)
    except (CatalogError, OSError, subprocess.CalledProcessError) as error:
        results.append(("catalog check", "FAIL", str(error)))
    else:
        results.append((
            "catalog check",
            "PASS",
            f"{len(projects)} projects, {len(fragments)} fragments, README and data/catalog.json up to date",
        ))

    scripts_dir = root / "scripts"
    if scripts_dir.is_dir():
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py"],
            cwd=root, capture_output=True, text=True,
        )
        detail = (proc.stderr or proc.stdout).strip()
        if proc.returncode == 0:
            summary_line = detail.splitlines()[-1] if detail else "ok"
            results.append(("unit tests", "PASS", summary_line))
        else:
            results.append(("unit tests", "FAIL", detail))
    else:
        results.append(("unit tests", "SKIPPED", "no scripts directory"))

    if not skip_external:
        for label, binary, ci_version in EXTERNAL_VERIFY_TOOLS:
            resolved = shutil.which(binary)
            if not resolved:
                results.append((label, "SKIPPED", f"not installed; CI uses {ci_version}"))
                continue
            if label == "markdownlint":
                cmd = [resolved, "--yes", ci_version]
            elif label == "typos":
                cmd = [resolved]
            else:
                md_paths = markdown_files(root)
                if not md_paths:
                    results.append((label, "SKIPPED", "no Markdown files found"))
                    continue
                cmd = [resolved, "--offline", "--include-fragments", "--no-progress", *md_paths]
            proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
            detail = (proc.stderr or proc.stdout).strip()
            if proc.returncode == 0:
                results.append((label, "PASS", ci_version))
            else:
                results.append((label, "FAIL", detail or f"exit {proc.returncode}"))

    for name, status, detail in results:
        first_line = detail.splitlines()[0] if detail else ""
        if status == "FAIL":
            print(f"[{status}] {name}")
            if detail:
                for line in detail.splitlines():
                    print(f"  {line}")
        else:
            suffix = f" ({first_line})" if first_line else ""
            print(f"[{status}] {name}{suffix}")

    failed = any(status == "FAIL" for _, status, _ in results)
    skipped = any(status == "SKIPPED" for _, status, _ in results)
    return 1 if (failed or (strict and skipped)) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    validate_cmd = commands.add_parser("validate", help="Check all project records, changelog fragments, and taxonomy")
    validate_cmd.add_argument("--base-ref", help="Check newly added taxonomy IDs since this commit SHA")

    commands.add_parser("render", help="Update generated README sections and data/catalog.json")

    check_cmd = commands.add_parser("check", help="Check records, changelog fragments, README, and data/catalog.json without writing")
    check_cmd.add_argument("--base-ref", help="Check newly added taxonomy IDs since this commit SHA")

    changelog_cmd = commands.add_parser("changelog", help="Compile changelog.d fragments into CHANGELOG.md")
    week_group = changelog_cmd.add_mutually_exclusive_group()
    week_group.add_argument("--week", help="Target Monday-starting UTC week in YYYY-MM-DD form")
    week_group.add_argument(
        "--by-commit-date",
        action="store_true",
        help="Bucket each fragment by the Monday-starting UTC week of its introducing git commit",
    )
    changelog_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the compiled CHANGELOG.md diff without editing files or deleting fragments",
    )

    links_cmd = commands.add_parser("links", help="Print unique upstream URLs for a link checker")
    links_cmd.add_argument("--base-ref", help="Limit URLs to project records and changelog fragments changed since this commit SHA")

    status_cmd = commands.add_parser("status", help="Show offline maintainer status dashboard")
    status_cmd.add_argument("--stale-review-days", type=int, default=60, help="Highlight reviews at least this many days old")
    status_cmd.add_argument("--inactive-days", type=int, default=90, help="Highlight repos quiet for at least this many days")

    remove_cmd = commands.add_parser("remove", help="Remove project entries, prune health.json, add changelog fragment, and render")
    remove_cmd.add_argument("ids", nargs="+", help="Project ID(s) to remove")
    remove_cmd.add_argument("--reason", required=True, help="Short explanation recorded in the Removed changelog fragment")
    remove_cmd.add_argument("--slug", help="Optional changelog.d fragment filename stem")

    verify_cmd = commands.add_parser("verify", help="Run local catalog, test, and optional Markdown/spelling/link checks")
    verify_cmd.add_argument("--strict", action="store_true", help="Fail if any optional external check is skipped")
    verify_cmd.add_argument("--skip-external", action="store_true", help="Skip external npx/typos/lychee checks")

    args = parser.parse_args()
    try:
        if args.command == "verify":
            return run_verify(ROOT, strict=args.strict, skip_external=args.skip_external)
        if args.command == "remove":
            summary = remove_projects(ROOT, args.ids, args.reason, args.slug)
            print(
                f'Removed {len(summary["removed"])} project(s): {", ".join(summary["removed"])}. '
                f'Wrote {summary["fragment"]} and rendered {", ".join(summary["rendered"])}.'
            )
            if summary["removed_health"]:
                print("Pruned from data/health.json: " + ", ".join(summary["removed_health"]))
            if summary["low_tags"]:
                print(
                    "Taxonomy IDs now at <= 1 entry: "
                    + ", ".join(f"{section}.{key} ({count})" for section, key, count in summary["low_tags"])
                )
            return 0
        taxonomy, projects = load_catalog(ROOT)
        health = load_health(ROOT, projects)
        fragments = load_changelog_fragments(ROOT)
        if args.command == "links":
            selected_projects = changed_projects(ROOT, projects, args.base_ref) if args.base_ref else projects
            selected_fragments = changed_changelog_fragments(ROOT, fragments, args.base_ref) if args.base_ref else fragments
            for value in catalog_urls(selected_projects, selected_fragments):
                print(value)
        elif args.command == "validate":
            validate_changelog_file(ROOT)
            validate_example_project(ROOT, taxonomy)
            if args.base_ref:
                validate_new_taxonomy_ids(ROOT, taxonomy, projects, args.base_ref)
            print(f"Validated {len(projects)} projects and {len(fragments)} changelog fragments.")
        elif args.command == "status":
            report = build_status_report(
                ROOT,
                taxonomy,
                projects,
                health,
                fragments,
                stale_review_days=args.stale_review_days,
                inactive_days=args.inactive_days,
            )
            print(format_status_report(report))
        elif args.command == "changelog":
            count, weeks, diff_text = update_changelog(
                ROOT,
                args.week,
                fragments,
                by_commit_date=args.by_commit_date,
                dry_run=args.dry_run,
            )
            if not count:
                print("No changelog fragments to compile.")
            elif args.dry_run:
                print(f"Dry run: would compile {count} changelog fragments into {', '.join(weeks)}.")
                if diff_text:
                    print(diff_text, end="")
            elif len(weeks) == 1:
                print(f"Compiled {count} changelog fragments into Week of {weeks[0]}.")
            else:
                print(f"Compiled {count} changelog fragments across {len(weeks)} weeks: {', '.join(weeks)}.")
        elif args.command == "render":
            rendered = render_outputs(ROOT, taxonomy, projects)
            print(f"Rendered {len(projects)} projects ({', '.join(rendered)}).")
        else:
            run_check(ROOT, args.base_ref)
            print(
                f"Validated {len(projects)} projects and {len(fragments)} changelog fragments; "
                "README and data/catalog.json are up to date."
            )
    except (CatalogError, OSError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
