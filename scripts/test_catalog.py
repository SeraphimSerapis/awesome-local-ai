# SPDX-License-Identifier: MIT
"""Catalog validation, rendering, and contribution-flow regression tests."""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
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

PINNED_SHA = "0123456789abcdef0123456789abcdef01234567"


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

    def make_project(self, *, project_id="second-project", name="Second Project",
                     repository="https://github.com/example/second-project", **overrides):
        entry = deepcopy(self.project)
        owner, repo = catalog.github_repo_parts(repository)
        entry.update(
            id=project_id,
            name=name,
            repository=repository,
        )
        entry["license"]["url"] = f"https://raw.githubusercontent.com/{owner}/{repo}/{PINNED_SHA}/LICENSE"
        entry["sources"] = [{
            "url": f"https://raw.githubusercontent.com/{owner}/{repo}/{PINNED_SHA}/README.md",
            "note": f"Documents {name} capabilities and requirements.",
        }]
        entry.update(overrides)
        return entry

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

    def health_record(self, repository=None, **overrides):
        repo = self.project["repository"] if repository is None else repository
        record = {
            "repository": repo,
            "checked_at": self.project["last_reviewed"],
            "status": "reachable",
            "detail": None,
            "last_successful_check": self.project["last_reviewed"],
            "canonical_repository": repo,
            "archived": False,
            "disabled": False,
            "last_push": "2026-11-14T04:25:59Z",
            "last_default_branch_commit": "2026-11-14T04:25:59Z",
        }
        record.update(overrides)
        return record

    def test_example_is_valid(self):
        _, projects = self.load()
        self.assertEqual(projects, [self.project])

    def test_example_project_file_is_valid_verbatim(self):
        taxonomy = catalog.load_taxonomy(catalog.ROOT)
        catalog.validate_example_project(catalog.ROOT, taxonomy)
        examples_dir = self.root / "examples"
        examples_dir.mkdir()
        bad = deepcopy(self.project)
        bad["license"]["spdx"] = "FSL-1.1-ALv2"
        (examples_dir / "project.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaisesRegex(catalog.CatalogError, "examples/project.json:.*SPDX"):
            catalog.validate_example_project(self.root, taxonomy)

    def test_seed_catalog_and_readme_are_valid(self):
        taxonomy, projects = catalog.load_catalog()
        self.assertEqual(len(projects), len(list((catalog.ROOT / "data/projects").glob("*.json"))))
        self.assertEqual(catalog.render_readme(catalog.ROOT, taxonomy, projects),
                         (catalog.ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(catalog.render_catalog_json(catalog.ROOT, taxonomy, projects),
                         (catalog.ROOT / catalog.CATALOG_INDEX).read_text(encoding="utf-8"))

    def test_missing_and_misspelled_fields_fail(self):
        misspelled = "description".replace("tion", "ton")
        self.project[misspelled] = self.project.pop("description")
        self.save()
        self.assert_invalid(f"missing fields.*description.*unexpected fields.*{misspelled}")

    def test_unknown_taxonomy_values_fail(self):
        for field, value in [("category", "invented"), ("local_mode", "offline"),
                             ("local_mode", "cloud-dependent"),
                             ("use_cases", ["unknown"]), ("use_cases", ["manage-cloud"]),
                             ("use_cases", ["translate-text"]),
                             ("use_cases", ["evaluate-model-behavior"]),
                             ("platforms", ["os2"]),
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

    def test_stray_files_in_projects_directory_fail(self):
        stray_file = self.root / "data/projects/notes.txt"
        stray_file.write_text("not json", encoding="utf-8")
        self.assert_invalid(r"notes\.txt.*must be \.json files")
        stray_file.unlink()
        stray_dir = self.root / "data/projects/subdir"
        stray_dir.mkdir()
        self.assert_invalid(r"subdir.*must be \.json files")

    def test_bad_field_types_fail(self):
        for field, value in [("name", []), ("category", []), ("use_cases", "serve-models"),
                             ("hardware", [{}]), ("compatibility", [False]),
                             ("license", []), ("sources", {}), ("last_reviewed", None)]:
            with self.subTest(field=field):
                changed = deepcopy(self.project)
                changed[field] = value
                self.save(changed)
                self.assert_invalid("must")

    def test_empty_use_cases_sources_and_limitations_fail(self):
        for field in ["use_cases", "sources", "limitations"]:
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
                           "https://github.com/example/project.GIT",
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

    def test_license_url_must_be_canonical_top_level_pinned_raw(self):
        for valid_name in ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENSE-MIT", "COPYING", "LICENCE.txt"]:
            with self.subTest(valid_name=valid_name):
                self.project["license"]["url"] = (
                    f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/{valid_name}"
                )
                self.save()
                self.load()

        bad_urls = [
            "https://example.com/LICENSE",
            f"https://github.com/example/project/blob/{PINNED_SHA}/LICENSE",
            "https://raw.githubusercontent.com/example/project/main/LICENSE",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA[:39]}/LICENSE",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA.upper()}/LICENSE",
            f"https://RAW.GITHUBUSERCONTENT.COM/example/project/{PINNED_SHA}/LICENSE",
            f"https://raw.githubusercontent.com/other/project/{PINNED_SHA}/LICENSE",
            f"https://raw.githubusercontent.com/example/project.git/{PINNED_SHA}/LICENSE",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/sub/LICENSE",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/README.md",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/LICENSE?raw=1",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/LICENSE#L1",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/..%2fLICENSE",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/sub%5cLICENSE",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/%2e/LICENSE",
        ]
        for bad_url in bad_urls:
            with self.subTest(bad_url=bad_url):
                self.project["license"]["url"] = bad_url
                self.save()
                self.assert_invalid("license.url")

    def test_sources_url_rules_and_no_license_duplication(self):
        canonical_source = self.project["sources"][0]
        # Secondary external docs, cross-repo pinned raw file, and commit URL are accepted alongside canonical raw source.
        for secondary in [
            "https://docs.example.com/guide",
            f"https://raw.githubusercontent.com/other/repo/{PINNED_SHA}/README.md",
            f"https://github.com/example/project/commit/{PINNED_SHA}",
        ]:
            with self.subTest(secondary=secondary):
                self.project["sources"] = [canonical_source, {"url": secondary, "note": "Additional supporting evidence."}]
                self.save()
                self.load()

        # Duplicating license.url (exact or case-folded) fails.
        for dup in [self.project["license"]["url"], self.project["license"]["url"].replace("/LICENSE", "/license")]:
            with self.subTest(dup=dup):
                self.project["sources"] = [canonical_source, {"url": dup, "note": "Duplicate license link."}]
                self.save()
                self.assert_invalid("duplicate license.url")

        # Unpinned raw, non-commit github.com URLs, and query/fragment fail.
        bad_secondary = [
            f"https://github.com/example/project/blob/{PINNED_SHA}/README.md",
            "https://github.com/example/project/tree/main/docs",
            "https://github.com/example/project/releases/tag/v1.0.0",
            "https://github.com/example/project",
            f"https://www.github.com/example/project/commit/{PINNED_SHA}",
            "https://raw.githubusercontent.com/example/project/main/README.md",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/README.md?plain=1",
            f"https://raw.githubusercontent.com/example/project/{PINNED_SHA}/README.md#top",
        ]
        for bad in bad_secondary:
            with self.subTest(bad=bad):
                self.project["sources"] = [canonical_source, {"url": bad, "note": "Bad GitHub link."}]
                self.save()
                self.assert_invalid("source.url")

        # Sources without any canonical repo-pinned raw file fail.
        for only_non_canonical in [
            [{"url": "https://docs.example.com/guide", "note": "External docs only."}],
            [{"url": f"https://raw.githubusercontent.com/other/repo/{PINNED_SHA}/README.md", "note": "Other repo only."}],
            [{"url": f"https://github.com/example/project/commit/{PINNED_SHA}", "note": "Commit link only."}],
        ]:
            with self.subTest(only_non_canonical=only_non_canonical):
                self.project["sources"] = only_non_canonical
                self.save()
                self.assert_invalid("at least one 40-hex commit-pinned")

    def test_oversized_multiline_and_low_quality_descriptions_fail(self):
        for description in [
            "a" * 181,
            "first\nsecond",
            "first\tsecond",
            " padded ",
            "",
            "Too short.",
            "Missing trailing period at the end of sentence",
            "Ends with double period..",
            "First sentence. Second sentence.",
            "Runs on a CPU. Supports GPUs.",
            "Fast engine! Also includes a chat UI.",
            "See https://example.com for details about local AI.",
            "Use [this link](https://example.com) for local models.",
            "![badge](https://example.com/badge.svg) local engine.",
            "- Bullet prefix is not allowed in descriptions.",
            "1. Numbered prefix is not allowed in descriptions.",
        ]:
            with self.subTest(description=description):
                self.project["description"] = description
                self.save()
                self.assert_invalid("description")

        # Technical dots and abbreviations inside a single sentence are allowed.
        self.project["description"] = "Serve llama.cpp and Node.js v2.0 models (e.g. Qwen) on local hardware."
        self.save()
        self.load()

    def test_plain_text_hygiene_preserves_local_loopback_urls(self):
        self.project["compatibility"] = [
            "Serves an OpenAI-compatible API at http://127.0.0.1:7878/v1 with optional authentication."
        ]
        self.save()
        self.load()

        for field, bad_value in [
            ("name", "Example https://example.com"),
            ("name", "[Example](https://example.com)"),
            ("compatibility", ["See [docs](https://example.com) for details."]),
            ("compatibility", ["- Bullet item in compatibility."]),
            ("limitations", ["![warn](https://example.com/w.png) preview build."]),
            ("limitations", ["1. Numbered limitation."]),
        ]:
            with self.subTest(field=field, bad_value=bad_value):
                changed = deepcopy(self.project)
                changed[field] = bad_value
                self.save(changed)
                self.assert_invalid(field)

        self.project["sources"][0]["note"] = "See [README](https://example.com) for details."
        self.save()
        self.assert_invalid("source.note")

    def test_platforms_and_hardware_consistency(self):
        for platforms, hardware, expected in [
            ([], ["cpu"], "hardware tags require"),
            (["windows"], ["dgx-spark"], "dgx-spark hardware requires linux"),
            (["macos"], ["dgx-spark"], "dgx-spark hardware requires linux"),
            (["windows"], ["apple-silicon"], "apple-silicon hardware requires"),
        ]:
            with self.subTest(platforms=platforms, hardware=hardware):
                changed = deepcopy(self.project)
                changed["platforms"] = platforms
                changed["hardware"] = hardware
                self.save(changed)
                self.assert_invalid(expected)

        for platforms, hardware in [
            (["linux", "macos", "windows"], []),
            (["macos"], ["apple-silicon"]),
            (["linux"], ["apple-silicon"]),
            (["linux"], ["dgx-spark"]),
        ]:
            with self.subTest(valid=(platforms, hardware)):
                changed = deepcopy(self.project)
                changed["platforms"] = platforms
                changed["hardware"] = hardware
                self.save(changed)
                self.load()

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

    def test_null_license_is_rejected(self):
        self.project["license"]["spdx"] = None
        self.project["limitations"] = ["Upstream licensing is unclear; confirm before redistribution."]
        self.save()
        self.assert_invalid("license.spdx.*not null")

    def test_spdx_expression_and_osi_enforcement(self):
        for valid_spdx in [
            "MIT",
            "Apache-2.0",
            "AGPL-3.0-only",
            "BSL-1.0",
            "MIT OR Apache-2.0",
            "(MIT OR Apache-2.0) AND BSD-3-Clause",
            "Apache-2.0 WITH LLVM-exception",
            "GPL-2.0-only WITH Classpath-exception-2.0 OR MIT",
            "(Apache-2.0 WITH LLVM-exception) OR MIT",
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
            "FSL-1.1-ALv2",
            "FSL-1.1-MIT",
            "BUSL-1.1",
            "SSPL-1.0",
            "CC0-1.0",
            "CC-BY-NC-4.0",
            "GPL-2.0+",
            "mit",
            "MIT OR FSL-1.1-ALv2",
            "MIT AND BUSL-1.1",
            "MIT WITH Apache-2.0",
            "LLVM-exception",
            "MIT WITH LLVM-exception WITH GCC-exception-3.1",
            "(MIT OR Apache-2.0) WITH LLVM-exception",
            "(MIT",
            "MIT)",
            "()",
            "MIT AND",
            "MIT Apache-2.0",
        ]:
            with self.subTest(spdx=bad_spdx):
                self.project["license"]["spdx"] = bad_spdx
                self.save()
                self.assert_invalid("SPDX")

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
                if field == "name":
                    changed = self.make_project(
                        project_id="another-project",
                        name=self.project["name"].upper(),
                        repository="https://github.com/another/project",
                    )
                else:
                    changed = self.make_project(
                        project_id="another-project",
                        name="Another Project",
                        repository="https://github.com/EXAMPLE/PROJECT",
                    )
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

    def test_health_rejects_orphaned_and_mismatched_entries_but_allows_missing(self):
        _, projects = self.load()
        health_path = self.root / "data/health.json"
        # Missing entry is allowed (new PRs do not edit data/health.json).
        health_path.write_text(json.dumps({}), encoding="utf-8")
        self.assertEqual(catalog.load_health(self.root, projects), {})

        # Exact match passes.
        valid = {self.project["id"]: self.health_record()}
        health_path.write_text(json.dumps(valid), encoding="utf-8")
        self.assertEqual(catalog.load_health(self.root, projects), valid)

        # Orphaned project ID fails.
        orphaned = dict(valid, removed=self.health_record("https://github.com/example/removed"))
        health_path.write_text(json.dumps(orphaned), encoding="utf-8")
        with self.assertRaisesRegex(catalog.CatalogError, "health.removed: unknown or removed project ID"):
            catalog.load_health(self.root, projects)

        # Mismatched repository URL fails.
        mismatched = {self.project["id"]: self.health_record("https://github.com/other/project")}
        health_path.write_text(json.dumps(mismatched), encoding="utf-8")
        with self.assertRaisesRegex(catalog.CatalogError, "repository does not match project record"):
            catalog.load_health(self.root, projects)

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

    def test_empty_categories_render_placeholder_with_valid_anchor(self):
        taxonomy, projects = self.load()
        generated = catalog.catalog_markdown(taxonomy, projects)
        self.assertNotIn("Cloud integrations", generated)
        self.assertIn("- [Open categories](#open-categories):", generated)
        self.assertIn("[Agent skills and extensions](#skills)", generated)
        self.assertIn(
            "### Open categories\n\n"
            "These categories do not have entries yet. [Suggest a project](CONTRIBUTING.md).\n",
            generated,
        )
        self.assertIn('- <a id="skills"></a>**Agent skills and extensions**', generated)

    def test_unknown_hardware_and_markdown_escaping(self):
        self.project["name"] = "Example [name] | <tag>"
        self.save()
        taxonomy, projects = self.load()
        generated = catalog.catalog_markdown(taxonomy, projects)
        self.assertIn("| Not recorded | Not recorded |", generated)
        self.assertIn(r"  [Example \[name\] \| \<tag\>](#project-example-project)", generated)
        self.assertIn(
            r'| <a id="project-example-project"></a>[Example \[name\] \| \<tag\>](https://github.com/example/project) |',
            generated,
        )

    def test_markdown_prose_wraps_bare_urls_in_code_spans(self):
        self.assertEqual(
            catalog.markdown_prose("API at http://127.0.0.1:7878/v1 with no key."),
            "API at `http://127.0.0.1:7878/v1` with no key.",
        )
        self.assertEqual(
            catalog.markdown_prose("Endpoint is https://example.com/a_b."),
            "Endpoint is `https://example.com/a_b`.",
        )
        self.project["compatibility"] = [
            "Serves OpenAI-compatible HTTP API at http://127.0.0.1:7878/v1 with optional auth."
        ]
        self.save()
        taxonomy, projects = self.load()
        generated = catalog.catalog_markdown(taxonomy, projects)
        self.assertIn("at `http://127.0.0.1:7878/v1` with optional auth.", generated)

    def test_health_rendering_covers_activity_alerts_and_details(self):
        taxonomy, projects = self.load()

        # Unchecked entry shows bold alert in table, no Repository alerts blockquote, no healthy boilerplate.
        unchecked_md = catalog.catalog_markdown(taxonomy, projects, {})
        self.assertIn("**Not checked yet**; [JSON](data/projects/example-project.json)", unchecked_md)
        self.assertIn("repository not checked yet", unchecked_md)
        self.assertNotIn("Repository alerts", unchecked_md)
        self.assertNotIn("Archived: no", unchecked_md)
        self.assertNotIn("Disabled: no", unchecked_md)

        base_observation = self.health_record(
            last_push="2026-11-14T04:25:59Z",
            last_default_branch_commit="2026-09-26T10:15:00Z",
        )
        self.assertEqual(
            catalog.table_activity_cell(self.project, base_observation),
            "2026-09-26; [JSON](data/projects/example-project.json)",
        )
        self.assertIsNone(catalog.category_alert_line(self.project, base_observation))

        divergent = catalog.project_detail_lines(
            self.project, base_observation, snapshot_date=self.project["last_reviewed"]
        )
        self.assertEqual(
            divergent[0],
            f'- **Example Project**, reviewed {self.project["last_reviewed"]}; '
            "default-branch commit 2026-09-26, push 2026-11-14; [record](data/projects/example-project.json)",
        )
        for forbidden in ["(", ")", "—", "–", "--"]:
            self.assertNotIn(forbidden, divergent[0].split("[record]", 1)[0])

        matching = catalog.project_detail_lines(
            self.project,
            dict(base_observation, last_default_branch_commit="2026-11-14T01:00:00Z"),
            snapshot_date=self.project["last_reviewed"],
        )
        self.assertIn("last commit 2026-11-14", matching[0])

        missing_commit = catalog.project_detail_lines(
            self.project,
            dict(base_observation, last_default_branch_commit=None),
            snapshot_date=self.project["last_reviewed"],
        )
        self.assertIn("last push 2026-11-14", missing_commit[0])

        # Flagged entry renders bold table flags, MD032-compliant blockquote alert, and details status line.
        flagged_obs = self.health_record(
            status="unavailable",
            detail="HTTP 404; repository may be missing.",
            archived=True,
            disabled=False,
            canonical_repository="https://github.com/example/renamed-project",
        )
        flagged_md = catalog.catalog_markdown(taxonomy, projects, {self.project["id"]: flagged_obs})
        self.assertIn("**Unavailable, Archived, Redirected**; [JSON](data/projects/example-project.json)", flagged_md)
        self.assertIn("> **Repository alerts:**\n>\n> - **Example Project:**", flagged_md)
        self.assertIn("[example/renamed-project](https://github.com/example/renamed-project)", flagged_md)
        self.assertIn("Prior metadata retained from", flagged_md)
        self.assertIn("  - **Repository status:**", flagged_md)

    def test_validate_health_record_validates_default_branch_commit_field(self):
        valid = self.health_record(last_default_branch_commit="2026-09-26T10:15:00Z")
        catalog.validate_health_record(valid)
        catalog.validate_health_record(dict(valid, last_default_branch_commit=None))

        missing_key = dict(valid)
        missing_key.pop("last_default_branch_commit")
        with self.assertRaisesRegex(catalog.CatalogError, "missing or unexpected"):
            catalog.validate_health_record(missing_key)

        for bad_ts in ["2026-09-26", "2026-09-26T10:15:00+00:00", 123, ""]:
            with self.subTest(bad_ts=bad_ts), self.assertRaisesRegex(catalog.CatalogError, "last_default_branch_commit"):
                catalog.validate_health_record(dict(valid, last_default_branch_commit=bad_ts))

        never_checked = dict(
            valid,
            status="check-failed",
            detail="Offline.",
            last_successful_check=None,
            canonical_repository=None,
            archived=None,
            disabled=None,
            last_push=None,
            last_default_branch_commit="2026-09-26T10:15:00Z",
        )
        with self.assertRaisesRegex(catalog.CatalogError, "requires a successful observation"):
            catalog.validate_health_record(never_checked)

    def test_url_output_is_deduplicated_and_sorted(self):
        _, projects = self.load()
        urls = catalog.catalog_urls(projects * 2)
        self.assertEqual(urls, sorted(set(urls)))
        self.assertIn(self.project["license"]["url"], urls)
        self.assertIn(self.project["sources"][0]["url"], urls)

    def test_submission_flow_and_stale_outputs_failure(self):
        self.assertEqual(self.cli("validate")[0], 0)
        result, message = self.cli("check")
        self.assertEqual(result, 1)
        self.assertIn("README is stale", message)
        self.assertEqual(self.cli("render")[0], 0)
        self.assertEqual(self.cli("check")[0], 0)

        index_path = self.root / catalog.CATALOG_INDEX
        self.assertTrue(index_path.is_file())
        index_data = catalog.read_json(index_path)
        self.assertEqual(index_data["schema_version"], 1)
        self.assertEqual(index_data["generated_by"], "scripts/catalog.py render")
        self.assertNotIn("generated_at", index_data)
        self.assertNotIn("project_count", index_data)
        self.assertEqual([entry["id"] for entry in index_data["projects"]], ["example-project"])
        entry = index_data["projects"][0]
        self.assertEqual(entry["record_path"], "data/projects/example-project.json")
        self.assertEqual(entry["labels"]["category"], "Inference and serving")
        self.assertEqual(entry["labels"]["local_mode"], "Local workload")
        self.assertEqual(entry["labels"]["use_cases"], ["Run a model on my hardware"])
        self.assertIsNone(entry["health"])
        self.assertEqual(entry["health_flags"], ["unchecked"])

        # Missing or drifted data/catalog.json fails check.
        index_path.unlink()
        result, message = self.cli("check")
        self.assertEqual(result, 1)
        self.assertIn("data/catalog.json is stale", message)
        index_path.write_text("{}\n", encoding="utf-8")
        result, message = self.cli("check")
        self.assertEqual(result, 1)
        self.assertIn("data/catalog.json is stale", message)

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
        unrelated = self.make_project(
            project_id="main-only",
            name="Main Only",
            repository="https://github.com/example/main-only",
        )
        self.save(unrelated)
        commit("advance main")
        advanced_main = git("rev-parse", "HEAD")

        git("checkout", "-q", "feature")
        self.assertEqual(catalog.changed_projects(self.root, [self.project, unrelated], advanced_main), [self.project])

        git("checkout", "-q", "--orphan", "disconnected")
        orphan = self.make_project(
            project_id="orphan-project",
            name="Orphan Project",
            repository="https://github.com/example/orphan",
        )
        self.save(orphan)
        commit("orphan commit")
        self.assertIn(orphan, catalog.changed_projects(self.root, [self.project, orphan], base))

    @unittest.skipUnless(shutil.which("git"), "Git is needed for new taxonomy ID base-ref test")
    def test_new_taxonomy_ids_require_two_projects_under_base_ref(self):
        def git(*args):
            return subprocess.run(["git", *args], cwd=self.root, check=True,
                                  capture_output=True, text=True).stdout.strip()

        def commit(message):
            git("add", ".")
            git("-c", "user.name=Catalog Tests", "-c", "user.email=catalog@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", message)

        self.assertEqual(self.cli("render")[0], 0)
        git("init", "-q", "-b", "main")
        commit("base")
        base = git("rev-parse", "HEAD")

        # Add a new use_case referenced by only 1 project -> must fail --base-ref.
        tax_path = self.root / "data/taxonomy.json"
        taxonomy = catalog.read_json(tax_path)
        taxonomy["use_cases"]["brand-new-task"] = "Run a brand new task"
        tax_path.write_text(json.dumps(taxonomy, indent=2) + "\n", encoding="utf-8")
        self.project["use_cases"] = ["serve-models", "brand-new-task"]
        self.save()
        self.assertEqual(self.cli("render")[0], 0)

        code, message = self.cli("validate", "--base-ref", base)
        self.assertEqual(code, 1)
        self.assertIn("brand-new-task", message)
        self.assertIn("at least 2", message)

        code, message = self.cli("check", "--base-ref", base)
        self.assertEqual(code, 1)
        self.assertIn("brand-new-task", message)

        # Adding a second qualifying project sharing the new ID passes.
        second = self.make_project(use_cases=["serve-models", "brand-new-task"])
        self.save(second)
        self.assertEqual(self.cli("render")[0], 0)
        self.assertEqual(self.cli("validate", "--base-ref", base)[0], 0)
        self.assertEqual(self.cli("check", "--base-ref", base)[0], 0)

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
        second = self.make_project(
            project_id="alpha-project",
            name="alpha project",
            repository="https://github.com/example/alpha",
        )
        self.save(second)
        taxonomy, projects = self.load()
        generated = catalog.catalog_markdown(taxonomy, projects)
        task_section, category_section = generated.split("## Browse by category", 1)
        self.assertNotIn("| I want to...", task_section)
        self.assertNotIn("https://", task_section)
        self.assertNotIn("### ", task_section)
        self.assertIn(
            "- **Run a model on my hardware:**\n"
            "  [alpha project](#project-alpha-project),\n"
            "  [Example Project](#project-example-project)\n",
            task_section,
        )
        self.assertIn(
            '| <a id="project-alpha-project"></a>[alpha project](https://github.com/example/alpha) |',
            category_section,
        )
        self.assertIn(
            '| <a id="project-example-project"></a>[Example Project](https://github.com/example/project) |',
            category_section,
        )

    def test_project_anchors_are_unique_and_resolve_all_readme_fragments(self):
        taxonomy, projects = catalog.load_catalog()
        rendered = catalog.render_readme(catalog.ROOT, taxonomy, projects)
        catalog_body = rendered.split(catalog.START, 1)[1].split(catalog.END, 1)[0]
        task_section, category_section = catalog_body.split("## Browse by category", 1)
        self.assertNotIn("https://", task_section)

        # Verify project anchors live outside collapsed <details> blocks.
        outside_details = re.sub(r"<details>.*?</details>", "", category_section, flags=re.DOTALL)
        for project in projects:
            anchor = f'project-{project["id"]}'
            escaped_name = catalog.markdown(project["name"])
            self.assertEqual(category_section.count(f'<a id="{anchor}"></a>'), 1)
            self.assertEqual(outside_details.count(f'<a id="{anchor}"></a>'), 1)
            self.assertIn(
                f'| <a id="{anchor}"></a>[{escaped_name}]({project["repository"]}) | ',
                outside_details,
            )
            self.assertIn(f"  [{escaped_name}](#{anchor})", task_section)

        non_fenced_lines = []
        in_fence = False
        for line in rendered.splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                non_fenced_lines.append(line)
        non_fenced = "\n".join(non_fenced_lines)

        anchor_ids = re.findall(r'<a id="([^"]+)"></a>', non_fenced)
        self.assertEqual(len(anchor_ids), len(set(anchor_ids)))

        heading_slugs = set()
        heading_counts = {}
        for line in non_fenced_lines:
            match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
            if not match:
                continue
            plain = re.sub(r"\\([\\`*_{}\[\]<>|])", r"\1", match.group(1))
            plain = plain.replace("`", "")
            slug = "".join(
                ch if (ch.isalnum() or ch in "_-") else ("-" if ch.isspace() else "")
                for ch in plain.lower()
            )
            count = heading_counts.get(slug, 0)
            heading_counts[slug] = count + 1
            heading_slugs.add(f"{slug}-{count}" if count else slug)

        project_anchors = {f'project-{project["id"]}' for project in projects}
        self.assertTrue(project_anchors.isdisjoint(heading_slugs))
        valid_targets = set(anchor_ids) | heading_slugs
        fragment_links = re.findall(r"\]\(#([^)\s]+)\)", non_fenced)
        self.assertTrue(fragment_links)
        for fragment in fragment_links:
            self.assertIn(fragment, valid_targets)

    def test_changelog_file_validation_and_fragment_hardening(self):
        changelog_path = self.root / "CHANGELOG.md"
        valid_changelog = (
            "# Weekly catalog changelog\n\n"
            "## Week of 2026-11-16\n\n"
            "### Added\n\n"
            "- [Alpha](https://github.com/example/alpha), first.\n\n"
            "## Week of 2026-11-09\n\n"
            "### Updated\n\n"
            "- Clarified limits.\n"
        )
        changelog_path.write_text(valid_changelog, encoding="utf-8")
        catalog.validate_changelog_file(self.root)

        bad_changelogs = [
            ("non-monday", "# Changelog\n\n## Week of 2026-11-18\n\n### Added\n\n- Entry.\n", "Monday"),
            ("ascending", "# Changelog\n\n## Week of 2026-11-09\n\n### Added\n\n- A.\n\n## Week of 2026-11-16\n\n### Added\n\n- B.\n", "descending"),
            ("empty-week", "# Changelog\n\n## Week of 2026-11-16\n\n## Week of 2026-11-09\n\n### Added\n\n- A.\n", "must not be empty"),
            ("bad-subsection", "# Changelog\n\n## Week of 2026-11-16\n\n### Fixed\n\n- A.\n", "unknown changelog subsection"),
            ("stray-line", "# Changelog\n\n## Week of 2026-11-16\n\n### Added\n\nNot a bullet.\n", "unexpected line"),
        ]
        for label, content, expected in bad_changelogs:
            with self.subTest(label=label):
                changelog_path.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(catalog.CatalogError, expected):
                    catalog.validate_changelog_file(self.root)

        # Also validate the repository's real CHANGELOG.md.
        catalog.validate_changelog_file(catalog.ROOT)

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
            ("ordered-list", '{"section":"Added","entry":"1. Numbered note."}', "list marker"),
            ("heading", '{"section":"Added","entry":"### Heading note."}', "heading"),
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
        self.project["last_reviewed"] = "2026-11-18"
        self.save()
        self.save_fragment("delta", section="Added", entry="[Delta](https://github.com/example/delta), new tool.")
        fake_now = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
        with patch("catalog.datetime") as mocked_dt:
            mocked_dt.now.return_value = fake_now
            self.assertEqual(self.cli("changelog")[0], 0)
        compiled_new = changelog_path.read_text(encoding="utf-8")
        self.assertLess(compiled_new.index("## Week of 2026-11-16"), compiled_new.index("## Week of 2026-11-09"))
        self.assertIn("## Week of 2026-11-16\n\n### Added\n\n- [Delta](https://github.com/example/delta), new tool.\n",
                      compiled_new)

    @unittest.skipUnless(shutil.which("git"), "Git is needed for commit-date changelog test")
    def test_changelog_by_commit_date_and_dry_run(self):
        def git(*args, commit_date=None):
            env = dict(os.environ)
            if commit_date is not None:
                env["GIT_AUTHOR_DATE"] = commit_date
                env["GIT_COMMITTER_DATE"] = commit_date
            return subprocess.run(["git", *args], cwd=self.root, check=True,
                                  capture_output=True, text=True, env=env).stdout.strip()

        changelog_path = self.root / "CHANGELOG.md"
        initial = "# Weekly catalog changelog\n\n## Week of 2026-11-09\n\n### Added\n\n- Existing item.\n"
        changelog_path.write_text(initial, encoding="utf-8")
        self.assertEqual(self.cli("render")[0], 0)
        git("init", "-q", "-b", "main")
        git("add", ".")
        git("-c", "user.name=Catalog Tests", "-c", "user.email=catalog@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "base", commit_date="2026-11-10T12:00:00Z")

        f1 = self.save_fragment("nov-20", section="Added", entry="[First](https://github.com/example/first), Nov 20 entry.")
        git("add", "changelog.d/nov-20.json")
        git("-c", "user.name=Catalog Tests", "-c", "user.email=catalog@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "add nov-20", commit_date="2026-11-20T15:00:00Z")

        f2 = self.save_fragment("nov-25", section="Updated", entry="[Second](https://github.com/example/second), Nov 25 update.")
        git("add", "changelog.d/nov-25.json")
        git("-c", "user.name=Catalog Tests", "-c", "user.email=catalog@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "add nov-25", commit_date="2026-11-25T08:00:00Z")

        # Dry run previews both weeks without editing CHANGELOG.md or deleting fragments.
        code, output = self.cli("changelog", "--by-commit-date", "--dry-run")
        self.assertEqual(code, 0, msg=output)
        self.assertIn("2026-11-16", output)
        self.assertIn("2026-11-23", output)
        self.assertIn("+++ CHANGELOG.md", output)
        self.assertTrue(f1.exists() and f2.exists())
        self.assertEqual(changelog_path.read_text(encoding="utf-8"), initial)

        # Actual run buckets Nov 20 -> Week of 2026-11-16 and Nov 25 -> Week of 2026-11-23.
        code, output = self.cli("changelog", "--by-commit-date")
        self.assertEqual(code, 0, msg=output)
        self.assertFalse(f1.exists() or f2.exists())
        compiled = changelog_path.read_text(encoding="utf-8")
        self.assertLess(compiled.index("## Week of 2026-11-23"), compiled.index("## Week of 2026-11-16"))
        self.assertLess(compiled.index("## Week of 2026-11-16"), compiled.index("## Week of 2026-11-09"))
        self.assertIn("## Week of 2026-11-23\n\n### Updated\n\n- [Second]", compiled)
        self.assertIn("## Week of 2026-11-16\n\n### Added\n\n- [First]", compiled)

    def test_status_dashboard_reports_all_sections(self):
        self.project["last_reviewed"] = "2026-09-01"
        self.save()
        second = self.make_project(
            project_id="quiet-tool",
            name="Quiet Tool",
            repository="https://github.com/example/quiet-tool",
            last_reviewed="2026-11-20",
            use_cases=["serve-models", "evaluate-tool-calling"],
        )
        self.save(second)
        third = self.make_project(
            project_id="unchecked-tool",
            name="Unchecked Tool",
            repository="https://github.com/other/unchecked",
            last_reviewed="2026-11-20",
        )
        self.save(third)
        self.save_fragment("pending-note", section="Updated", entry="Pending note.")

        health_data = {
            self.project["id"]: self.health_record(
                checked_at="2026-11-24",
                last_successful_check="2026-11-24",
                last_push="2026-11-20T00:00:00Z",
                last_default_branch_commit="2026-11-20T00:00:00Z",
                archived=True,
            ),
            "quiet-tool": self.health_record(
                repository="https://github.com/example/quiet-tool",
                checked_at="2026-11-24",
                last_successful_check="2026-11-24",
                last_push="2026-07-01T00:00:00Z",
                last_default_branch_commit="2026-07-01T00:00:00Z",
            ),
        }
        (self.root / "data/health.json").write_text(json.dumps(health_data), encoding="utf-8")

        taxonomy, projects = self.load()
        health = catalog.load_health(self.root, projects)
        fragments = catalog.load_changelog_fragments(self.root)
        report = catalog.build_status_report(
            self.root, taxonomy, projects, health, fragments,
            stale_review_days=60, inactive_days=90, today=date(2026, 11, 26),
        )
        formatted = catalog.format_status_report(report)
        self.assertIn("3 projects, 2/3 health checked, 1 pending changelog fragments", formatted)
        self.assertIn("changelog.d/pending-note.json [Updated]", formatted)
        self.assertIn("Missing from data/health.json: unchecked-tool", formatted)
        self.assertIn("Flagged example-project: archived", formatted)
        self.assertIn("example-project: reviewed 2026-09-01 (86d ago), commit 2026-11-20 (+80d after review)", formatted)
        self.assertIn("quiet-tool: last commit 2026-07-01 (148d ago)", formatted)
        self.assertIn("use_cases.evaluate-tool-calling (quiet-tool)", formatted)
        self.assertIn("example: example-project, quiet-tool", formatted)

        code, cli_output = self.cli("status", "--stale-review-days", "60", "--inactive-days", "90")
        self.assertEqual(code, 0)
        self.assertIn("Catalog status", cli_output)

    def test_remove_command_prunes_health_writes_fragment_renders_and_reports_low_tags(self):
        second = self.make_project(
            project_id="retire-me",
            name="Retire [Me]",
            repository="https://github.com/example/retire-me",
            use_cases=["serve-models", "evaluate-tool-calling"],
            platforms=["linux"],
            hardware=["cpu"],
        )
        self.save(second)
        health_data = {
            self.project["id"]: self.health_record(),
            "retire-me": self.health_record(repository=second["repository"]),
        }
        (self.root / "data/health.json").write_text(json.dumps(health_data), encoding="utf-8")
        self.assertEqual(self.cli("render")[0], 0)

        # Error cases before any mutation: unknown ID, duplicate ID, removing every project.
        self.assertEqual(self.cli("remove", "missing-id", "--reason", "gone")[0], 1)
        self.assertEqual(self.cli("remove", "retire-me", "retire-me", "--reason", "dup")[0], 1)
        self.assertEqual(self.cli("remove", "example-project", "retire-me", "--reason", "all")[0], 1)
        self.assertTrue((self.root / "data/projects/retire-me.json").exists())

        code, output = self.cli("remove", "retire-me", "--reason", "fails OSI license requirement")
        self.assertEqual(code, 0, msg=output)
        self.assertFalse((self.root / "data/projects/retire-me.json").exists())
        updated_health = catalog.read_json(self.root / "data/health.json")
        self.assertEqual(set(updated_health), {self.project["id"]})
        fragment_path = self.root / "changelog.d/remove-retire-me.json"
        self.assertTrue(fragment_path.exists())
        fragment = catalog.read_json(fragment_path)
        self.assertEqual(fragment["section"], "Removed")
        self.assertIn(r"[Retire \[Me\]](https://github.com/example/retire-me), fails OSI license requirement.", fragment["entry"])
        self.assertIn("use_cases.evaluate-tool-calling (0)", output)
        self.assertIn("hardware.cpu (0)", output)
        # Catalog passes full check after remove without manual follow-up.
        self.assertEqual(self.cli("check")[0], 0)

    def test_verify_command_handles_skip_external_strict_and_missing_tools(self):
        self.assertEqual(self.cli("render")[0], 0)
        # Isolated temp dir has no scripts/ dir -> unit tests skipped -> 0 without strict, 1 with strict.
        code, output = self.cli("verify", "--skip-external")
        self.assertEqual(code, 0, msg=output)
        self.assertIn("[PASS] catalog check", output)
        self.assertIn("[SKIPPED] unit tests", output)

        code_strict, _ = self.cli("verify", "--skip-external", "--strict")
        self.assertEqual(code_strict, 1)

        # Missing external tools report SKIPPED and pass without --strict, fail with --strict.
        with patch("catalog.shutil.which", return_value=None):
            code, output = self.cli("verify")
            self.assertEqual(code, 0, msg=output)
            self.assertIn("[SKIPPED] markdownlint", output)
            self.assertIn("[SKIPPED] typos", output)
            self.assertIn("[SKIPPED] lychee", output)

            code_strict, _ = self.cli("verify", "--strict")
            self.assertEqual(code_strict, 1)

        # Stale README causes catalog check FAIL and exit code 1.
        (self.root / "README.md").write_text(self.readme, encoding="utf-8")
        code, output = self.cli("verify", "--skip-external")
        self.assertEqual(code, 1, msg=output)
        self.assertIn("[FAIL] catalog check", output)

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
        base_index = (self.root / catalog.CATALOG_INDEX).read_text(encoding="utf-8")

        submissions = [
            ("arbor-serve", "Arbor Serve", "inference"),
            ("nimbus-chat", "Nimbus Chat", "deployment"),
            ("zephyr-local", "Zephyr Local", "applications"),
        ]
        branch_readmes = []
        branch_indexes = []
        branch_projects = []
        branch_fragments = []

        for slug, name, category in submissions:
            with tempfile.TemporaryDirectory() as branch_dir:
                branch_root = Path(branch_dir)
                shutil.copytree(self.root, branch_root, dirs_exist_ok=True)
                entry = self.make_project(
                    project_id=slug,
                    name=name,
                    repository=f"https://github.com/example/{slug}",
                    description=f"Run and chat with models locally through {name}.",
                    category=category,
                    use_cases=["serve-models", "chat-with-models"],
                )
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
                branch_indexes.append((branch_root / catalog.CATALOG_INDEX).read_text(encoding="utf-8"))
                branch_projects.append((slug, project_file.read_text(encoding="utf-8")))
                branch_fragments.append((slug, fragment_file.read_text(encoding="utf-8")))

        def merge_series(base_text, branch_texts, ext):
            with tempfile.TemporaryDirectory() as merge_dir:
                merge_path = Path(merge_dir)
                base_file = merge_path / f"base.{ext}"
                current_file = merge_path / f"current.{ext}"
                other_file = merge_path / f"other.{ext}"
                base_file.write_text(base_text, encoding="utf-8", newline="\n")
                current_file.write_text(branch_texts[0], encoding="utf-8", newline="\n")
                for next_text in branch_texts[1:]:
                    other_file.write_text(next_text, encoding="utf-8", newline="\n")
                    result = subprocess.run(
                        ["git", "merge-file", str(current_file), str(base_file), str(other_file)],
                        capture_output=True, text=True, encoding="utf-8",
                    )
                    self.assertEqual(result.returncode, 0, msg=result.stderr)
                    merged_text = current_file.read_text(encoding="utf-8")
                    for marker in ["<<<<<<<", "=======", ">>>>>>>"]:
                        self.assertNotIn(marker, merged_text)
                return current_file.read_text(encoding="utf-8")

        final_merged_readme = merge_series(base_readme, branch_readmes, "md")
        final_merged_index = merge_series(base_index, branch_indexes, "json")

        for slug, content in branch_projects:
            (self.root / "data/projects" / f"{slug}.json").write_text(content, encoding="utf-8")
        for slug, content in branch_fragments:
            (self.root / "changelog.d" / f"{slug}.json").write_text(content, encoding="utf-8")
        (self.root / "README.md").write_text(final_merged_readme, encoding="utf-8")
        (self.root / catalog.CATALOG_INDEX).write_text(final_merged_index, encoding="utf-8")

        # Verify byte-for-byte README and catalog.json match and full check WITHOUT re-rendering.
        taxonomy, projects = self.load()
        self.assertEqual(final_merged_readme, catalog.render_readme(self.root, taxonomy, projects))
        self.assertEqual(final_merged_index, catalog.render_catalog_json(self.root, taxonomy, projects))
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
