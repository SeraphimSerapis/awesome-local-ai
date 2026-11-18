# Contributing

Submit a project, improve an entry, or report a broken link through a pull request.
Self-submissions are welcome. You do not need a minimum number of stars, a release
badge, or a paid listing.

## What belongs here

A core entry must help people run, use, evaluate, or maintain AI on their own
hardware. Local machines and self-hosted clusters both count. Skills and MCP
servers belong when they support that workflow; a local process alone does not
make a cloud service a local AI tool.

Every new submission must meet seven acceptance criteria:

1. **Working open-source code in the canonical repository.** The linked GitHub
   repository must contain the working source code for the listed capability.
   Closed-source issue stubs, zero-code SaaS connector manifests, and truncated
   one-way private export drops do not qualify.
2. **Direct local-AI execution or local-runtime integration.** Entries marked
   `local` must run model inference, multimodal processing, or local AI cluster
   and systems workloads in their own code rather than serving non-AI HTTP apps
   or defaulting to scripted mock replies. Entries in `local-client`, `skills`,
   and `mcp` must implement or document direct configuration for local model
   servers, local weights, or local AI hardware in their own repository. Generic
   software prompt packs, cloud-vendor CLI wrappers, external-CLI task wrappers,
   and cloud-only service connectors do not qualify.
3. **Runnable distribution without mandatory cloud sign-in.** Projects must
   provide human-reproducible setup steps and ship a tagged release, published
   package, or source build on a stable toolchain. Version `0.0.0` stubs,
   simulator mockups, unreleased compiler prerequisites, and setups that delegate
   installation to a coding agent do not qualify. Official builds for `local`
   and `local-client` tools must work against a local model endpoint without
   mandatory cloud sign-in or license-server activation calls.
4. **Fourteen-day public commit history.** New submissions must have at least 14
   days of public commit history across multiple days before submission,
   excluding same-day or single-weekend code drops.
5. **Top-level OSI-approved license and clean provenance.** Repositories must
   carry a top-level OSI-approved `LICENSE` or `COPYING` file covering all
   first-party code directories, with clean dataset and weight provenance. New
   submissions cannot use `license.spdx` set to `null`, subdirectory-only
   license claims, or seat-capped commercial source-available licenses in core
   categories.
6. **Companion-repo consolidation, tested tags, and shared taxonomy IDs.**
   Single-author or single-board micro-utilities and host scripts belong in one
   consolidated entry unless each repository ships independent releases, CI, and
   external adoption. Record `platforms` and `hardware` tags only for physically
   tested targets, and add a new taxonomy ID only when at least two qualifying
   entries share it.
7. **Commit-pinned raw evidence and safe benchmark defaults.** GitHub file
   evidence and `license.url` must use 40-hex commit-pinned
   `raw.githubusercontent.com` URLs, and `sources` must not duplicate
   `license.url`. Back core claims with repository-pinned files rather than
   ephemeral external pages, and require code-running benchmarks to sandbox
   execution or gate host execution behind an explicit opt-in flag.

Projects must also state visible preview caveats, model restrictions, telemetry,
permissions, and any other limits that affect a user's decision. Listings are
not endorsements, security audits, or runtime certifications.

## Add or update an entry

1. Copy [`examples/project.json`](examples/project.json) to
   `data/projects/<project-id>.json`, or edit an existing entry.
2. Replace the example values. Use a lowercase hyphenated ID and the canonical
   repository URL. Pick existing IDs from
   [`data/taxonomy.json`](data/taxonomy.json) unless at least two qualifying
   entries share a new taxonomy ID.
3. Read the upstream documentation. Include 40-hex commit-pinned
   `raw.githubusercontent.com` URLs for GitHub files and a note explaining what
   each source supports without repeating `license.url` in `sources`. Record the
   UTC date you actually reviewed those sources.
4. Add a changelog fragment at `changelog.d/<slug>.json` with `section` set to
   `Added`, `Updated`, or `Removed` and a single-line `entry` without a leading
   bullet:

   ```json
   {
     "section": "Added",
     "entry": "[Example Project](https://github.com/example/project), short summary of what it does locally."
   }
   ```

   Describe catalog changes, not upstream releases, and explain removals. Leave
   [`CHANGELOG.md`](CHANGELOG.md) untouched in your pull request so parallel
   branches do not conflict. Maintainers compile fragments into weekly sections
   with `python3 scripts/catalog.py changelog`.
