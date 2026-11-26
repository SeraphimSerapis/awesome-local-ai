# SPDX-License-Identifier: MIT
"""Unit tests for the read-only compliance, staleness, and PR triage auditor."""

import base64
from datetime import date
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import audit  # noqa: E402
import catalog  # noqa: E402
import health  # noqa: E402

SHA_A = "a" * 40
SHA_B = "b" * 40
TODAY = date(2026, 11, 26)


def make_taxonomy():
    return {
        "categories": {
            "inference": "Inference and serving",
            "skills": "Agent skills and extensions",
        },
        "use_cases": {
            "serve-models": "Run a model on my hardware",
            "unused-case": "Unused task",
        },
        "platforms": {
            "linux": "Linux",
            "macos": "macOS",
        },
        "hardware": {
            "cpu": "CPU",
            "apple-silicon": "Apple Silicon",
        },
        "local_modes": {
            "local": "Local workload",
            "local-client": "Local client or agent",
        },
    }


def make_project(
    pid="tool-one",
    name="Tool One",
    owner="alice",
    repo="tool-one",
    sha=SHA_A,
    spdx="MIT",
    last_reviewed="2026-11-20",
    limitations=None,
    category="inference",
    use_cases=None,
    platforms=None,
    hardware=None,
):
    repository = f"https://github.com/{owner}/{repo}"
    return {
        "id": pid,
        "name": name,
        "repository": repository,
        "description": "Runs local models cleanly on user-controlled hardware.",
        "category": category,
        "use_cases": ["serve-models"] if use_cases is None else use_cases,
        "platforms": ["linux"] if platforms is None else platforms,
        "hardware": ["cpu"] if hardware is None else hardware,
        "local_mode": "local",
        "compatibility": ["OpenAI-compatible API"],
        "limitations": ["Requires 8 GB RAM."] if limitations is None else limitations,
        "license": {
            "spdx": spdx,
            "url": f"https://raw.githubusercontent.com/{owner}/{repo}/{sha}/LICENSE",
        },
        "sources": [
            {
                "url": f"https://raw.githubusercontent.com/{owner}/{repo}/{sha}/README.md",
                "note": "Primary README documenting local setup and requirements.",
            }
        ],
        "last_reviewed": last_reviewed,
    }


def make_health(repository, checked_at="2026-11-24", last_commit="2026-11-22T10:00:00Z", **overrides):
    record = {
        "repository": repository,
        "checked_at": checked_at,
        "status": "reachable",
        "detail": None,
        "last_successful_check": checked_at,
        "canonical_repository": repository,
        "archived": False,
        "disabled": False,
        "last_push": last_commit,
        "last_default_branch_commit": last_commit,
    }
    record.update(overrides)
    return record


def make_workspace(root, projects, health_map=None, taxonomy=None, fragments=None):
    (root / "data/projects").mkdir(parents=True, exist_ok=True)
    (root / "changelog.d").mkdir(parents=True, exist_ok=True)
    (root / "data/taxonomy.json").write_text(
        json.dumps(taxonomy or make_taxonomy(), indent=2) + "\n", encoding="utf-8"
    )
    for project in projects:
        (root / "data/projects" / f'{project["id"]}.json').write_text(
            json.dumps(project, indent=2) + "\n", encoding="utf-8"
        )
    if health_map is not None:
        (root / "data/health.json").write_text(
            json.dumps(health_map, indent=2) + "\n", encoding="utf-8"
        )
    if fragments:
        for slug, payload in fragments.items():
            (root / "changelog.d" / f"{slug}.json").write_text(
                json.dumps(payload, indent=2) + "\n", encoding="utf-8"
            )
    (root / "CHANGELOG.md").write_text("# Weekly catalog changelog\n", encoding="utf-8")
    (root / "README.md").write_text(f"# Fixture\n\n{catalog.START}\n\n{catalog.END}\n", encoding="utf-8")


def b64_file(text):
    return {
        "type": "file",
        "encoding": "base64",
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
    }


