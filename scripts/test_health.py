# SPDX-License-Identifier: MIT
"""Health observations must preserve evidence without inventing maintenance claims."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request

import catalog
import health


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.repository = "https://github.com/example/project"
        self.today = datetime.now(timezone.utc).date().isoformat()
        self.yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        self.metadata = {"html_url": self.repository, "archived": False, "disabled": False,
                         "private": False, "pushed_at": "2026-01-01T12:00:00Z"}
        self.previous = health.observe(self.repository, None, self.yesterday, lambda _: self.metadata)

    def observe(self, metadata=None, previous=None):
        return health.observe(self.repository, previous, self.today,
                              lambda _: self.metadata if metadata is None else metadata)

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
        rendered = "\n".join(catalog.health_lines({"repository": self.repository, "last_reviewed": self.yesterday}, record))
        self.assertIn("Repository redirect observed", rendered)
        self.assertIn(canonical, rendered)

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
                for field in ["last_successful_check", "last_push", "canonical_repository", "archived", "disabled"]:
                    self.assertEqual(record[field], self.previous[field])

    def test_network_failures_preserve_success(self):
        for error in [URLError("offline"), TimeoutError(), OSError("network")]:
            with self.subTest(error=type(error).__name__):
                record = self.failed(error, self.previous)
                self.assertEqual(record["status"], "check-failed")
                self.assertEqual(record["last_push"], self.previous["last_push"])
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
        rendered = "\n".join(catalog.health_lines({"repository": self.repository, "last_reviewed": self.yesterday}, record))
        self.assertIn("check failed", rendered)
        self.assertNotIn("Archived:", rendered)

    def test_failed_check_renders_prior_observations_as_retained(self):
        record = self.failed(URLError("offline"), self.previous)
        rendered = "\n".join(catalog.health_lines({"repository": self.repository, "last_reviewed": self.yesterday}, record))
        self.assertIn("retained from the last successful check on " + self.yesterday, rendered)
        self.assertIn("Last observed push", rendered)

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
            self.assertEqual(catalog.load_health(root, [{"id": "example", "repository": self.repository}]),
                             {"example": self.previous})
            self.assertEqual(catalog.load_health(root, [{"id": "example", "repository": "https://github.com/new/repo"}]), {})

    def test_missing_snapshot_is_allowed_for_new_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(catalog.load_health(Path(directory), []), {})
        rendered = "\n".join(catalog.health_lines({"last_reviewed": self.yesterday}, None))
        self.assertIn("not checked yet", rendered)

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
            project = catalog.read_json(catalog.ROOT / "examples/project.json")
            project.update(repository=self.repository, last_reviewed=self.yesterday)
            project_path = root / "data/projects" / (project["id"] + ".json")
            project_path.write_text(json.dumps(project), encoding="utf-8")
            readme = root / "README.md"
            readme.write_text(f"# Fixture\n\n{catalog.START}\n\n{catalog.END}\n", encoding="utf-8")
            taxonomy, projects = catalog.load_catalog(root)
            readme.write_text(catalog.render_readme(root, taxonomy, projects), encoding="utf-8")
            snapshot = {project["id"]: self.observe()}
            health.write_snapshot(root / "data/health.json", snapshot)
            output = io.StringIO()
            with patch.object(catalog, "ROOT", root), patch("sys.argv", ["catalog.py", "check"]), \
                    patch("sys.stdout", output), patch("sys.stderr", output):
                self.assertEqual(catalog.main(), 1)
            self.assertIn("README is stale", output.getvalue())
            rendered = catalog.render_readme(root, taxonomy, projects)
            self.assertIn("Documentation reviewed: " + self.yesterday, rendered)
            self.assertIn("Last observed push: 2026-01-01", rendered)
            readme.write_text(rendered, encoding="utf-8")
            self.assertEqual(catalog.render_readme(root, taxonomy, projects), rendered)
            self.assertEqual(catalog.read_json(project_path), project)
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


if __name__ == "__main__":
    unittest.main()
