# SPDX-License-Identifier: MIT
"""Catalog validation, rendering, and contribution-flow regression tests."""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import catalog


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "data/projects").mkdir(parents=True)
        shutil.copy(catalog.ROOT / "data/taxonomy.json", self.root / "data/taxonomy.json")
        self.project = catalog.read_json(catalog.ROOT / "examples/project.json")
        self.project["last_reviewed"] = datetime.now(timezone.utc).date().isoformat()
        self.save()
        self.readme = f"# Fixture\n\nManual introduction.\n\n{catalog.START}\n\nOld catalog.\n\n{catalog.END}\n\nManual footer.\n"
        (self.root / "README.md").write_text(self.readme, encoding="utf-8")

    def save(self, project=None):
        project = self.project if project is None else project
        path = self.root / "data/projects" / (project["id"] + ".json")
        path.write_text(json.dumps(project), encoding="utf-8")
        return path

    def load(self):
        return catalog.load_catalog(self.root)

    def assert_invalid(self, message):
        with self.assertRaisesRegex(catalog.CatalogError, message):
            self.load()

    def cli(self, *args):
        output = io.StringIO()
        with patch.object(catalog, "ROOT", self.root), patch("sys.argv", ["catalog.py", *args]), \
                patch("sys.stdout", output), patch("sys.stderr", output):
            result = catalog.main()
        return result, output.getvalue()

    def test_example_is_valid(self):
        _, projects = self.load()
        self.assertEqual(projects, [self.project])

    def test_seed_catalog_and_readme_are_valid(self):
        taxonomy, projects = catalog.load_catalog()
        self.assertEqual(len(projects), len(list((catalog.ROOT / "data/projects").glob("*.json"))))
        self.assertEqual(catalog.render_readme(catalog.ROOT, taxonomy, projects),
                         (catalog.ROOT / "README.md").read_text(encoding="utf-8"))

    def test_missing_and_misspelled_fields_fail(self):
        misspelled = "description".replace("tion", "ton")
        self.project[misspelled] = self.project.pop("description")
        self.save()
        self.assert_invalid(f"missing fields.*description.*unexpected fields.*{misspelled}")

    def test_unknown_taxonomy_values_fail(self):
        for field, value in [("category", "invented"), ("local_mode", "offline"),
                             ("use_cases", ["unknown"]), ("platforms", ["os2"]),
                             ("hardware", ["everything"])]:
            with self.subTest(field=field):
                changed = deepcopy(self.project)
                changed[field] = value
                self.save(changed)
                self.assert_invalid("unknown")

    def test_non_objects_fail_without_tracebacks(self):
        for value in [None, [], "entry", True]:
            with self.subTest(value=value):
                path = self.root / "data/projects/example-project.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                self.assert_invalid("entry must be an object")

    def test_bad_field_types_fail(self):
        for field, value in [("name", []), ("category", []), ("use_cases", "serve-models"),
                             ("hardware", [{}]), ("compatibility", [False]),
                             ("license", []), ("sources", {}), ("last_reviewed", None)]:
            with self.subTest(field=field):
                changed = deepcopy(self.project)
                changed[field] = value
                self.save(changed)
                self.assert_invalid("must")

    def test_empty_use_cases_and_sources_fail(self):
        for field in ["use_cases", "sources"]:
            with self.subTest(field=field):
                changed = deepcopy(self.project)
                changed[field] = []
                self.save(changed)
                self.assert_invalid("nonempty|must not be empty")

    def test_duplicate_array_values_fail(self):
        self.project["use_cases"] *= 2
        self.save()
        self.assert_invalid("contains duplicates")

    def test_duplicate_json_keys_fail(self):
        path = self.root / "data/projects/example-project.json"
        path.write_text('{"id":"one","id":"two"}', encoding="utf-8")
        self.assert_invalid("duplicate JSON key")

    def test_invalid_ids_and_filename_mismatch_fail(self):
        for identifier in ["MixedCase", "path/to/file", "valid-but-different"]:
            with self.subTest(identifier=identifier):
                changed = deepcopy(self.project)
                changed["id"] = identifier
                path = self.root / "data/projects/example-project.json"
                path.write_text(json.dumps(changed), encoding="utf-8")
                self.assert_invalid("id must|filename must")

    def test_repository_must_be_canonical(self):
        for repository in ["https://github.com/example/project/", "https://github.com/example/project.git",
                           "https://github.com/example/project#readme", "https://gitlab.com/example/project",
                           "https://github.com/example/project?x=y", "https://github.com/example/.",
                           "https://github.com/example/..", "https://github.com/../project",
                           "https://github.com/./project", "https://github.com/-bad/project",
                           "https://github.com/bad-/project", f"https://github.com/{'a' * 40}/project"]:
            with self.subTest(repository=repository):
                self.project["repository"] = repository
                self.save()
                self.assert_invalid("repository must")

    def test_unsafe_source_urls_fail(self):
        for value in ["http://example.com", "javascript:alert(1)", "https://user:password@example.com",
                      "https://example.com:8443", "https://example.com:/readme",
                      "https://localhost/readme", "https://app.localhost/readme",
                      "https://app.localhos%74/readme", "https://intranet/readme",
                      "https://example.com./readme", "https://127.0.0.1/readme",
                      "https://127.1/readme", "https://0177.0.0.1/readme",
                      "https://0x7f.0.0.0x1/readme", "https://127.0.0.%31/readme",
                      "https://10.0.0.1/readme", "https://172.16.0.1/readme",
                      "https://192.168.1.1/readme",
                      "https://169.254.169.254/latest/meta-data",
                      "https://0xa9.0xfe.0xa9.0xfe/latest/meta-data",
                      "https://169.254\u3002169\u3002254/latest/meta-data",
                      "https://100.64.0.1/readme",
                      "https://0.0.0.0/readme", "https://224.0.0.1/readme", "https://240.0.0.1/readme",
                      "https://example.com/x y", "https://example.com/)bad", "https://example.com/<script>",
                      "https://[bad"]:
            with self.subTest(url=value):
                self.project["sources"][0]["url"] = value
                self.save()
                self.assert_invalid("source.url")
        catalog.url("https://1.1.1.1/readme", "source.url")

    def test_oversized_and_multiline_descriptions_fail(self):
        for description in ["a" * 181, "first\nsecond", "first\tsecond", " padded ", ""]:
            with self.subTest(description=description):
                self.project["description"] = description
                self.save()
                self.assert_invalid("description")

    def test_invalid_and_future_dates_fail(self):
        tomorrow_utc = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
        for reviewed in ["20260101", "2026-02-30", "2026-1-1", tomorrow_utc]:
            with self.subTest(reviewed=reviewed):
                self.project["last_reviewed"] = reviewed
                self.save()
                self.assert_invalid("last_reviewed")
        fake_utc = datetime(2026, 11, 18, 0, 30, tzinfo=timezone.utc)
        with patch("catalog.datetime") as mocked_dt:
            mocked_dt.now.return_value = fake_utc
            self.project["last_reviewed"] = "2026-11-18"
            self.save()
            self.load()
            self.project["last_reviewed"] = "2026-11-19"
            self.save()
            self.assert_invalid("last_reviewed")

    def test_unknown_license_needs_visible_note(self):
        self.project["license"]["spdx"] = None
        self.project["limitations"] = []
        self.save()
        self.assert_invalid("unknown licensing")
        self.project["limitations"] = ["Upstream licensing is unclear; confirm before redistribution."]
        self.save()
        taxonomy, projects = self.load()
        self.assertIn("Unclear; check upstream", catalog.catalog_markdown(taxonomy, projects))

    def test_spdx_expression_and_invalid_shape(self):
        for valid_spdx in [
            "MIT OR Apache-2.0",
            "Apache-2.0 WITH LLVM-exception",
            "GPL-2.0-only WITH Classpath-exception-2.0 OR MIT",
        ]:
            with self.subTest(spdx=valid_spdx):
                self.project["license"]["spdx"] = valid_spdx
                self.save()
                self.load()
        for bad_spdx in [
            "a license maybe",
            "Unknown",
            "PROPRIETARY",
            "none",
            "Custom",
            "other",
            "TBD",
            "Unlicensed",
            "NOASSERTION",
            "MIT OR Proprietary",
            "OR",
        ]:
            with self.subTest(spdx=bad_spdx):
                self.project["license"]["spdx"] = bad_spdx
                self.save()
                self.assert_invalid("SPDX")

    def test_cloud_entry_needs_limitations(self):
        self.project["local_mode"] = "cloud-dependent"
        self.project["limitations"] = []
        self.save()
        self.assert_invalid("cloud integrations must explain")

    def test_source_shape_and_duplicates_fail(self):
        self.project["sources"][0]["claim"] = "unexpected"
        self.save()
        self.assert_invalid("each source must contain")
        self.project["sources"][0].pop("claim")
        self.project["sources"] *= 2
        self.save()
        self.assert_invalid("duplicate URLs")

    def test_duplicate_names_and_repositories_are_case_insensitive(self):
        for field in ["name", "repository"]:
            with self.subTest(field=field):
                changed = deepcopy(self.project)
                changed["id"] = "another-project"
                changed["name"] = "Another Project"
                changed["repository"] = "https://github.com/another/project"
                changed[field] = self.project[field].upper() if field == "name" else "https://github.com/EXAMPLE/PROJECT"
                self.save(changed)
                self.assert_invalid(f"duplicate {field}")

    def test_empty_catalog_fails(self):
        (self.root / "data/projects/example-project.json").unlink()
        self.assert_invalid("at least one")

    def test_invalid_taxonomy_fails(self):
        path = self.root / "data/taxonomy.json"
        taxonomy = catalog.read_json(path)
        taxonomy["categories"] = []
        path.write_text(json.dumps(taxonomy), encoding="utf-8")
        self.assert_invalid("categories must be")

    def test_render_is_idempotent_and_preserves_manual_sections(self):
        taxonomy, projects = self.load()
        first = catalog.render_readme(self.root, taxonomy, projects)
        self.assertTrue(first.startswith(self.readme.split(catalog.START)[0]))
        self.assertTrue(first.endswith(self.readme.split(catalog.END)[1]))
        (self.root / "README.md").write_text(first, encoding="utf-8")
        self.assertEqual(catalog.render_readme(self.root, taxonomy, projects), first)

    def test_bad_readme_markers_fail(self):
        taxonomy, projects = self.load()
        for readme in ["no markers", catalog.START + catalog.START + catalog.END,
                       catalog.END + catalog.START]:
            with self.subTest(readme=readme):
                (self.root / "README.md").write_text(readme, encoding="utf-8")
                with self.assertRaises(catalog.CatalogError):
                    catalog.render_readme(self.root, taxonomy, projects)

    def test_cloud_entries_only_appear_in_cloud_section_and_task_index(self):
        self.project["local_mode"] = "cloud-dependent"
        self.save()
        taxonomy, projects = self.load()
        generated = catalog.catalog_markdown(taxonomy, projects)
        core = generated.split("## Browse by category", 1)[1].split("## Cloud integrations", 1)[0]
        self.assertNotIn(self.project["repository"], core)
        self.assertIn(self.project["repository"], generated.split("## Cloud integrations", 1)[1])
        self.assertIn(catalog.project_link(self.project) + " (cloud)", generated)

    def test_unknown_hardware_and_markdown_escaping(self):
        self.project["name"] = "Example [name] | <tag>"
        self.save()
        taxonomy, projects = self.load()
        generated = catalog.catalog_markdown(taxonomy, projects)
        self.assertIn("Hardware: Not recorded", generated)
        self.assertIn(r"Example \[name\] \| \<tag\>", generated)

    def test_url_output_is_deduplicated_and_sorted(self):
        _, projects = self.load()
        urls = catalog.catalog_urls(projects * 2)
        self.assertEqual(urls, sorted(set(urls)))
        self.assertIn(self.project["license"]["url"], urls)
        self.assertIn(self.project["sources"][0]["url"], urls)

    def test_submission_flow_and_stale_readme_failure(self):
        self.assertEqual(self.cli("validate")[0], 0)
        result, message = self.cli("check")
        self.assertEqual(result, 1)
        self.assertIn("README is stale", message)
        self.assertEqual(self.cli("render")[0], 0)
        self.assertEqual(self.cli("check")[0], 0)
        result, urls = self.cli("links")
        self.assertEqual(result, 0)
        self.assertIn(self.project["repository"], urls)

    def test_changed_project_filter_rejects_invalid_ref(self):
        for ref in ["main", "--help", "a" * 39]:
            with self.subTest(ref=ref), self.assertRaisesRegex(catalog.CatalogError, "full commit SHA"):
                catalog.changed_projects(self.root, [self.project], ref)

    @unittest.skipUnless(shutil.which("git"), "Git is needed for changed-record integration test")
    def test_changed_project_filter_with_real_git_commits(self):
        def git(*args):
            return subprocess.run(["git", *args], cwd=self.root, check=True,
                                  capture_output=True, text=True).stdout.strip()

        def commit(message):
            git("add", ".")
            git("-c", "user.name=Catalog Tests", "-c", "user.email=catalog@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", message)

        git("init", "-q", "-b", "main")
        commit("fixture")
        base = git("rev-parse", "HEAD")
        self.assertEqual(catalog.changed_projects(self.root, [self.project], base), [])

        git("checkout", "-qb", "feature")
        self.project["description"] = "Updated fixture."
        self.save()
        commit("update feature")

        git("checkout", "-q", "main")
        unrelated = deepcopy(self.project)
        unrelated.update(id="main-only", name="Main Only", repository="https://github.com/example/main-only")
        self.save(unrelated)
        commit("advance main")
        advanced_main = git("rev-parse", "HEAD")

        git("checkout", "-q", "feature")
        self.assertEqual(catalog.changed_projects(self.root, [self.project, unrelated], advanced_main), [self.project])

        git("checkout", "-q", "--orphan", "disconnected")
        orphan = deepcopy(self.project)
        orphan.update(id="orphan-project", name="Orphan Project", repository="https://github.com/example/orphan")
        self.save(orphan)
        commit("orphan commit")
        self.assertIn(orphan, catalog.changed_projects(self.root, [self.project, orphan], base))

    def save_fragment(self, slug="example-project", section="Added", entry=None):
        directory = self.root / "changelog.d"
        directory.mkdir(exist_ok=True)
        payload = {
            "section": section,
            "entry": entry if entry is not None else "[Example Project](https://github.com/example/project), a fixture entry.",
        }
        path = directory / f"{slug}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_task_index_renders_multiline_sorted_bullets(self):
        second = deepcopy(self.project)
        second.update(id="alpha-project", name="alpha project", repository="https://github.com/example/alpha")
        self.save(second)
        taxonomy, projects = self.load()
        generated = catalog.catalog_markdown(taxonomy, projects)
        task_section = generated.split("## Browse by category", 1)[0]
        self.assertNotIn("| I want to...", task_section)
        self.assertIn(
            "### Run a model on my hardware\n\n"
            "- [alpha project](https://github.com/example/alpha)\n"
            "- [Example Project](https://github.com/example/project)\n",
            task_section,
        )

    def test_changelog_fragment_validation_and_cli_integration(self):
        (self.root / "changelog.d").mkdir()
        (self.root / "changelog.d/.gitkeep").write_text("", encoding="utf-8")
        self.save_fragment("valid-link")
        self.save_fragment("valid-prose", section="Updated", entry="Task-based browsing lists one project per line.")
        self.assertEqual(self.cli("render")[0], 0)
        self.assertEqual(self.cli("validate")[0], 0)
        self.assertEqual(self.cli("check")[0], 0)

        invalid_fragments = [
            ("non-object", "[]", "must be an object"),
            ("dup-keys", '{"section":"Added","section":"Updated","entry":"Valid prose."}', "duplicate JSON key"),
            ("bad-fields", '{"section":"Added","entry":"Valid prose.","extra":1}', "unexpected fields"),
            ("bad-section", '{"section":"Fixed","entry":"Valid prose."}', "section must be one of"),
            ("leading-bullet", '{"section":"Added","entry":"- [Example](https://example.com), note."}', "list marker"),
            ("padded", '{"section":"Added","entry":" padded "}', "surrounding whitespace"),
            ("control", '{"section":"Added","entry":"line1\\nline2"}', "control characters"),
            ("http-url", '{"section":"Added","entry":"[Example](http://example.com), note."}', "HTTPS URL"),
            ("js-url", '{"section":"Added","entry":"[Example](javascript:alert(1)), note."}', "unsafe URL|HTTPS URL"),
            ("cred-url", '{"section":"Added","entry":"[Example](https://u:p@example.com), note."}', "credentials"),
            ("local-url", '{"section":"Added","entry":"[Example](https://localhost/doc), note."}', "public documentation"),
            ("space-url", '{"section":"Added","entry":"[Example](https://example.com/a b), note."}', "unsafe URL"),
            ("empty-label", '{"section":"Added","entry":"[](https://example.com), note."}', "link label"),
            ("unclosed-link", '{"section":"Added","entry":"[Example](https://example.com"}', "malformed Markdown link"),
            ("bare-url", '{"section":"Added","entry":"See https://example.com for details."}', "Markdown links"),
            ("markdown-image", '{"section":"Added","entry":"![Badge](https://example.com/badge.svg) note."}', "Markdown images"),
            ("raw-html", '{"section":"Added","entry":"Note <script>alert(1)</script>."}', "raw HTML"),
        ]
        for name, raw_json, expected in invalid_fragments:
            with self.subTest(case=name):
                bad = self.root / "changelog.d/bad-fragment.json"
                bad.write_text(raw_json, encoding="utf-8")
                for subcommand in ["validate", "check"]:
                    code, message = self.cli(subcommand)
                    self.assertEqual(code, 1)
                    self.assertRegex(message, expected)
                bad.unlink()

        for bad_filename in ["MixedCase.json", "under_score.json", "note.md"]:
            with self.subTest(filename=bad_filename):
                bad = self.root / "changelog.d" / bad_filename
                bad.write_text('{"section":"Updated","entry":"Valid prose."}', encoding="utf-8")
                code, message = self.cli("validate")
                self.assertEqual(code, 1)
                self.assertIn(bad_filename, message)
                bad.unlink()

        duplicate = self.save_fragment("duplicate-prose", section="Updated",
                                       entry="task-based browsing lists one project per line.")
        code, message = self.cli("validate")
        self.assertEqual(code, 1)
        self.assertIn("duplicate changelog entry", message)
        duplicate.unlink()

    @unittest.skipUnless(shutil.which("git"), "Git is needed for changed-fragment link extraction test")
    def test_links_extracts_all_and_changed_changelog_fragment_urls(self):
        def git(*args):
            return subprocess.run(["git", *args], cwd=self.root, check=True,
                                  capture_output=True, text=True).stdout.strip()

        old_url = "https://github.com/example/older-fragment"
        new_url = "https://github.com/example/newer-fragment"
        self.save_fragment("older", entry=f"[Older]({old_url}), earlier note.")
        self.assertEqual(self.cli("render")[0], 0)
        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=Catalog Tests", "-c", "user.email=catalog@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "base")
        base = git("rev-parse", "HEAD")

        self.save_fragment("newer", entry=f"[Newer]({new_url}), new note.")
        git("add", ".")
        git("-c", "user.name=Catalog Tests", "-c", "user.email=catalog@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "add fragment")

        code, all_urls = self.cli("links")
        self.assertEqual(code, 0)
        self.assertIn(old_url, all_urls.splitlines())
        self.assertIn(new_url, all_urls.splitlines())

        code, changed_urls = self.cli("links", "--base-ref", base)
        self.assertEqual(code, 0)
        self.assertEqual(changed_urls.splitlines(), [new_url])

    def test_changelog_compilation_merges_sorts_and_deletes_fragments(self):
        changelog_path = self.root / "CHANGELOG.md"
        initial = (
            "# Weekly catalog changelog\n\n"
            "Intro paragraph.\n\n"
            "## Week of 2026-11-09\n\n"
            "### Added\n\n"
            "- [Zeta](https://github.com/example/zeta), existing entry.\n\n"
            "### Removed\n\n"
            "- [Old](https://github.com/example/old), retired upstream.\n"
        )
        changelog_path.write_text(initial, encoding="utf-8")

        # Absent or empty changelog.d is a clean no-op.
        self.assertEqual(self.cli("changelog", "--week", "2026-11-16")[0], 0)
        self.assertEqual(changelog_path.read_text(encoding="utf-8"), initial)

        (self.root / "changelog.d").mkdir()
        (self.root / "changelog.d/.gitkeep").write_text("", encoding="utf-8")
        self.assertEqual(self.cli("changelog", "--week", "2026-11-16")[0], 0)
        self.assertEqual(changelog_path.read_text(encoding="utf-8"), initial)

        # Non-Monday and malformed weeks fail without consuming fragments.
        frag_b = self.save_fragment("bravo", section="Added", entry="[Bravo](https://github.com/example/bravo), second.")
        for bad_week in ["2026-11-18", "2026-02-30", "bad"]:
            with self.subTest(week=bad_week):
                code, _ = self.cli("changelog", "--week", bad_week)
                self.assertEqual(code, 1)
                self.assertTrue(frag_b.exists())
                self.assertEqual(changelog_path.read_text(encoding="utf-8"), initial)

        # Compile into existing week: preserves Zeta order, sorts new Added case-insensitively,
        # and inserts Updated in canonical Added -> Updated -> Removed order.
        self.save_fragment("alpha", section="Added", entry="[alpha](https://github.com/example/alpha), first.")
        self.save_fragment("note", section="Updated", entry="Clarified hardware requirements.")
        self.assertEqual(self.cli("changelog", "--week", "2026-11-09")[0], 0)
        self.assertEqual(list((self.root / "changelog.d").iterdir()), [self.root / "changelog.d/.gitkeep"])
        merged_existing = changelog_path.read_text(encoding="utf-8")
        self.assertIn(
            "## Week of 2026-11-09\n\n"
            "### Added\n\n"
            "- [Zeta](https://github.com/example/zeta), existing entry.\n"
            "- [alpha](https://github.com/example/alpha), first.\n"
            "- [Bravo](https://github.com/example/bravo), second.\n\n"
            "### Updated\n\n"
            "- Clarified hardware requirements.\n\n"
            "### Removed\n\n"
            "- [Old](https://github.com/example/old), retired upstream.\n",
            merged_existing,
        )

        # Compile into a newer week via default current UTC Monday (mocked to Wednesday 2026-11-18).
        self.save_fragment("delta", section="Added", entry="[Delta](https://github.com/example/delta), new tool.")
        fake_now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
        with patch("catalog.datetime") as mocked_dt:
            mocked_dt.now.return_value = fake_now
            self.assertEqual(self.cli("changelog")[0], 0)
        compiled_new = changelog_path.read_text(encoding="utf-8")
        self.assertLess(compiled_new.index("## Week of 2026-11-16"), compiled_new.index("## Week of 2026-11-09"))
        self.assertIn("## Week of 2026-11-16\n\n### Added\n\n- [Delta](https://github.com/example/delta), new tool.\n",
                      compiled_new)

    @unittest.skipUnless(shutil.which("git"), "Git is needed for 3-way merge-file proof")
    def test_three_concurrent_prs_sharing_hotspots_merge_cleanly_and_pass_check(self):
        shutil.rmtree(self.root / "data/projects")
        shutil.copytree(catalog.ROOT / "data/projects", self.root / "data/projects")
        shutil.copy(catalog.ROOT / "data/health.json", self.root / "data/health.json")
        shutil.copy(catalog.ROOT / "CHANGELOG.md", self.root / "CHANGELOG.md")
        shutil.copy(catalog.ROOT / "README.md", self.root / "README.md")
        (self.root / "changelog.d").mkdir()
        (self.root / "changelog.d/.gitkeep").write_text("", encoding="utf-8")
        self.assertEqual(self.cli("render")[0], 0)
        base_readme = (self.root / "README.md").read_text(encoding="utf-8")

        submissions = [
            ("arbor-serve", "Arbor Serve", "inference"),
            ("nimbus-chat", "Nimbus Chat", "deployment"),
            ("zephyr-local", "Zephyr Local", "applications"),
        ]
        branch_readmes = []
        branch_projects = []
        branch_fragments = []

        for slug, name, category in submissions:
            with tempfile.TemporaryDirectory() as branch_dir:
                branch_root = Path(branch_dir)
                shutil.copytree(self.root, branch_root, dirs_exist_ok=True)
                entry = deepcopy(self.project)
                entry.update(
                    id=slug,
                    name=name,
                    repository=f"https://github.com/example/{slug}",
                    description=f"Run and chat with models locally through {name}.",
                    category=category,
                    use_cases=["serve-models", "chat-with-models"],
                )
                entry["license"]["url"] = (
                    f"https://raw.githubusercontent.com/example/{slug}/0123456789abcdef0123456789abcdef01234567/LICENSE"
                )
                entry["sources"] = [{
                    "url": f"https://raw.githubusercontent.com/example/{slug}/0123456789abcdef0123456789abcdef01234567/README.md",
                    "note": f"Documents {name} local serving and chat.",
                }]
                project_file = branch_root / "data/projects" / f"{slug}.json"
                project_file.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
                fragment_payload = {
                    "section": "Added",
                    "entry": f"[{name}](https://github.com/example/{slug}), local serving and chat.",
                }
                fragment_file = branch_root / "changelog.d" / f"{slug}.json"
                fragment_file.write_text(json.dumps(fragment_payload, indent=2) + "\n", encoding="utf-8")

                output = io.StringIO()
                with patch.object(catalog, "ROOT", branch_root), patch("sys.argv", ["catalog.py", "render"]), \
                        patch("sys.stdout", output), patch("sys.stderr", output):
                    self.assertEqual(catalog.main(), 0)
                branch_readmes.append((branch_root / "README.md").read_text(encoding="utf-8"))
                branch_projects.append((slug, project_file.read_text(encoding="utf-8")))
                branch_fragments.append((slug, fragment_file.read_text(encoding="utf-8")))

        with tempfile.TemporaryDirectory() as merge_dir:
            merge_path = Path(merge_dir)
            base_file = merge_path / "base.md"
            current_file = merge_path / "current.md"
            other_file = merge_path / "other.md"
            base_file.write_text(base_readme, encoding="utf-8", newline="\n")
            current_file.write_text(branch_readmes[0], encoding="utf-8", newline="\n")

            for next_readme in branch_readmes[1:]:
                other_file.write_text(next_readme, encoding="utf-8", newline="\n")
                result = subprocess.run(
                    ["git", "merge-file", str(current_file), str(base_file), str(other_file)],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                merged_text = current_file.read_text(encoding="utf-8")
                for marker in ["<<<<<<<", "=======", ">>>>>>>"]:
                    self.assertNotIn(marker, merged_text)

            final_merged_readme = current_file.read_text(encoding="utf-8")

        for slug, content in branch_projects:
            (self.root / "data/projects" / f"{slug}.json").write_text(content, encoding="utf-8")
        for slug, content in branch_fragments:
            (self.root / "changelog.d" / f"{slug}.json").write_text(content, encoding="utf-8")
        (self.root / "README.md").write_text(final_merged_readme, encoding="utf-8")

        # Verify byte-for-byte README match and full check WITHOUT re-rendering.
        taxonomy, projects = self.load()
        self.assertEqual(final_merged_readme, catalog.render_readme(self.root, taxonomy, projects))
        code, message = self.cli("check")
        self.assertEqual(code, 0, msg=message)

        # Verify compiling all 3 fragments into CHANGELOG.md succeeds cleanly.
        self.assertEqual(self.cli("changelog", "--week", "2026-11-16")[0], 0)
        compiled = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        for _, name, _ in submissions:
            self.assertIn(f"- [{name}](https://github.com/example/", compiled)
        self.assertEqual(list((self.root / "changelog.d").iterdir()), [self.root / "changelog.d/.gitkeep"])


if __name__ == "__main__":
    unittest.main()