class FakeGitHubClient:
    def __init__(self, repos):
        self.repos = repos

    def get_repo(self, owner_repo):
        entry = self.repos.get(owner_repo)
        if entry is None:
            return None, 404
        if "raise" in entry:
            raise entry["raise"]
        if "http_status" in entry:
            return None, entry["http_status"]
        return entry["meta"], 200

    def get_commits(self, owner_repo, branch, per_page=100):
        entry = self.repos[owner_repo]
        return entry.get("commits", []), entry.get("commits_headers", {})

    def get_commits_by_path(self, api_path):
        for entry in self.repos.values():
            by_path = entry.get("commits_by_path", {})
            if api_path in by_path:
                return by_path[api_path], {}
        return [], {}

    def get_root_tree(self, owner_repo, branch):
        return self.repos[owner_repo].get("tree")

    def compare(self, owner_repo, base_sha, head_branch):
        compares = self.repos[owner_repo].get("compares", {})
        if base_sha not in compares:
            return None, 404
        val = compares[base_sha]
        if isinstance(val, int):
            return None, val
        return val, 200

    def get_contents(self, owner_repo, file_path, ref):
        return self.repos[owner_repo].get("contents", {}).get((ref, file_path))

    def get_contents_list(self, owner_repo, dir_path, ref):
        return self.repos[owner_repo].get("contents_list", {}).get((ref, dir_path))

    def get_latest_release(self, owner_repo):
        return self.repos[owner_repo].get("latest_release")

    def get_tags(self, owner_repo, per_page=1):
        return self.repos[owner_repo].get("tags", [])

    def get_releases(self, owner_repo, per_page=10):
        return self.repos[owner_repo].get("releases", [])

    def get_contributors(self, owner_repo, per_page=5):
        return self.repos[owner_repo].get("contributors", [])


def healthy_repo_fixture(owner="alice", repo="tool-one", sha=SHA_A, readme="Clean local tool.\n", **overrides):
    fixture = {
        "meta": {
            "html_url": f"https://github.com/{owner}/{repo}",
            "private": False,
            "archived": False,
            "disabled": False,
            "fork": False,
            "size": 120,
            "pushed_at": "2026-11-24T10:00:00Z",
            "created_at": "2026-06-01T00:00:00Z",
            "default_branch": "main",
            "stargazers_count": 42,
            "forks_count": 5,
            "license": {"spdx_id": "MIT"},
        },
        "commits": [
            {"commit": {"committer": {"date": "2026-11-24T10:00:00Z"}}},
            {"commit": {"committer": {"date": "2026-10-01T10:00:00Z"}}},
        ],
        "commits_headers": {},
        "tree": {
            "tree": [
                {"path": "LICENSE", "type": "blob"},
                {"path": "README.md", "type": "blob"},
            ]
        },
        "compares": {sha: {"ahead_by": 2}},
        "contents": {
            (sha, "LICENSE"): b64_file("MIT License"),
            (sha, "README.md"): b64_file(readme),
            ("main", "README.md"): b64_file(readme),
        },
        "contents_list": {("main", ".github/workflows"): [{"name": "ci.yml"}]},
        "latest_release": {"tag_name": "v1.2.0"},
        "tags": [{"name": "v1.2.0"}],
        "releases": [{"tag_name": "v1.2.0"}, {"tag_name": "v1.1.0"}],
        "contributors": [{"login": owner}, {"login": "bob"}],
    }
    fixture.update(overrides)
    return fixture


