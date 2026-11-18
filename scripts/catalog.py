#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate the catalog, compile changelog fragments, and generate README sections. Python 3.11+, no dependencies."""

import argparse
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
START = "<!-- catalog:start -->"
END = "<!-- catalog:end -->"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REPOSITORY = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
MARKDOWN_LINK = re.compile(r"\[((?:\\.|[^\[\]\\])*)\]\(([^)]*)\)")
WEEK_HEADING = re.compile(r"## Week of (\d{4}-\d{2}-\d{2})")
CHANGELOG_SECTIONS = ("Added", "Updated", "Removed")
CHANGELOG_FIELDS = {"section", "entry"}
FIELDS = {
    "id", "name", "repository", "description", "category", "use_cases",
    "platforms", "hardware", "local_mode", "compatibility", "limitations",
    "license", "sources", "last_reviewed",
}
HEALTH_FIELDS = {
    "repository", "checked_at", "status", "detail", "last_successful_check",
    "canonical_repository", "archived", "disabled", "last_push",
}


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


def text(value, field, max_length=600):
    require(isinstance(value, str), f"{field} must be a string")
    require(0 < len(value) <= max_length, f"{field} must contain 1..{max_length} characters")
    require(value == value.strip(), f"{field} must not have surrounding whitespace")
    require(all(ord(char) >= 32 and ord(char) != 127 for char in value),
            f"{field} must be single-line text without control characters")


def url(value, field):
    text(value, field, 1000)
    require(not re.search(r"[\s<>\[\]()\\\"`]", value), f"{field} contains unsafe URL characters")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise CatalogError(f"{field}: {error}") from error
    require(parsed.scheme == "https" and bool(parsed.hostname), f"{field} must be an HTTPS URL")
    require(parsed.username is None and parsed.password is None and port is None,
            f"{field} must not contain credentials or a custom port")
    require(parsed.hostname not in {"localhost", "127.0.0.1", "::1"},
            f"{field} must point to public documentation")


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
    require(set(taxonomy["local_modes"]) == {"local", "local-client", "cloud-dependent"},
            "local_modes must retain the three documented meanings")
    return taxonomy


def validate_project(project, path, taxonomy):
    require(isinstance(project, dict), "entry must be an object")
    require(set(project) == FIELDS,
            f"missing fields: {sorted(FIELDS - set(project))}; unexpected fields: {sorted(set(project) - FIELDS)}")
    for field, limit in [("id", 80), ("name", 80), ("description", 180)]:
        text(project[field], field, limit)
    require(SLUG.fullmatch(project["id"]) is not None, "id must be a lowercase hyphenated slug")
    require(path.name == project["id"] + ".json", "filename must match id")
    url(project["repository"], "repository")
    require(REPOSITORY.fullmatch(project["repository"]) is not None,
            "repository must be a canonical https://github.com/owner/repo URL")
    require(not project["repository"].endswith(".git"), "repository must not end with .git")
    for field, choices in [("category", "categories"), ("local_mode", "local_modes")]:
        text(project[field], field, 80)
        require(project[field] in taxonomy[choices], f"unknown {field}: {project[field]}")
    for field in ["use_cases", "platforms", "hardware"]:
        string_list(project[field], field, taxonomy[field], nonempty=field == "use_cases")
    for field in ["compatibility", "limitations"]:
        string_list(project[field], field)
    if project["local_mode"] == "cloud-dependent":
        require(bool(project["limitations"]), "cloud integrations must explain their cloud requirements")
    license_info = project["license"]
    require(isinstance(license_info, dict) and set(license_info) == {"spdx", "url"},
            "license must contain spdx and url")
    if license_info["spdx"] is not None:
        text(license_info["spdx"], "license.spdx", 100)
        require(re.fullmatch(r"[A-Za-z0-9.+-]+(?: (?:OR|AND) [A-Za-z0-9.+-]+)*", license_info["spdx"]) is not None,
                "license.spdx must be an SPDX identifier or a simple AND/OR expression")
    else:
        require(any(word in note.lower() for note in project["limitations"] for word in ["license", "licensing"]),
                "unknown licensing must be explained in limitations")
    url(license_info["url"], "license.url")
    sources = project["sources"]
    require(isinstance(sources, list) and bool(sources), "sources must be a nonempty array")
    source_urls = []
    for source in sources:
        require(isinstance(source, dict) and set(source) == {"url", "note"},
                "each source must contain url and note")
        url(source["url"], "source.url")
        text(source["note"], "source.note")
        source_urls.append(source["url"])
    require(len(set(source_urls)) == len(source_urls), "sources contains duplicate URLs")
    text(project["last_reviewed"], "last_reviewed", 10)
    try:
        reviewed = date.fromisoformat(project["last_reviewed"])
    except ValueError as error:
        raise CatalogError("last_reviewed must be YYYY-MM-DD") from error
    require(reviewed.isoformat() == project["last_reviewed"] and reviewed <= date.today(),
            "last_reviewed must be YYYY-MM-DD and not in the future")


def load_catalog(root=ROOT):
    taxonomy = load_taxonomy(root)
    paths = sorted((root / "data/projects").glob("*.json"))
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


