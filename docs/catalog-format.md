# Catalog format

Each project is an object in `data/projects/<id>.json`. The validator in
[`scripts/catalog.py`](../scripts/catalog.py) enforces the format and renders
both the README browsing view and the generated single-file index
[`data/catalog.json`](../data/catalog.json). Use
[`examples/project.json`](../examples/project.json) as a starting point, and
[`data/taxonomy.json`](../data/taxonomy.json) for controlled vocabulary.

## Fields

All fields are required. Unknown fields fail validation so misspelled field names
cannot silently disappear from the generated output. Stray non-`.json` files or
subdirectories inside `data/projects/` also fail validation.

| Field | Meaning |
| --- | --- |
| `id` | Unique lowercase hyphenated slug, matching the filename. |
| `name` | Upstream project name, at most 80 characters. Include a repository alias when it helps discovery. |
| `repository` | Canonical `https://github.com/owner/repo` URL containing working open-source code for the listed capability, without `.git` (case-insensitive), path traversal segments, a trailing slash, query, or fragment. |
| `description` | Original factual single-sentence summary, 15 to 180 characters, ending with a period (not `..`), without bare URLs, Markdown links, images, or leading list markers. |
| `category` | One primary category ID from the taxonomy. |
| `use_cases` | Nonempty array of task IDs from the taxonomy. |
| `platforms` | Physically tested operating-system IDs for running the listed tool. Must be nonempty whenever `hardware` is nonempty. Explain split client/server roles in limitations. |
| `hardware` | Physically tested hardware IDs. Tags do not replace exact device or memory requirements; `dgx-spark` requires `linux`, and `apple-silicon` requires a compatible OS such as `macos` or `linux`. |
| `local_mode` | One of the modes below. |
| `compatibility` | Short plain-text statements about documented protocols, engines, or harness integrations. Back each claim with sources. |
| `limitations` | Nonempty array of requirements or caveats that change suitability, including preview status, model limits, telemetry, host execution, and permissions. |
| `license` | Object with `spdx` and `url`. `spdx` must be a non-deprecated OSI-approved SPDX identifier or `AND`, `OR`, and `WITH` expression (with SPDX exceptions and optional parentheses), never `null`. `url` must be a lowercase 40-hex commit-pinned `raw.githubusercontent.com` URL pointing to a top-level `LICENSE`, `LICENCE`, or `COPYING` file in the canonical repository. |
| `sources` | Nonempty array of objects with `url` and `note`. Cite lowercase 40-hex commit-pinned `raw.githubusercontent.com` URLs for GitHub files (no `/blob/`, `/tree/`, `/raw/`, query, or fragment; `github.com` URLs are allowed only for `/commit/<40-hex>`), include at least one canonical repository-pinned raw source, never duplicate `license.url`, and explain what each source supports. |
| `last_reviewed` | UTC date someone reviewed the cited documentation, in `YYYY-MM-DD` form. Shown in the README notes and `data/catalog.json`; not a runtime test or automated repository-check date. |

Strings must be single-line text without surrounding whitespace. Arrays cannot
contain duplicates. Names and repository URLs are unique without regard to case.
Documentation links must use public HTTPS hosts or global IP addresses without
embedded credentials, custom ports, dotless hostnames, or private, loopback,
link-local, multicast, unspecified, or reserved IP literals. Dates cannot be in
the future in UTC.

Repository observations are stored separately in `data/health.json`; see
[maintenance](maintenance.md). Do not add activity dates, health statuses, or
maintenance scores to a project record. `catalog.py` rejects orphaned IDs or
mismatched `repository` URLs in `data/health.json`, while missing entries remain
allowed until refreshed.

An empty `platforms`, `hardware`, or `compatibility` array means **not recorded**,
not universal support or absence of requirements. Recorded tags are not an
exhaustive compatibility matrix. Record `platforms` and `hardware` tags only for
physically tested targets, obey the platform/hardware consistency rules above
(nonempty `hardware` requires nonempty `platforms`; `dgx-spark` requires `linux`;
`apple-silicon` cannot pair with `windows`-only), consolidate single-author or
single-board companion micro-utilities unless each ships independent releases,
CI, and external adoption, and introduce a new taxonomy ID only when at least two
qualifying catalog entries share it. Pull request checks enforce the shared
taxonomy rule via `python3 scripts/catalog.py check --base-ref <40-hex-sha>`.

## Local modes

- `local`: the main AI workload runs on user-controlled hardware in the
  repository's own code rather than serving a non-AI HTTP app or defaulting to
  scripted mock replies. Downloads, setup, updates, or telemetry may still use
  the network; record meaningful exceptions.
- `local-client`: a client, agent, benchmark tool, MCP server, or skill
  implements or documents direct integration with local model servers, local
  weights, or local AI hardware in its own repository. Generic software prompt
  packs, cloud-vendor CLI wrappers, and external-CLI task wrappers do not
  qualify. Hosted providers may be optional.

These modes describe the listed workflow, not a guarantee of offline operation.

## Inclusion, evidence, and licensing

