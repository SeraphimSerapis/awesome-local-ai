# Contributing

Submit a project, improve an entry, or report a broken link through a pull request.
Self-submissions are welcome. You do not need a minimum number of stars, a release
badge, or a paid listing.

## What belongs here

A core entry must help people run, use, evaluate, or maintain AI on their own
hardware. Local machines and self-hosted clusters both count. Skills and MCP
servers belong when they support that workflow; a local process alone does not
make a cloud service a local AI tool.

Cloud-dependent integrations can appear in the separate cloud section if their
role in an agent workflow is clear. Mark them `cloud-dependent` and explain
credentials, network access, and possible costs.

Projects should have:

- A public repository with useful setup or usage instructions.
- A specific use case and a factual description, not marketing claims.
- Evidence for hardware requirements and compatibility claims.
- Identifiable licensing, or an explicit licensing uncertainty that a maintainer
  agrees to list. Unclear licenses must use `null` and a visible limitation.
- Visible preview status, model restrictions, telemetry, permissions, or other
  requirements that affect a user's decision.

Early-stage projects are welcome when their status and limitations are clear.
Listings are not endorsements, security audits, or runtime certifications.

## Add or update an entry

1. Copy [`examples/project.json`](examples/project.json) to
   `data/projects/<project-id>.json`, or edit an existing entry.
2. Replace the example values. Use a lowercase hyphenated ID and the canonical
   repository URL. Pick IDs from [`data/taxonomy.json`](data/taxonomy.json).
3. Read the upstream documentation. Include source URLs and a note explaining
   what each source supports. Record the date you actually reviewed those sources.
4. Add a short note to the current Monday-starting UTC week in
   [`CHANGELOG.md`](CHANGELOG.md), under Added, Updated, or Removed. Create the
   week's `## Week of YYYY-MM-DD` heading at the top when needed. Describe catalog
   changes, not upstream releases; explain removals. Omit empty subsections.
5. Run these commands with Python 3.11 or newer:

   ```sh
   python3 scripts/catalog.py validate
   python3 scripts/catalog.py render
   python3 scripts/catalog.py check
   python3 -m unittest discover -s scripts -p 'test_*.py'
   ```

6. Open a PR with the record, changelog, and generated README changes. Explain the use case,
   evidence, and any limits in the PR template. Flag ownership or affiliation.

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

Remote URLs from changed project records get an advisory PR check. Timeouts,
authentication requirements, and rate limits can make working links look broken,
so reviewers must inspect its report. Weekly and manual runs check the whole
catalog and documentation; broken links fail those runs. Fix a moved link or
record the investigation rather than deleting a useful entry after one timeout.

Remote checks use [`.lychee.toml`](.lychee.toml). Pinned GitHub file links are
checked at the same commit and path on `raw.githubusercontent.com`; commit links
use the GitHub API. Repository links can fall back to the API using the workflow's
read-only GitHub token. This checks that the targets exist, not that GitHub's HTML
pages are available. Missing targets and failed API or raw-file requests still
fail the full scan. No server-error status is accepted as success.

Passing CI does not establish factual accuracy. Reviewers check:

- Does the project meet the scope and have a distinct use case?
- Does the upstream documentation support the description and compatibility?
- Are model, hardware, maturity, privacy, and licensing limits visible?
- Are the submission and generated changes limited to the intended entry?

Maintainers make the final inclusion decision. CI does not auto-merge or install
submitted projects. Maintain the same standard for the maintainer's own projects.

After the first GitHub CI run, protect `main` and require PR review plus the
catalog and documentation checks before merge. Configure those rules in GitHub;
workflow files alone do not prevent merging a failed PR. Keep the upstream link
check advisory on PRs.

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
change with evidence and a changelog note. Routine health-only PRs do not need
changelog notes. See [maintenance](docs/maintenance.md) for fields, local refresh
commands, and workflow permissions.

## Contributor licensing

By submitting original catalog or documentation contributions, you agree to
dedicate them under [CC0-1.0](LICENSE). Contributions to `scripts/` or
`.github/workflows/` use the [MIT license](scripts/LICENSE). Submit only material
you have the right to contribute. There is no separate contributor license agreement.

Write short original summaries and link to evidence instead of copying upstream
documentation. Upstream software and model licenses do not change when we list them.