class AuditTests(unittest.TestCase):
    def test_offline_checks_surface_taxonomy_health_and_staleness(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(pid="tool-one", owner="alice", repo="tool-one", last_reviewed="2026-08-01")
            p2 = make_project(pid="tool-two", name="Tool Two", owner="alice", repo="tool-two", last_reviewed="2026-11-20")
            health_map = {
                "tool-one": make_health(
                    p1["repository"],
                    checked_at="2026-11-01",
                    last_commit="2026-05-01T00:00:00Z",
                ),
            }
            make_workspace(root, [p1, p2], health_map=health_map)
            report = audit.run_audit(root=root, today=TODAY, offline=True)
            checks = {(f["severity"], f["scope"], f["check"]) for f in report["findings"]}
            self.assertIn(("INFO", "catalog", "taxonomy-empty-category"), checks)
            self.assertIn(("WARN", "catalog", "taxonomy-unused"), checks)
            self.assertIn(("INFO", "catalog", "companion-repos"), checks)
            self.assertIn(("WARN", "tool-two", "health-missing"), checks)
            self.assertIn(("WARN", "tool-one", "health-stale"), checks)
            self.assertIn(("ERROR", "tool-one", "stale-commit"), checks)
            self.assertIn(("WARN", "tool-one", "stale-review"), checks)
            self.assertEqual(report["summary"]["projects_checked"], 0)

    def test_live_clean_project_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tax = {
                "categories": {"inference": "Inference"},
                "use_cases": {"serve-models": "Serve"},
                "platforms": {"linux": "Linux"},
                "hardware": {"cpu": "CPU"},
                "local_modes": {"local": "Local", "local-client": "Client"},
            }
            p1 = make_project(pid="tool-one", owner="alice", repo="tool-one")
            p2 = make_project(pid="tool-two", name="Tool Two", owner="bob", repo="tool-two")
            health_map = {
                "tool-one": make_health(p1["repository"]),
                "tool-two": make_health(p2["repository"]),
            }
            make_workspace(root, [p1, p2], health_map=health_map, taxonomy=tax)
            client = FakeGitHubClient({
                "alice/tool-one": healthy_repo_fixture("alice", "tool-one"),
                "bob/tool-two": healthy_repo_fixture("bob", "tool-two"),
            })
            report = audit.run_audit(root=root, client=client, today=TODAY)
            self.assertEqual(report["summary"]["errors"], 0)
            self.assertEqual(report["summary"]["warnings"], 0)
            self.assertEqual(report["summary"]["projects_checked"], 2)

    def test_live_flags_archived_disabled_redirect_fork_and_license_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(pid="tool-one", owner="alice", repo="tool-one", spdx="MIT")
            make_workspace(root, [p1], health_map={"tool-one": make_health(p1["repository"])})
            fixture = healthy_repo_fixture("alice", "tool-one")
            fixture["meta"].update(
                archived=True,
                disabled=True,
                fork=True,
                html_url="https://github.com/alice/renamed-tool",
                license={"spdx_id": "Apache-2.0"},
            )
            report = audit.run_audit(root=root, client=FakeGitHubClient({"alice/tool-one": fixture}), today=TODAY)
            checks = {(f["severity"], f["check"]) for f in report["findings"]}
            self.assertIn(("ERROR", "archived"), checks)
            self.assertIn(("ERROR", "disabled"), checks)
            self.assertIn(("ERROR", "redirect"), checks)
            self.assertIn(("WARN", "fork"), checks)
            self.assertIn(("WARN", "license-drift"), checks)

            agpl_proj = make_project(pid="agpl-tool", name="AGPL Tool", owner="bob", repo="agpl-tool", spdx="AGPL-3.0-only")
            make_workspace(root, [agpl_proj], health_map={"agpl-tool": make_health(agpl_proj["repository"])})
            agpl_fix = healthy_repo_fixture("bob", "agpl-tool")
            agpl_fix["meta"]["license"] = {"spdx_id": "AGPL-3.0"}
            agpl_report = audit.run_audit(root=root, client=FakeGitHubClient({"bob/agpl-tool": agpl_fix}), today=TODAY)
            agpl_checks = {(f["severity"], f["check"]) for f in agpl_report["findings"]}
            self.assertNotIn(("WARN", "license-drift"), agpl_checks)

    def test_live_14_day_history_link_pagination_and_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p_short = make_project(pid="short-repo", name="Short", owner="alice", repo="short")
            p_paged = make_project(pid="paged-repo", name="Paged", owner="bob", repo="paged")
            p_numeric = make_project(pid="numeric-repo", name="Numeric", owner="carol", repo="numeric")
            make_workspace(
                root,
                [p_short, p_paged, p_numeric],
                health_map={
                    "short-repo": make_health(p_short["repository"]),
                    "paged-repo": make_health(p_paged["repository"]),
                    "numeric-repo": make_health(p_numeric["repository"]),
                },
            )
            short_fix = healthy_repo_fixture("alice", "short")
            short_fix["meta"]["created_at"] = "2026-11-20T00:00:00Z"
            short_fix["commits"] = [
                {"commit": {"committer": {"date": "2026-11-24T12:00:00Z"}}},
                {"commit": {"committer": {"date": "2026-11-24T08:00:00Z"}}},
            ]
            paged_fix = healthy_repo_fixture("bob", "paged")
            paged_fix["commits"] = [
                {"commit": {"committer": {"date": "2026-11-24T12:00:00Z"}}},
                {"commit": {"committer": {"date": "2026-11-23T08:00:00Z"}}},
            ]
            paged_fix["commits_headers"] = {
                "link": '<https://api.github.com/repos/bob/paged/commits?sha=main&per_page=100&page=5>; rel="last"'
            }
            paged_fix["commits_by_path"] = {
                "repos/bob/paged/commits?sha=main&per_page=100&page=5": [
                    {"commit": {"committer": {"date": "2026-09-01T08:00:00Z"}}}
                ]
            }
            numeric_fix = healthy_repo_fixture("carol", "numeric")
            numeric_fix["meta"]["id"] = 1410331061
            numeric_fix["commits"] = [
                {"commit": {"committer": {"date": "2026-11-24T12:00:00Z"}}},
                {"commit": {"committer": {"date": "2026-11-24T08:00:00Z"}}},
            ]
            numeric_fix["commits_headers"] = {
                "link": '<https://api.github.com/repositories/1410331061/commits?sha=main&per_page=100&page=12>; rel="last"'
            }
            numeric_fix["commits_by_path"] = {
                "repositories/1410331061/commits?sha=main&per_page=100&page=12": [
                    {"commit": {"committer": {"date": "2026-08-15T08:00:00Z"}}}
                ]
            }
            client = FakeGitHubClient({
                "alice/short": short_fix,
                "bob/paged": paged_fix,
                "carol/numeric": numeric_fix,
            })
            report = audit.run_audit(root=root, client=client, today=TODAY)
            short_checks = {(f["severity"], f["check"]) for f in report["findings"] if f["scope"] == "short-repo"}
            paged_checks = {(f["severity"], f["check"]) for f in report["findings"] if f["scope"] == "paged-repo"}
            numeric_checks = {(f["severity"], f["check"]) for f in report["findings"] if f["scope"] == "numeric-repo"}
            self.assertIn(("ERROR", "history-age"), short_checks)
            self.assertIn(("ERROR", "commit-span"), short_checks)
            self.assertIn(("ERROR", "commit-days"), short_checks)
            self.assertNotIn(("ERROR", "commit-span"), paged_checks)
            self.assertNotIn(("ERROR", "commit-days"), paged_checks)
            self.assertNotIn(("ERROR", "commit-span"), numeric_checks)
            self.assertNotIn(("ERROR", "commit-days"), numeric_checks)

    def test_live_root_license_notice_pinned_sha_release_and_disclosures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(
                pid="drifted",
                owner="alice",
                repo="drifted",
                sha=SHA_A,
                last_reviewed="2026-07-01",
                limitations=["Requires macOS."],
            )
            make_workspace(root, [p1], health_map={"drifted": make_health(p1["repository"])})
            fixture = healthy_repo_fixture(
                "alice",
                "drifted",
                sha=SHA_A,
                readme="This preview build collects telemetry and checks for updates daily using Commons Clause sounds.",
            )
            fixture["tree"] = {"tree": [{"path": "README.md", "type": "blob"}, {"path": "NOTICE", "type": "blob"}]}
            fixture["compares"] = {SHA_A: {"ahead_by": 150}}
            fixture["contents"].pop((SHA_A, "LICENSE"))
            fixture["latest_release"] = {"tag_name": "v0.0.0"}
            fixture["commits"] = [
                {"commit": {"committer": {"date": "2026-08-01T00:00:00Z"}}},
                {"commit": {"committer": {"date": "2026-06-01T00:00:00Z"}}},
            ]
            report = audit.run_audit(root=root, client=FakeGitHubClient({"alice/drifted": fixture}), today=TODAY)
            by_check = {f["check"]: f for f in report["findings"] if f["scope"] == "drifted"}
            self.assertEqual(by_check["root-license"]["severity"], "ERROR")
            self.assertEqual(by_check["root-notice"]["severity"], "INFO")
            self.assertEqual(by_check["sha-drift"]["severity"], "WARN")
            self.assertEqual(by_check["review-drift"]["severity"], "WARN")
            self.assertEqual(by_check["pinned-file"]["severity"], "ERROR")
            self.assertEqual(by_check["release-tag"]["severity"], "ERROR")
            self.assertEqual(by_check["stale-commit"]["severity"], "WARN")
            self.assertEqual(by_check["disclosure-scan"]["severity"], "INFO")
            self.assertIn("telemetry", by_check["disclosure-scan"]["message"])
            self.assertIn("update", by_check["disclosure-scan"]["message"])
            self.assertIn("commons clause", by_check["disclosure-scan"]["message"])

    def test_disclosure_scan_suppresses_already_disclosed_terms(self):
        undisclosed = audit.scan_disclosure_keywords(
            ["Preview release with optional telemetry and API key support."],
            ["Early preview release; optional telemetry can be disabled; optional API key for remote endpoints."],
        )
        self.assertEqual(undisclosed, [])

    def test_companion_adoption_signals_and_output_formats(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(pid="alpha", name="Alpha", owner="shared", repo="alpha")
            p2 = make_project(pid="beta", name="Beta", owner="shared", repo="beta")
            make_workspace(
                root,
                [p1, p2],
                health_map={"alpha": make_health(p1["repository"]), "beta": make_health(p2["repository"])},
            )
            client = FakeGitHubClient({
                "shared/alpha": healthy_repo_fixture("shared", "alpha"),
                "shared/beta": healthy_repo_fixture("shared", "beta"),
            })
            report = audit.run_audit(root=root, client=client, today=TODAY)
            self.assertIn("shared", report["companion_groups"])
            self.assertEqual(len(report["companion_groups"]["shared"]), 2)
            text_out = audit.format_text(report)
            md_out = audit.format_markdown(report)
            json_out = json.loads(audit.format_json(report))
            self.assertIn("Companion-repo adoption signals:", text_out)
            self.assertIn("### Companion-repo adoption signals", md_out)
            self.assertEqual(len(json_out["companion_groups"]["shared"]), 2)
            self.assertNotIn("\u2014", text_out)
            self.assertNotIn("\u2014", md_out)

    def test_base_ref_pr_fragment_hygiene_warnings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(pid="tool-one", owner="alice", repo="tool-one")
            make_workspace(root, [p1], health_map={"tool-one": make_health(p1["repository"])})
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=root, check=True)
            base_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            p2 = make_project(pid="tool-two", name="Tool Two", owner="bob", repo="tool-two")
            (root / "data/projects/tool-two.json").write_text(json.dumps(p2), encoding="utf-8")
            (root / "CHANGELOG.md").write_text("# Weekly catalog changelog\n\n## Week of 2026-11-23\n\n### Added\n\n- Manual edit.\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add tool-two without fragment"], cwd=root, check=True)
            report = audit.run_audit(root=root, today=TODAY, base_ref=base_sha, offline=True)
            checks = {f["check"] for f in report["findings"]}
            self.assertIn("pr-changelog-fragment", checks)
            self.assertIn("pr-changelog-direct-edit", checks)

    def test_standalone_repo_triage_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(pid="tool-one", owner="alice", repo="tool-one")
            make_workspace(root, [p1], health_map={"tool-one": make_health(p1["repository"])})
            client = FakeGitHubClient({
                "alice/candidate": healthy_repo_fixture("alice", "candidate", readme="Uses optional telemetry.")
            })
            report = audit.run_audit(
                root=root,
                client=client,
                today=TODAY,
                repo_url="https://github.com/alice/candidate",
            )
            checks = {(f["severity"], f["check"]) for f in report["findings"]}
            self.assertIn(("WARN", "companion-repos"), checks)
            self.assertIn(("INFO", "disclosure-scan"), checks)
            self.assertEqual(report["summary"]["errors"], 0)
            self.assertEqual(report["summary"]["projects_checked"], 1)

    def test_cli_exit_codes_clean_strict_error_and_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(pid="tool-one", owner="alice", repo="tool-one")
            make_workspace(root, [p1], health_map={})
            out = io.StringIO()
            with patch.object(catalog, "ROOT", root), patch("sys.stdout", out), patch("sys.stderr", out):
                # Missing health -> WARN only -> 0 without --strict, 1 with --strict
                self.assertEqual(audit.main(["--offline", "--format", "json"]), 0)
                self.assertEqual(audit.main(["--offline", "--strict"]), 1)
                # Invalid args -> exit 2
                self.assertEqual(audit.main(["--warn-stale-days", "200", "--fail-stale-days", "100"]), 2)
                self.assertEqual(audit.main(["--repo", "https://github.com/a/b", "--project", "tool-one"]), 2)
                self.assertEqual(audit.main(["--base-ref", "not-a-sha"]), 2)

        # Runtime API error (HTTP 403 rate limit) -> exit 2
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            p1 = make_project(pid="tool-one", owner="alice", repo="tool-one")
            make_workspace(root, [p1], health_map={"tool-one": make_health(p1["repository"])})
            err_403 = HTTPError("https://api.github.com/repos/alice/tool-one", 403, "rate limit", {}, None)
            out = io.StringIO()
            try:
                with patch.object(catalog, "ROOT", root), \
                        patch.object(health, "github_api_with_headers", side_effect=err_403), \
                        patch("sys.stdout", out), patch("sys.stderr", out):
                    self.assertEqual(audit.main([]), 2)
            finally:
                err_403.close()


if __name__ == "__main__":
    unittest.main()