5. Run these commands with Python 3.11 or newer:

   ```sh
   python3 scripts/catalog.py validate
   python3 scripts/catalog.py render
   python3 scripts/catalog.py check
   python3 -m unittest discover -s scripts -p 'test_*.py'
   ```

6. Open a PR with the record, changelog fragment, and generated README changes.
   Explain the use case, evidence, and any limits in the PR template. Flag
   ownership or affiliation.

The scripts use only Python's standard library. The format reference is in
[`docs/catalog-format.md`](docs/catalog-format.md). Edit catalog records rather
than the README's generated block. Changes outside that block are fine.

If you cannot run the commands, submit the record and say so. A maintainer can
help with generation and checks before merge.

## Checks and review

CI runs the catalog checks, tests, Markdown linting, spelling, and offline link
checks. For the other checks locally:

```sh
npx --yes markdownlint-cli2@0.18.1
typos
lychee --offline --include-fragments './**/*.md'
```

The CI versions of Typos and Lychee are pinned in
[the workflow](.github/workflows/checks.yml). Install those versions when matching
CI locally. Add a technical word to `.typos.toml` only if it is correct; do not
ignore an entire document to silence a typo.

Remote URLs from changed project records, changelog fragments, and Markdown
documentation get an advisory PR check. Timeouts, authentication requirements,
and rate limits can make working links look broken, so reviewers must inspect
its report. Weekly, push, and manual runs on `main` check the whole catalog and
documentation; broken links fail those runs. Fix a moved link or record the
investigation rather than deleting a useful entry after one timeout.

Remote checks use [`.lychee.toml`](.lychee.toml). Pinned GitHub blob links
remap to the same commit and path on `raw.githubusercontent.com` after stripping
query strings and line fragments. Commit and repository links on `github.com`
authenticate directly with the workflow's read-only GitHub token. This checks
that the targets exist rather than depending on GitHub's HTML renderer. Missing
targets and server errors still fail the full scan on `main`.

Passing CI does not establish factual accuracy. Reviewers check:

- Does the project meet all seven acceptance criteria and have a distinct use case?
- Does repository-pinned upstream documentation support the description and compatibility?
- Are model, hardware, maturity, privacy, host-execution, and licensing limits visible?
- Are the submission and generated changes limited to the intended entry?

Maintainers make the final inclusion decision. CI does not auto-merge or install
submitted projects. Maintain the same standard for the maintainer's own projects.

An active GitHub ruleset protects `main` by requiring pull requests with
resolved review threads, blocking force-pushes and branch deletion, and
requiring the `Catalog / ubuntu-latest / Python 3.11`,
`Catalog / windows-latest / Python 3.13`, and `Documentation` status checks
before merge. Because `health.yml` opens and merges routine snapshot pull
requests with `GITHUB_TOKEN`, which cannot approve its own pull request or join
ruleset bypass actors, the ruleset leaves the required approving review count at
zero and maintainers enforce human review manually on project, script, workflow,
and documentation pull requests. Keep the `Upstream links` check advisory on
pull requests.

## Review dates and repository observations

Set `last_reviewed` only after reading the cited upstream sources. A repository
check or recent push is not a documentation review. Automated observations live
in `data/health.json`, not in project records; contributors adding an entry do
not need to fetch or edit that snapshot.

The weekly health workflow proposes snapshot and README updates in a PR. Routine
refreshes can merge automatically under the [health safety gate](docs/maintenance.md#automatic-merging-of-routine-refreshes).
Review unavailable, archived, disabled, and redirected repositories before merging.
Investigate failed checks instead of treating them as deletion or abandonment.
If an entry needs a correction or removal, make a separate reviewed catalog
change with evidence and a changelog fragment. Routine health-only PRs do not
need changelog fragments. See [maintenance](docs/maintenance.md) for fields,
local refresh commands, and workflow permissions.

## Contributor licensing

By submitting original catalog or documentation contributions, you agree to
dedicate them under [CC0-1.0](LICENSE). Contributions to `scripts/` or
`.github/workflows/` use the [MIT license](scripts/LICENSE). Submit only material
you have the right to contribute. There is no separate contributor license agreement.

Write short original summaries and link to evidence instead of copying upstream
documentation. Upstream software and model licenses do not change when we list them.
