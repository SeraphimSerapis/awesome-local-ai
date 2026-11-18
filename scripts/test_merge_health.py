# SPDX-License-Identifier: MIT
"""The health merge gate must reject anything beyond a clean, tested bot refresh."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import catalog
import health
import merge_health


def checks_workflow_job_names(workflow_path):
    """Extract rendered job names from checks.yml using stdlib-only parsing."""
    in_jobs = False
    jobs = {}
    current_job = None
    in_include = False
    current_matrix_item = None
    for raw_line in workflow_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            in_jobs = stripped == "jobs:"
            current_job = None
            in_include = False
            current_matrix_item = None
            continue
        if not in_jobs:
            continue
        if indent == 2 and stripped.endswith(":"):
            current_job = stripped[:-1]
            jobs[current_job] = {"name": current_job, "include": []}
            in_include = False
            current_matrix_item = None
            continue
        if current_job is None:
            continue
        if indent == 4 and stripped.startswith("name:"):
            jobs[current_job]["name"] = stripped.removeprefix("name:").strip().strip("\"'")
            in_include = False
            current_matrix_item = None
        elif indent <= 6:
            in_include = False
            current_matrix_item = None
        elif indent == 8 and stripped == "include:":
            in_include = True
            current_matrix_item = None
        elif in_include and indent == 10 and stripped.startswith("- "):
            current_matrix_item = {}
            jobs[current_job]["include"].append(current_matrix_item)
            key, value = stripped[2:].split(":", 1)
            current_matrix_item[key.strip()] = value.strip().strip("\"'")
        elif in_include and indent == 12 and current_matrix_item is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_matrix_item[key.strip()] = value.strip().strip("\"'")
    names = set()
    for info in jobs.values():
        template = info["name"]
        if info["include"]:
            for entry in info["include"]:
                rendered = re.sub(
                    r"\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}",
                    lambda match: entry[match.group(1)],
                    template,
                )
                names.add(rendered)
        else:
            names.add(template)
    return names


class MergePolicyTests(unittest.TestCase):
    def setUp(self):
        self.repository = "example/catalog"
        self.sha = "a" * 40
        self.run = {"id": 123, "head_repository": {"full_name": self.repository},
                    "head_branch": merge_health.BRANCH, "head_sha": self.sha,
                    "event": "workflow_dispatch", "path": ".github/workflows/checks.yml",
                    "status": "completed", "conclusion": "success"}
        self.jobs = [{"name": name, "status": "completed", "conclusion": "success"}
                     for name in sorted(merge_health.REQUIRED_JOBS)]
        self.pr = {"number": 4, "state": "open", "draft": False, "user": {"login": "github-actions[bot]"},
                   "head": {"repo": {"full_name": self.repository}, "ref": merge_health.BRANCH, "sha": self.sha},
                   "base": {"repo": {"full_name": self.repository}, "ref": "main"}}

    def test_successful_run_and_bot_pr_are_eligible(self):
        merge_health.validate_run(self.run, self.jobs, self.repository)
        merge_health.validate_pr(self.pr, self.sha, self.repository, "main")

    def test_required_jobs_match_checks_workflow_job_names(self):
        workflow_names = checks_workflow_job_names(catalog.ROOT / ".github/workflows/checks.yml")
        self.assertEqual(
            workflow_names,
            {
                "Catalog / ubuntu-latest / Python 3.11",
                "Catalog / windows-latest / Python 3.13",
                "Documentation",
                "Upstream links",
            },
        )
        self.assertEqual(merge_health.REQUIRED_JOBS, workflow_names - {"Upstream links"})

    def test_run_provenance_and_sha_are_required(self):
        for field, value in [("head_repository", {"full_name": "attacker/fork"}),
                             ("head_branch", "submission"), ("event", "pull_request"),
                             ("path", ".github/workflows/other.yml"), ("status", "in_progress"),
                             ("conclusion", "failure"), ("head_sha", "--help")]:
            with self.subTest(field=field), self.assertRaises(catalog.CatalogError):
                merge_health.validate_run(dict(self.run, **{field: value}), self.jobs, self.repository)

    def test_green_run_does_not_replace_missing_or_failed_job_checks(self):
        cases = [self.jobs[:-1]]
        for conclusion in ["failure", "skipped", "cancelled", "neutral", None]:
            jobs = deepcopy(self.jobs)
            jobs[0]["conclusion"] = conclusion
            cases.append(jobs)
        cases.append(self.jobs + [{"name": "Additional check", "status": "completed", "conclusion": "failure"}])
        cases.append([dict(job, status="in_progress") for job in self.jobs])
        for jobs in cases:
            with self.subTest(jobs=jobs), self.assertRaises(catalog.CatalogError):
                merge_health.validate_run(self.run, jobs, self.repository)

    def test_only_current_same_repo_bot_pr_is_eligible(self):
        cases = [dict(self.pr, state="closed"), dict(self.pr, draft=True),
                 dict(self.pr, user={"login": "contributor"})]
        for side, field, value in [("head", "repo", {"full_name": "attacker/fork"}),
                                   ("base", "repo", {"full_name": "other/catalog"}),
                                   ("head", "ref", "submission"), ("base", "ref", "other"),
                                   ("head", "sha", "b" * 40)]:
            pr = deepcopy(self.pr)
            pr[side][field] = value
            cases.append(pr)
        for pr in cases:
            with self.subTest(pr=pr), self.assertRaises(catalog.CatalogError):
                merge_health.validate_pr(pr, self.sha, self.repository, "main")

    def run_main(self, *, stale_base=False, moved_head=False, extra_jobs=False, unsafe_content=False, run_id="123"):
        event = {"repository": {"default_branch": "main"}}
        jobs = {"total_count": len(self.jobs) + int(extra_jobs), "jobs": self.jobs}
        current_pr = deepcopy(self.pr)
        if moved_head:
            current_pr["head"]["sha"] = "b" * 40
        responses = [self.run, jobs, [self.pr], {"object": {"sha": "changed" if stale_base else "base"}}, current_pr]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "event.json"
            path.write_text(json.dumps(event), encoding="utf-8")
            with patch.dict(os.environ, {"GITHUB_REPOSITORY": self.repository, "GITHUB_EVENT_PATH": str(path),
                                         "HEALTH_CI_RUN_ID": run_id}), \
                    patch("merge_health.api", side_effect=responses), \
                    patch("merge_health.validate_content", return_value="base",
                          side_effect=catalog.CatalogError("unsafe content") if unsafe_content else None), \
                    patch("merge_health.command") as command, patch("sys.stdout", io.StringIO()), \
                    patch("sys.stderr", io.StringIO()):
                result = merge_health.main()
                return result, command.call_args_list

    def test_main_merges_only_tested_head_without_bypassing_protection(self):
        result, calls = self.run_main()
        self.assertEqual(result, 0)
        self.assertEqual(calls[-1].args, ("gh", "pr", "merge", "4", "--repo", self.repository,
                                         "--merge", "--match-head-commit", self.sha))

    def test_invalid_dispatch_run_id_blocks_before_any_command(self):
        for run_id in ["", "null", "0", "../other", "123?query"]:
            with self.subTest(run_id=run_id):
                result, calls = self.run_main(run_id=run_id)
                self.assertEqual(result, 1)
                self.assertEqual(calls, [])

    def test_main_never_merges_when_base_or_head_moves_or_jobs_are_truncated(self):
        for options in [{"stale_base": True}, {"moved_head": True}, {"extra_jobs": True}, {"unsafe_content": True}]:
            with self.subTest(options=options):
                result, calls = self.run_main(**options)
                self.assertEqual(result, 1)
                self.assertFalse(any(call.args[:3] == ("gh", "pr", "merge") for call in calls))


@unittest.skipUnless(shutil.which("git"), "Git is needed for merge-gate integration tests")
class MergeContentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "data/projects").mkdir(parents=True)
        shutil.copy(catalog.ROOT / "data/taxonomy.json", self.root / "data/taxonomy.json")
        self.today = datetime.now(timezone.utc).date().isoformat()
        self.yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        self.project = catalog.read_json(catalog.ROOT / "examples/project.json")
        self.project["last_reviewed"] = self.yesterday
        self.project_path = self.root / "data/projects" / (self.project["id"] + ".json")
        self.project_path.write_text(json.dumps(self.project), encoding="utf-8")
        metadata = {"html_url": self.project["repository"], "private": False,
                    "archived": False, "disabled": False, "pushed_at": None}
        self.record = health.observe(self.project["repository"], None, self.today, lambda _: metadata)
        self.snapshot = {self.project["id"]: self.record}
        self.readme = self.root / "README.md"
        self.readme.write_text(f"# Fixture\n\nManual text.\n\n{catalog.START}\n\n{catalog.END}\n", encoding="utf-8")
        self.write_snapshot({self.project["id"]: dict(self.record, checked_at=self.yesterday,
                                                    last_successful_check=self.yesterday)})
        self.git("init", "-q")
        self.commit("base")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return merge_health.command("git", *args, root=self.root)

    def commit(self, message):
        self.git("add", ".")
        self.git("-c", "user.name=Health tests", "-c", "user.email=tests@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", message)

    def write_snapshot(self, snapshot):
        health.write_snapshot(self.root / "data/health.json", snapshot)
        taxonomy, projects = catalog.load_catalog(self.root)
        self.readme.write_text(catalog.render_readme(self.root, taxonomy, projects), encoding="utf-8")

    def candidate(self):
        self.commit("refresh")
        sha = self.git("rev-parse", "HEAD").strip()
        self.git("checkout", "--force", "--detach", self.base)
        return sha

    def test_fresh_complete_snapshot_and_exact_render_pass_without_checkout(self):
        self.write_snapshot(self.snapshot)
        sha = self.candidate()
        self.assertEqual(merge_health.validate_content(self.root, sha, self.today), self.base)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)

    def test_unavailable_failed_archived_disabled_redirected_and_stale_records_block(self):
        for changes in [{"status": "unavailable", "detail": "HTTP 404"},
                        {"status": "check-failed", "detail": "Timeout"},
                        {"archived": True}, {"disabled": True},
                        {"canonical_repository": "https://github.com/renamed/project"},
                        {"checked_at": self.yesterday, "last_successful_check": self.yesterday},
                        {"repository": "https://github.com/different/project"},
                        {"archived": "false"}]:
            snapshot = {self.project["id"]: dict(self.record, **changes)}
            with self.subTest(changes=changes), self.assertRaises(catalog.CatalogError):
                merge_health.validate_snapshot(snapshot, [self.project], self.today)

    def test_snapshot_cannot_omit_or_add_projects(self):
        for snapshot in [{}, dict(self.snapshot, extra=self.record), []]:
            with self.subTest(snapshot=snapshot), self.assertRaises(catalog.CatalogError):
                merge_health.validate_snapshot(snapshot, [self.project], self.today)

    def test_code_catalog_and_workflow_changes_block(self):
        for path in ["scripts/untrusted.py", "data/projects/extra.json", ".github/workflows/extra.yml"]:
            with self.subTest(path=path):
                self.write_snapshot(self.snapshot)
                extra = self.root / path
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_text("untrusted content", encoding="utf-8")
                sha = self.candidate()
                with self.assertRaisesRegex(catalog.CatalogError, "extend beyond"):
                    merge_health.validate_content(self.root, sha, self.today)

    def test_manual_readme_edits_and_non_generated_content_block(self):
        for change in [lambda text: text.replace("Manual text.", "Altered text."),
                       lambda text: text.replace(catalog.START, catalog.START + "\nUnsupported claim"),
                       lambda text: "\n" + text, lambda text: text + "\n"]:
            with self.subTest(change=change):
                self.write_snapshot(self.snapshot)
                text = self.readme.read_text(encoding="utf-8")
                self.readme.write_text(change(text), encoding="utf-8")
                sha = self.candidate()
                with self.assertRaisesRegex(catalog.CatalogError, "README differs"):
                    merge_health.validate_content(self.root, sha, self.today)

    def test_deleted_snapshot_and_executable_readme_block(self):
        self.write_snapshot(self.snapshot)
        self.git("add", ".")
        self.git("update-index", "--chmod=+x", "README.md")
        self.git("-c", "user.name=Health tests", "-c", "user.email=tests@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "executable readme")
        sha = self.git("rev-parse", "HEAD").strip()
        self.git("checkout", "--force", "--detach", self.base)
        with self.assertRaisesRegex(catalog.CatalogError, "regular non-executable"):
            merge_health.validate_content(self.root, sha, self.today)
        (self.root / "data/health.json").unlink()
        sha = self.candidate()
        with self.assertRaisesRegex(catalog.CatalogError, "regular non-executable"):
            merge_health.validate_content(self.root, sha, self.today)

    def test_stale_base_and_malformed_snapshot_fail_closed(self):
        self.write_snapshot(self.snapshot)
        sha = self.candidate()
        (self.root / "new.txt").write_text("new default-branch change", encoding="utf-8")
        self.commit("advance main")
        with self.assertRaises(subprocess.CalledProcessError):
            merge_health.validate_content(self.root, sha, self.today)
        self.git("checkout", "--force", "--detach", self.base)
        (self.root / "data/health.json").write_text('{"duplicate": 1, "duplicate": 2}', encoding="utf-8")
        sha = self.candidate()
        with self.assertRaisesRegex(catalog.CatalogError, "duplicate JSON key"):
            merge_health.validate_content(self.root, sha, self.today)


if __name__ == "__main__":
    unittest.main()