def markdown(value):
    return re.sub(r"([\\`*_{}\[\]<>|])", r"\\\1", value)


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


def validate_health_record(record):
    require(isinstance(record, dict) and set(record) == HEALTH_FIELDS,
            "health observation has missing or unexpected fields")
    for field in ["repository", "canonical_repository"]:
        value = record[field]
        if field == "canonical_repository" and value is None:
            continue
        url(value, f"health.{field}")
        require(REPOSITORY.fullmatch(value) is not None and not value.endswith(".git"),
                f"health.{field} must be a canonical GitHub repository URL")
    health_date(record["checked_at"], "health.checked_at")
    require(isinstance(record["status"], str) and record["status"] in {"reachable", "unavailable", "check-failed"},
            "invalid health status")
    if record["detail"] is not None:
        text(record["detail"], "health.detail")
    for field in ["archived", "disabled"]:
        require(record[field] is None or type(record[field]) is bool,
                f"health.{field} must be a boolean or null")
    if record["last_push"] is not None:
        text(record["last_push"], "health.last_push", 20)
        try:
            parsed = datetime.strptime(record["last_push"], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as error:
            raise CatalogError("health.last_push must be a UTC GitHub timestamp") from error
        require(parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == record["last_push"],
                "health.last_push must be a UTC GitHub timestamp")
    successful = record["last_successful_check"]
    if successful is None:
        require(all(record[field] is None for field in ["canonical_repository", "archived", "disabled", "last_push"]),
                "health metadata requires a successful observation")
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
        if record["repository"] == repositories.get(identifier):
            current[identifier] = record
    return current


def health_lines(project, observation):
    reviewed = f'Documentation reviewed: {project["last_reviewed"]}.'
    if observation is None:
        return [f"  - {reviewed} Repository: not checked yet."]
    status = observation["status"].replace("check-failed", "check failed")
    result = [f'  - {reviewed} Repository checked: {observation["checked_at"]} ({status}).']
    if observation["status"] != "reachable":
        result.append(f'  - Check note: {markdown(observation["detail"])}')
        if observation["last_successful_check"]:
            result.append(f'  - Upstream observations retained from the last successful check on {observation["last_successful_check"]}.')
    if observation["last_successful_check"]:
        pushed = observation["last_push"][:10] if observation["last_push"] else "Not reported"
        archived = "yes" if observation["archived"] else "no"
        disabled = "yes" if observation["disabled"] else "no"
        result.append(f"  - Last observed push: {pushed}. Archived: {archived}. Disabled: {disabled}.")
        canonical = observation["canonical_repository"]
        if canonical.casefold() != project["repository"].casefold():
            result.append(f"  - Repository redirect observed: [{markdown(canonical)}]({canonical}). Review the catalog URL.")
    return result


def project_lines(project, taxonomy, observation=None):
    platforms = ", ".join(taxonomy["platforms"][key] for key in project["platforms"]) or "Not recorded"
    hardware = ", ".join(taxonomy["hardware"][key] for key in project["hardware"]) or "Not recorded"
    license_name = project["license"]["spdx"] or "Unclear; check upstream"
    result = [
        f'- {project_link(project)}: {markdown(project["description"])}',
        f'  - {markdown(taxonomy["local_modes"][project["local_mode"]])}. Platforms: {markdown(platforms)}. Hardware: {markdown(hardware)}.',
        f'  - License: [{markdown(license_name)}]({project["license"]["url"]}). [Metadata and evidence](data/projects/{project["id"]}.json).',
    ]
    result.extend(health_lines(project, observation))
    for note in project["limitations"]:
        result.append(f"  - Note: {markdown(note)}")
    return result


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
    require(not re.match(r"^[-*+](?:\s|$)", entry), "entry must not start with a list marker")
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


def compile_changelog(changelog_text, fragments, week):
    week = parse_week(week)
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
            seen_weeks.add(heading_week)
            if current_week is not None:
                week_blocks.append((current_week, current_lines))
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


def update_changelog(root=ROOT, week=None, fragments=None):
    week = current_utc_monday() if week is None else parse_week(week)
    fragments = load_changelog_fragments(root) if fragments is None else fragments
    changelog_path = root / "CHANGELOG.md"
    require(changelog_path.is_file(), "CHANGELOG.md is missing")
    original = changelog_path.read_text(encoding="utf-8")
    compiled = compile_changelog(original, fragments, week)
    if not fragments:
        return 0, week
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=root, delete=False) as output:
            temporary = Path(output.name)
            output.write(compiled)
        temporary.replace(changelog_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    for fragment in fragments:
        fragment["path"].unlink()
    return len(fragments), week


def catalog_markdown(taxonomy, projects, health=None):
    health = {} if health is None else health
    core = [project for project in projects if project["local_mode"] != "cloud-dependent"]
    cloud = [project for project in projects if project["local_mode"] == "cloud-dependent"]
    lines = ["## Find tools by task", ""]
    for key, label in taxonomy["use_cases"].items():
        matches = sorted(
            (project for project in projects if key in project["use_cases"]),
            key=lambda project: (project["name"].casefold(), project["id"]),
        )
        if matches:
            lines.extend([f"### {markdown(label)}", ""])
            for project in matches:
                suffix = " (cloud)" if project["local_mode"] == "cloud-dependent" else ""
                lines.append(f"- {project_link(project)}{suffix}")
            lines.append("")
    lines.extend(["## Browse by category", ""])
    for category, label in taxonomy["categories"].items():
        lines.append(f"- [{markdown(label)}](#{category})")
    lines.extend(["- [Cloud integrations](#cloud-integrations)", ""])
    for category, label in taxonomy["categories"].items():
        lines.extend([f'<a id="{category}"></a>', "", f"### {markdown(label)}", ""])
        matches = [project for project in core if project["category"] == category]
        for project in matches:
            lines.extend(project_lines(project, taxonomy, health.get(project["id"])))
            lines.append("")
        if not matches:
            lines.extend(["No local-first entries yet. [Suggest a project](CONTRIBUTING.md).", ""])
            if any(project["category"] == category for project in cloud):
                lines.extend(["Cloud-dependent entries are in [Cloud integrations](#cloud-integrations).", ""])
    lines.extend(["## Cloud integrations", "", "These integrations connect agents to cloud services. They are not offline local AI tools.", ""])
    for project in cloud:
        lines.extend(project_lines(project, taxonomy, health.get(project["id"])))
        lines.append("")
    if not cloud:
        lines.extend(["No entries yet.", ""])
    return "\n".join(lines).rstrip() + "\n"


def render_readme(root, taxonomy, projects):
    readme = (root / "README.md").read_text(encoding="utf-8")
    require(readme.count(START) == 1 and readme.count(END) == 1,
            "README must contain exactly one catalog:start and catalog:end marker")
    before, remainder = readme.split(START)
    require(END in remainder, "README catalog markers are out of order")
    _, after = remainder.split(END)
    health = load_health(root, projects)
    return before + START + "\n\n" + catalog_markdown(taxonomy, projects, health) + "\n" + END + after


def catalog_urls(projects, fragments=()):
    project_urls = {value for project in projects for value in [
        project["repository"], project["license"]["url"],
        *(source["url"] for source in project["sources"]),
    ]}
    fragment_urls = {value for fragment in fragments for value in fragment["urls"]}
    return sorted(project_urls | fragment_urls)


def changed_projects(root, projects, base_ref):
    require(re.fullmatch(r"[0-9a-f]{40}", base_ref) is not None, "base-ref must be a full commit SHA")
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", base_ref, "HEAD", "--", "data/projects/"],
        cwd=root, check=True, capture_output=True, text=True,
    )
    changed = set(result.stdout.splitlines())
    return [project for project in projects if f'data/projects/{project["id"]}.json' in changed]


