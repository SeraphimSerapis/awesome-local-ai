# SPDX-License-Identifier: MIT
"""Health observations must preserve evidence without inventing maintenance claims."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import catalog  # noqa: E402
import health  # noqa: E402


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.repository = "https://github.com/example/project"
        self.today = datetime.now(timezone.utc).date().isoformat()
        self.yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        self.metadata = {"html_url": self.repository, "archived": False, "disabled": False,
                         "private": False, "pushed_at": "2026-01-01T12:00:00Z",
                         "default_branch": "main", "size": 42}
        self.commit_date = "2026-01-01T12:00:00Z"
        self.previous = health.observe(
            self.repository, None, self.yesterday,
            lambda _: self.metadata, lambda _repo, _branch: self.commit_date,
        )

    def observe(self, metadata=None, previous=None, fetch_commit=False):
        target = self.metadata if metadata is None else metadata
        commit_loader = (
            (lambda _repo, _branch: self.commit_date)
            if fetch_commit is False
            else fetch_commit
        )
        return health.observe(self.repository, previous, self.today, lambda _: target, commit_loader)

    def failed(self, error, previous=None):
        def fetch(_):
            raise error
        return health.observe(self.repository, previous, self.today, fetch)

    def test_success_records_facts_and_date(self):
        record = self.observe()
        self.assertEqual(record["status"], "reachable")
        self.assertEqual(record["checked_at"], self.today)
        self.assertEqual(record["last_successful_check"], self.today)
        self.assertEqual(record["last_push"], self.metadata["pushed_at"])
        self.assertEqual(record["last_default_branch_commit"], self.commit_date)
        self.assertIs(record["archived"], False)
        self.assertNotIn("maintained", record)

    def test_archived_and_disabled_are_observations_not_removals(self):
        record = self.observe(dict(self.metadata, archived=True, disabled=True))
        self.assertEqual(record["status"], "reachable")
        self.assertIs(record["archived"], True)
        self.assertIs(record["disabled"], True)

    def test_rename_keeps_catalog_identity_and_records_canonical_url(self):
        canonical = "https://github.com/new-owner/renamed"
        record = self.observe(dict(self.metadata, html_url=canonical))
        self.assertEqual(record["repository"], self.repository)
        self.assertEqual(record["canonical_repository"], canonical)
        project = {
            "id": "example",
            "name": "Example",
            "repository": self.repository,
            "last_reviewed": self.yesterday,
            "compatibility": [],
            "limitations": ["Example limit."],
        }
        self.assertEqual(catalog.health_flags(project, record), ["redirected"])
        alert = catalog.category_alert_line(project, record)
        self.assertIn("Repository redirect observed", alert)
        self.assertIn(canonical, alert)
        detail = "\n".join(catalog.project_detail_lines(project, record))
        self.assertIn("Redirected to", detail)
        self.assertIn(canonical, detail)

    def test_rate_limits_auth_failures_and_server_errors_preserve_success(self):
        for code in [401, 403, 429, 500, 503]:
            with self.subTest(code=code):
                error = HTTPError("https://api.github.com/repos/example/project", code, "failure", {}, None)
                try:
                    record = self.failed(error, self.previous)
                finally:
                    error.close()
                self.assertEqual(record["status"], "check-failed")
                self.assertEqual(record["checked_at"], self.today)
                for field in [
                    "last_successful_check", "last_push", "last_default_branch_commit",
                    "canonical_repository", "archived", "disabled",
                ]:
                    self.assertEqual(record[field], self.previous[field])

    def test_network_failures_preserve_success(self):
        for error in [URLError("offline"), TimeoutError(), OSError("network")]:
            with self.subTest(error=type(error).__name__):
                record = self.failed(error, self.previous)
                self.assertEqual(record["status"], "check-failed")
                self.assertEqual(record["last_push"], self.previous["last_push"])
                self.assertEqual(record["last_default_branch_commit"], self.previous["last_default_branch_commit"])
                self.assertEqual(record["last_successful_check"], self.yesterday)

    def test_unavailable_is_not_a_claim_that_a_repository_was_deleted(self):
        for code in [404, 410, 451]:
            with self.subTest(code=code):
                error = HTTPError("https://api.github.com/repos/example/project", code, "missing", {}, None)
                try:
                    record = self.failed(error, self.previous)
                finally:
                    error.close()
                self.assertEqual(record["status"], "unavailable")
                self.assertIn("may be", record["detail"])
                self.assertEqual(record["last_successful_check"], self.yesterday)

    def test_private_repository_metadata_is_not_published(self):
        record = self.observe(dict(self.metadata, private=True, pushed_at="2026-02-01T12:00:00Z"), self.previous)
        self.assertEqual(record["status"], "unavailable")
        self.assertEqual(record["last_push"], self.previous["last_push"])
        fresh = self.observe(dict(self.metadata, private=True))
        self.assertIsNone(fresh["last_push"])

    def test_malformed_api_metadata_preserves_last_good_observation(self):
        for metadata in [[], {}, dict(self.metadata, archived="false"),
                         dict(self.metadata, html_url="https://attacker.example"),
                         dict(self.metadata, pushed_at="not a timestamp")]:
            with self.subTest(metadata=metadata):
                record = self.observe(metadata, self.previous)
                self.assertEqual(record["status"], "check-failed")
                self.assertEqual(record["last_push"], self.previous["last_push"])

    def test_changed_repository_does_not_inherit_unrelated_metadata(self):
        changed = dict(self.previous, repository="https://github.com/other/repository")
        record = self.failed(URLError("offline"), changed)
        self.assertIsNone(record["last_successful_check"])
        self.assertIsNone(record["canonical_repository"])

    def test_empty_repository_can_have_no_push_timestamp(self):
        record = self.observe(dict(self.metadata, pushed_at=None))
        self.assertEqual(record["status"], "reachable")
        self.assertIsNone(record["last_push"])

    def test_fresh_failure_does_not_invent_upstream_properties(self):
        record = self.failed(URLError("offline"))
        self.assertIsNone(record["last_successful_check"])
        self.assertIsNone(record["archived"])
        project = {
            "id": "example",
            "name": "Example",
            "repository": self.repository,
            "last_reviewed": self.yesterday,
            "compatibility": [],
            "limitations": ["Example limit."],
        }
        rendered = "\n".join(catalog.project_detail_lines(project, record))
        self.assertIn("check failed", rendered)
        self.assertNotIn("Archived", rendered)
        self.assertNotIn("Metadata retained", rendered)

    def test_failed_check_renders_prior_observations_as_retained(self):
        record = self.failed(URLError("offline"), self.previous)
        project = {
            "id": "example",
            "name": "Example",
            "repository": self.repository,
            "last_reviewed": self.yesterday,
            "compatibility": [],
            "limitations": ["Example limit."],
        }
        alert = catalog.category_alert_line(project, record)
        self.assertIn("Prior metadata retained from " + self.yesterday, alert)
        rendered = "\n".join(catalog.project_detail_lines(project, record))
        self.assertIn("Metadata retained from " + self.yesterday, rendered)
        self.assertIn("last commit 2026-01-01", rendered)

    def test_snapshot_validator_rejects_bad_types_dates_and_states(self):
        for field, value in [("status", []), ("checked_at", "20260101"), ("archived", 1),
                             ("detail", " multiline\n"), ("last_successful_check", None),
                             ("canonical_repository", "https://github.com/example/project.git"),
                             ("checked_at", (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat())]:
            with self.subTest(field=field):
                record = dict(self.previous)
                record[field] = value
                with self.assertRaises(catalog.CatalogError):
                    catalog.validate_health_record(record)

    def test_unknown_health_fields_and_non_objects_fail(self):
        for record in [[], dict(self.previous, maintained=True)]:
            with self.subTest(record=record), self.assertRaises(catalog.CatalogError):
                catalog.validate_health_record(record)

    def test_load_health_filters_removed_and_repointed_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            path = root / "data/health.json"
            path.write_text(json.dumps({"example": self.previous, "removed": self.previous}), encoding="utf-8")
            current, removed = health.load_previous_health_with_removed(
                root, [{"id": "example", "repository": self.repository}]
            )
            self.assertEqual(current, {"example": self.previous})
            self.assertEqual(removed, ["removed"])
            self.assertEqual(
                health.load_previous_health(root, [{"id": "example", "repository": self.repository}]),
                {"example": self.previous},
            )
            repointed, repointed_removed = health.load_previous_health_with_removed(
                root, [{"id": "example", "repository": "https://github.com/new/repo"}]
            )
            self.assertEqual(repointed, {})
            self.assertEqual(repointed_removed, ["example", "removed"])

    def test_missing_snapshot_is_allowed_for_new_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(catalog.load_health(Path(directory), []), {})
        project = {
            "id": "example",
            "name": "Example",
            "repository": self.repository,
            "last_reviewed": self.yesterday,
            "compatibility": [],
            "limitations": ["Example limit."],
        }
        rendered = "\n".join(catalog.project_detail_lines(project, None))
        self.assertIn("repository not checked yet", rendered)
        self.assertIn("**Not checked yet**", catalog.table_activity_cell(project, None))

    def test_refresh_prunes_removed_projects_and_does_not_mutate_inputs(self):
        projects = [{"id": "example", "repository": self.repository}]
        original = deepcopy(projects)
        previous = {"removed": self.previous, "example": self.previous}
        before = deepcopy(previous)
        observed = health.refresh(projects, previous, self.today, lambda _: self.metadata)
        self.assertEqual(set(observed), {"example"})
        self.assertEqual(projects, original)
        self.assertEqual(previous, before)

    def test_atomic_snapshot_write_and_cleanup_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "health.json"
            health.write_snapshot(path, {"example": self.previous})
            original = path.read_text(encoding="utf-8")
            with patch.object(Path, "replace", side_effect=OSError("write failed")), self.assertRaises(OSError):
                health.write_snapshot(path, {})
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_readme_check_tracks_snapshot_changes_and_rejects_invalid_health(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/projects").mkdir(parents=True)
            shutil.copy(catalog.ROOT / "data/taxonomy.json", root / "data/taxonomy.json")
            (root / "CHANGELOG.md").write_text("# Weekly catalog changelog\n", encoding="utf-8")
            project = catalog.read_json(catalog.ROOT / "examples/project.json")
            project.update(repository=self.repository, last_reviewed=self.yesterday)
            project_path = root / "data/projects" / (project["id"] + ".json")
            project_path.write_text(json.dumps(project), encoding="utf-8")
            readme = root / "README.md"
            readme.write_text(f"# Fixture\n\n{catalog.START}\n\n{catalog.END}\n", encoding="utf-8")
            taxonomy, projects = catalog.load_catalog(root)
            catalog.render_outputs(root, taxonomy, projects)
            snapshot = {project["id"]: self.observe()}
            health.write_snapshot(root / "data/health.json", snapshot)
            output = io.StringIO()
            with patch.object(catalog, "ROOT", root), patch("sys.argv", ["catalog.py", "check"]), \
                    patch("sys.stdout", output), patch("sys.stderr", output):
                self.assertEqual(catalog.main(), 1)
            self.assertIn("README is stale", output.getvalue())
            rendered = catalog.render_readme(root, taxonomy, projects)
            self.assertIn("reviewed " + self.yesterday, rendered)
            self.assertIn("2026-01-01", rendered)
            catalog.render_outputs(root, taxonomy, projects)
            self.assertEqual(catalog.render_readme(root, taxonomy, projects), rendered)
            self.assertEqual(catalog.read_json(project_path), project)
            ok_output = io.StringIO()
            with patch.object(catalog, "ROOT", root), patch("sys.argv", ["catalog.py", "check"]), \
                    patch("sys.stdout", ok_output), patch("sys.stderr", ok_output):
                self.assertEqual(catalog.main(), 0, ok_output.getvalue())
            snapshot[project["id"]]["archived"] = "false"
            health.write_snapshot(root / "data/health.json", snapshot)
            with patch.object(catalog, "ROOT", root), patch("sys.argv", ["catalog.py", "check"]), \
                    patch("sys.stdout", output), patch("sys.stderr", output):
                self.assertEqual(catalog.main(), 1)
            self.assertIn("health.archived must be a boolean", output.getvalue())

    def test_credentials_only_go_to_github_api(self):
        response = io.BytesIO(json.dumps(self.metadata).encode())
        with patch.dict(os.environ, {"GH_TOKEN": "test-token"}), patch("health.build_opener") as builder:
            builder.return_value.open.return_value = response
            self.assertEqual(health.github_metadata(self.repository), self.metadata)
            request = builder.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, "https://api.github.com/repos/example/project")
            self.assertEqual(request.headers["Authorization"], "Bearer test-token")
            self.assertEqual(builder.return_value.open.call_args.kwargs["timeout"], 20)

    def test_redirects_cannot_forward_credentials_to_other_hosts(self):
        handler = health.GitHubRedirects()
        request = Request("https://api.github.com/repos/old/name", headers={"Authorization": "Bearer test-token"})
        for target in ["https://example.com", "http://api.github.com/repos/1", "https://api.github.com:444/repos/1",
                       "https://user@api.github.com/repos/1"]:
            with self.subTest(target=target), self.assertRaises(URLError):
                handler.redirect_request(request, None, 302, "redirect", {}, target)
        redirect = handler.redirect_request(request, None, 302, "redirect", {}, "https://api.github.com/repositories/1")
        self.assertEqual(redirect.full_url, "https://api.github.com/repositories/1")

    def test_oversized_or_invalid_api_payload_fails(self):
        for payload in [b"x" * 1_000_001, b"[]", b'{"private":false,"private":true}']:
            with self.subTest(size=len(payload)), patch("health.build_opener") as builder:
                builder.return_value.open.return_value = io.BytesIO(payload)
                with self.assertRaises(ValueError):
                    health.github_metadata(self.repository)

    def test_pushed_at_newer_than_default_branch_commit_is_recorded_separately(self):
        stalled_main = "2026-09-26T10:15:00Z"
        bot_branch_push = "2026-11-14T04:25:59Z"
        record = self.observe(
            dict(self.metadata, pushed_at=bot_branch_push),
            fetch_commit=lambda _repo, branch: stalled_main if branch == "main" else None,
        )
        self.assertEqual(record["status"], "reachable")
        self.assertEqual(record["last_push"], bot_branch_push)
        self.assertEqual(record["last_default_branch_commit"], stalled_main)

    def test_github_branch_commit_quotes_branch_and_normalizes_dates(self):
        commit_payload = [{"commit": {"author": {"date": "2026-09-01T08:00:00Z"},
                                      "committer": {"date": "2026-09-26T12:15:00+02:00"}}}]
        with patch.dict(os.environ, {"GH_TOKEN": "test-token"}), patch("health.build_opener") as builder:
            builder.return_value.open.return_value = io.BytesIO(json.dumps(commit_payload).encode())
            observed = health.github_branch_commit(self.repository, "release/1.0")
            self.assertEqual(observed, "2026-09-26T10:15:00Z")
            request = builder.return_value.open.call_args.args[0]
            self.assertEqual(
                request.full_url,
                "https://api.github.com/repos/example/project/commits?sha=release%2F1.0&per_page=1",
            )
            self.assertEqual(request.headers["Authorization"], "Bearer test-token")
            self.assertEqual(request.headers["Accept"], "application/vnd.github+json")
            self.assertEqual(builder.return_value.open.call_args.kwargs["timeout"], 20)

        author_only = [{"commit": {"author": {"date": "2026-10-05T09:30:00Z"}, "committer": None}}]
        with patch("health.build_opener") as builder:
            builder.return_value.open.return_value = io.BytesIO(json.dumps(author_only).encode())
            self.assertEqual(health.github_branch_commit(self.repository, "main"), "2026-10-05T09:30:00Z")

        with patch("health.build_opener") as builder:
            builder.return_value.open.return_value = io.BytesIO(b"[]")
            self.assertIsNone(health.github_branch_commit(self.repository, "main"))

        with patch("health.build_opener") as builder:
            builder.return_value.open.return_value = io.BytesIO(b"{}")
            with self.assertRaisesRegex(catalog.CatalogError, "must be an array"):
                health.github_branch_commit(self.repository, "main")

        empty_repo_error = HTTPError(
            "https://api.github.com/repos/example/project/commits?sha=main&per_page=1", 409, "empty", {}, None
        )
        try:
            with patch("health.build_opener") as builder:
                builder.return_value.open.side_effect = empty_repo_error
                self.assertIsNone(health.github_branch_commit(self.repository, "main"))
        finally:
            empty_repo_error.close()

    def test_transient_commit_endpoint_errors_preserve_prior_default_branch_commit(self):
        newer_meta = dict(self.metadata, pushed_at="2026-11-17T18:00:00Z")
        for code in [401, 403, 404, 429, 500, 503]:
            with self.subTest(code=code):
                error = HTTPError("https://api.github.com/repos/example/project/commits/main", code, "failure", {}, None)
                try:
                    def fail_commit(_repo, _branch, exc=error):
                        raise exc
                    record = self.observe(newer_meta, previous=self.previous, fetch_commit=fail_commit)
                finally:
                    error.close()
                self.assertEqual(record["status"], "check-failed")
                self.assertEqual(record["last_push"], self.previous["last_push"])
                self.assertEqual(record["last_default_branch_commit"], self.previous["last_default_branch_commit"])
        for failure in [URLError("reset"), TimeoutError(), lambda _r, _b: "not-a-timestamp"]:
            with self.subTest(failure=failure):
                if isinstance(failure, Exception):
                    def fail_loader(_repo, _branch, exc=failure):
                        raise exc
                else:
                    fail_loader = failure
                record = self.observe(newer_meta, previous=self.previous, fetch_commit=fail_loader)
                self.assertEqual(record["status"], "check-failed")
                self.assertEqual(record["last_default_branch_commit"], self.previous["last_default_branch_commit"])
                self.assertNotIn("(", record["detail"])
                self.assertNotIn(")", record["detail"])

    def test_disabled_or_empty_repositories_skip_commit_lookup(self):
        called = []

        def unexpected_commit(repo, branch):
            called.append((repo, branch))
            return "2026-11-17T00:00:00Z"

        for overrides in [
            {"disabled": True},
            {"pushed_at": None},
            {"default_branch": None},
        ]:
            with self.subTest(overrides=overrides):
                record = self.observe(dict(self.metadata, **overrides), fetch_commit=unexpected_commit)
                self.assertEqual(record["status"], "reachable")
                self.assertIsNone(record["last_default_branch_commit"])
        self.assertEqual(called, [])

        small_repo = self.observe(
            dict(self.metadata, size=0),
            fetch_commit=lambda _repo, _branch: "2026-11-17T00:00:00Z",
        )
        self.assertEqual(small_repo["status"], "reachable")
        self.assertEqual(small_repo["last_default_branch_commit"], "2026-11-17T00:00:00Z")

    def test_legacy_health_records_without_default_branch_commit_upgrade_cleanly(self):
        legacy = dict(self.previous)
        legacy.pop("last_default_branch_commit")
        failed_record = self.failed(URLError("offline"), previous=legacy)
        self.assertEqual(failed_record["status"], "check-failed")
        self.assertIsNone(failed_record["last_default_branch_commit"])
        self.assertEqual(failed_record["last_push"], self.previous["last_push"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/health.json").write_text(json.dumps({"example": legacy}), encoding="utf-8")
            upgraded = health.load_previous_health(root, [{"id": "example", "repository": self.repository}])
            self.assertIsNone(upgraded["example"]["last_default_branch_commit"])
            refreshed = health.refresh(
                [{"id": "example", "repository": self.repository}],
                upgraded,
                self.today,
                lambda _: self.metadata,
                lambda _repo, _branch: "2026-11-17T14:19:54Z",
            )
            self.assertEqual(refreshed["example"]["last_default_branch_commit"], "2026-11-17T14:19:54Z")

    def test_render_summary_routine_with_newly_observed_removed_and_quiet(self):
        today = "2026-11-26"
        projects = [
            {"id": "active-tool", "repository": "https://github.com/example/active"},
            {"id": "new-tool", "repository": "https://github.com/example/new"},
            {"id": "quiet-tool", "repository": "https://github.com/example/quiet"},
        ]
        previous = {
            "active-tool": {
                "repository": "https://github.com/example/active",
                "checked_at": "2026-11-20",
                "status": "reachable",
                "detail": None,
                "last_successful_check": "2026-11-20",
                "canonical_repository": "https://github.com/example/active",
                "archived": False,
                "disabled": False,
                "last_push": "2026-11-20T00:00:00Z",
                "last_default_branch_commit": "2026-11-20T00:00:00Z",
            },
            "quiet-tool": {
                "repository": "https://github.com/example/quiet",
                "checked_at": "2026-11-20",
                "status": "reachable",
                "detail": None,
                "last_successful_check": "2026-11-20",
                "canonical_repository": "https://github.com/example/quiet",
                "archived": False,
                "disabled": False,
                "last_push": "2026-07-10T19:18:53Z",
                "last_default_branch_commit": "2026-07-10T19:18:40Z",
            },
        }
        observations = {
            "active-tool": dict(previous["active-tool"], checked_at=today, last_successful_check=today),
            "new-tool": {
                "repository": "https://github.com/example/new",
                "checked_at": today,
                "status": "reachable",
                "detail": None,
                "last_successful_check": today,
                "canonical_repository": "https://github.com/example/new",
                "archived": False,
                "disabled": False,
                "last_push": "2026-11-25T10:00:00Z",
                "last_default_branch_commit": "2026-11-25T10:00:00Z",
            },
            "quiet-tool": dict(previous["quiet-tool"], checked_at=today, last_successful_check=today),
        }
        summary = health.render_summary(
            projects, previous, observations, today, removed_ids=["old-tool"], quiet_days=90
        )
        self.assertIn("## Snapshot summary (2026-11-26)", summary)
        self.assertIn("Checked: 3 repositories (3 reachable, 0 unavailable, 0 check-failed)", summary)
        self.assertIn("Flagged for manual review: 0", summary)
        self.assertIn("Newly observed: 1 (`new-tool`)", summary)
        self.assertIn("Removed from snapshot: 1 (`old-tool`)", summary)
        self.assertNotIn("### Flagged entries requiring manual review", summary)
        self.assertIn("### Quiet repositories (more than 90 days since last default-branch commit)", summary)
        self.assertIn("| `quiet-tool` | 2026-07-10 | 139 |", summary)
        self.assertIn("`data/health.json`, `data/catalog.json`, and `README.md`", summary)
        self.assertNotIn("\u2014", summary)

    def test_render_summary_lists_exact_reasons_for_flagged_entries(self):
        today = "2026-11-26"
        projects = [
            {"id": "archived-tool", "repository": "https://github.com/example/archived"},
            {"id": "gone-tool", "repository": "https://github.com/example/gone"},
            {"id": "moved-tool", "repository": "https://github.com/example/old-name"},
        ]
        observations = {
            "archived-tool": {
                "repository": "https://github.com/example/archived",
                "checked_at": today,
                "status": "reachable",
                "detail": None,
                "last_successful_check": today,
                "canonical_repository": "https://github.com/example/archived",
                "archived": True,
                "disabled": True,
                "last_push": "2026-11-01T00:00:00Z",
                "last_default_branch_commit": "2026-11-01T00:00:00Z",
            },
            "gone-tool": {
                "repository": "https://github.com/example/gone",
                "checked_at": today,
                "status": "unavailable",
                "detail": "HTTP 404; repository may be missing, private, or restricted.",
                "last_successful_check": None,
                "canonical_repository": None,
                "archived": None,
                "disabled": None,
                "last_push": None,
                "last_default_branch_commit": None,
            },
            "moved-tool": {
                "repository": "https://github.com/example/old-name",
                "checked_at": today,
                "status": "reachable",
                "detail": None,
                "last_successful_check": today,
                "canonical_repository": "https://github.com/example/new-name",
                "archived": False,
                "disabled": False,
                "last_push": "2026-11-24T00:00:00Z",
                "last_default_branch_commit": "2026-11-24T00:00:00Z",
            },
        }
        summary = health.render_summary(projects, {}, observations, today)
        self.assertIn("Flagged for manual review: 3", summary)
        self.assertIn("### Flagged entries requiring manual review", summary)
        self.assertIn("| `archived-tool` | reachable | archived; disabled |", summary)
        self.assertIn("| `gone-tool` | unavailable | unavailable (HTTP 404; repository may be missing, private, or restricted.) |", summary)
        self.assertIn("| `moved-tool` | reachable | redirected to https://github.com/example/new-name |", summary)

    def test_cli_summary_file_writes_pr_body(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/projects").mkdir(parents=True)
            shutil.copy(catalog.ROOT / "data/taxonomy.json", root / "data/taxonomy.json")
            project = catalog.read_json(catalog.ROOT / "examples/project.json")
            project.update(repository=self.repository, last_reviewed=self.yesterday)
            (root / "data/projects" / (project["id"] + ".json")).write_text(
                json.dumps(project), encoding="utf-8"
            )
            (root / "data/health.json").write_text(
                json.dumps({"stale-removed": self.previous}), encoding="utf-8"
            )
            summary_path = root / "out/health-summary.md"
            output = io.StringIO()

            real_refresh = health.refresh

            def fake_refresh(projects_arg, previous_arg, today_arg):
                return real_refresh(
                    projects_arg,
                    previous_arg,
                    today_arg,
                    lambda _: self.metadata,
                    lambda _r, _b: self.commit_date,
                )

            with patch.object(catalog, "ROOT", root), \
                    patch.object(health, "refresh", side_effect=fake_refresh), \
                    patch("sys.argv", ["health.py", "--summary-file", str(summary_path)]), \
                    patch("sys.stdout", output), patch("sys.stderr", output):
                code = health.main()
            self.assertEqual(code, 0, output.getvalue())
            self.assertTrue(summary_path.is_file())
            body = summary_path.read_text(encoding="utf-8")
            self.assertIn("Newly observed: 1 (`example-project`)", body)
            self.assertIn("Removed from snapshot: 1 (`stale-removed`)", body)
            self.assertIn("`data/health.json`, `data/catalog.json`, and `README.md`", body)


if __name__ == "__main__":
    unittest.main()