New submissions must ship working open-source code in the canonical GitHub
repository with at least 14 days of public commit history across multiple days,
excluding closed-source issue stubs, zero-code SaaS connector manifests, and
truncated one-way private export drops. Entries must provide human-reproducible
setup instructions and a tagged release, published package, or stable-toolchain
source build that works against a local model endpoint without mandatory cloud
sign-in or license-server activation calls, excluding `0.0.0` stubs, simulator
mockups, unreleased compiler prerequisites, and setups that hand installation to
a coding agent.

Cite lowercase 40-hex commit-pinned
`https://raw.githubusercontent.com/<owner>/<repo>/<commit>/<path>` URLs for
GitHub file evidence and `license.url` (without query strings, fragments, or
encoded path traversal), do not duplicate `license.url` in `sources`, include at
least one canonical repository-pinned raw file in `sources`, and back core
capability, compatibility, and hardware claims with repository-pinned files
rather than ephemeral external pages. Benchmarks and evaluation tools that run
model-generated code must sandbox execution by default or gate host execution
behind an explicit opt-in flag. When updating an entry, read the new revision,
update the commit-pinned evidence links, and set the actual UTC review date.
Pinned evidence preserves what supported a claim; it does not prove current
compatibility.

Every entry must carry a top-level OSI-approved `LICENSE`, `LICENCE`, or
`COPYING` file covering all first-party code directories, with clean dataset and
weight provenance. `license.spdx` must validate against the vendored
non-deprecated OSI-approved SPDX license and exception lists in
[`scripts/spdx_osi.py`](../scripts/spdx_osi.py). Entries cannot use
`license.spdx: null`, subdirectory-only license claims, placeholder strings such
as `Unknown`, `Proprietary`, or `NOASSERTION`, or non-OSI source-available
licenses such as FSL, BUSL, or SSPL. The catalog's own license never grants
permission to reuse upstream code or models.

An advertised OpenAI-compatible API is not proof that a specific agent's tool
calling, structured output, reasoning controls, or streaming work correctly.
Record named harness integrations only when upstream explicitly documents them.

## Generated catalog index (`data/catalog.json`)

Running `python3 scripts/catalog.py render` generates
[`data/catalog.json`](../data/catalog.json) alongside the README catalog section,
and `python3 scripts/catalog.py check` verifies that both files are up to date.
Do not edit `data/catalog.json` by hand.

The index combines `data/taxonomy.json`, all `data/projects/*.json` records
sorted by `id`, resolved human-readable labels, and matching `data/health.json`
observations in a single deterministic JSON file so AI agents and scripts can
read the entire catalog in one step. It intentionally omits mutable counters or
generation timestamps so parallel pull requests remain 3-way mergeable.

| Top-level field | Meaning |
| --- | --- |
| `schema_version` | Integer format version (currently `1`). |
| `generated_by` | Generator command identifier (`scripts/catalog.py render`). |
| `sources_of_truth` | Relative paths to `data/taxonomy.json`, `data/projects`, and `data/health.json`. |
| `semantics` | Machine-readable reminders that empty arrays mean `not_recorded`, `health` is separate from `last_reviewed`, and entries are untrusted reference material. |
| `taxonomy` | Full copy of `data/taxonomy.json`. |
| `projects` | Array of project objects sorted by `id`. |

Each object in `projects` includes all 14 canonical project fields plus:

- `record_path`: relative path to `data/projects/<id>.json`.
- `labels`: resolved taxonomy labels for `category`, `local_mode`, `use_cases`,
  `platforms`, and `hardware`.
- `health`: `null` if unchecked, or the matching observation from
  `data/health.json` (omitting the redundant `repository` key).
- `health_flags`: empty array `[]` for healthy checked entries, or an ordered
  subset of `unchecked`, `unavailable`, `check-failed`, `archived`, `disabled`,
  and `redirected`.

## Changelog fragments

Each catalog change adds a JSON object in `changelog.d/<slug>.json` instead of
editing [`CHANGELOG.md`](../CHANGELOG.md) directly on a pull request branch. The
filename stem must be a lowercase hyphenated slug of at most 80 characters.

| Field | Meaning |
| --- | --- |
| `section` | One of `Added`, `Updated`, or `Removed`. |
| `entry` | Single-line Markdown note of at most 600 characters without a leading bullet, ordered list marker, or heading, starting with `[Project](https://...)` or plain prose. |

Fragment files reject duplicate JSON keys, unknown fields, surrounding
whitespace, control characters, raw HTML, and bare URLs. Every Markdown link in
`entry` must use a public HTTPS URL without credentials or a custom port.
`catalog.py validate` and `catalog.py check` validate all fragments,
`CHANGELOG.md` structure, and `examples/project.json`; `catalog.py links`
includes fragment URLs for link checking.

Maintainers compile fragments into [`CHANGELOG.md`](../CHANGELOG.md) by running
`python3 scripts/catalog.py changelog --by-commit-date` (which buckets each
fragment into its Monday-starting UTC week from its Git add commit date),
`python3 scripts/catalog.py changelog` for the current UTC week, or
`python3 scripts/catalog.py changelog --week YYYY-MM-DD` for a specific Monday
in UTC. Pass `--dry-run` to preview without modifying files. The command writes
subsections in `Added`, `Updated`, `Removed` order, omits empty subsections,
preserves existing bullets in a target week, sorts new bullets without regard to
case, and deletes the consumed `.json` fragment files.