def changed_changelog_fragments(root, fragments, base_ref):
    require(re.fullmatch(r"[0-9a-f]{40}", base_ref) is not None, "base-ref must be a full commit SHA")
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", base_ref, "HEAD", "--", "changelog.d/"],
        cwd=root, check=True, capture_output=True, text=True,
    )
    changed = set(result.stdout.splitlines())
    return [fragment for fragment in fragments if f'changelog.d/{fragment["slug"]}.json' in changed]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Check all project records, changelog fragments, and taxonomy")
    commands.add_parser("render", help="Update generated README sections")
    commands.add_parser("check", help="Check records, changelog fragments, and README generation without writing")
    changelog = commands.add_parser("changelog", help="Compile changelog.d fragments into CHANGELOG.md")
    changelog.add_argument("--week", help="Target Monday-starting UTC week in YYYY-MM-DD form")
    links = commands.add_parser("links", help="Print unique upstream URLs for a link checker")
    links.add_argument("--base-ref", help="Limit URLs to project records and changelog fragments changed since this commit SHA")
    args = parser.parse_args()
    try:
        taxonomy, projects = load_catalog(ROOT)
        load_health(ROOT, projects)
        fragments = load_changelog_fragments(ROOT)
        if args.command == "links":
            selected_projects = changed_projects(ROOT, projects, args.base_ref) if args.base_ref else projects
            selected_fragments = changed_changelog_fragments(ROOT, fragments, args.base_ref) if args.base_ref else fragments
            for value in catalog_urls(selected_projects, selected_fragments):
                print(value)
        elif args.command == "validate":
            print(f"Validated {len(projects)} projects and {len(fragments)} changelog fragments.")
        elif args.command == "changelog":
            count, week = update_changelog(ROOT, args.week, fragments)
            if count:
                print(f"Compiled {count} changelog fragments into Week of {week}.")
            else:
                print("No changelog fragments to compile.")
        else:
            generated = render_readme(ROOT, taxonomy, projects)
            if args.command == "render":
                (ROOT / "README.md").write_text(generated, encoding="utf-8")
                print(f"Rendered {len(projects)} projects.")
            else:
                require(generated == (ROOT / "README.md").read_text(encoding="utf-8"),
                        "README is stale; run python3 scripts/catalog.py render")
                print(f"Validated {len(projects)} projects and {len(fragments)} changelog fragments; README is up to date.")
    except (CatalogError, OSError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
