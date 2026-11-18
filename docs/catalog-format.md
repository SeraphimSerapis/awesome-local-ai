# Catalog format

Each project is an object in `data/projects/<id>.json`. The validator in
[`scripts/catalog.py`](../scripts/catalog.py) enforces the format. Use
[`examples/project.json`](../examples/project.json) as a starting point, and
[`data/taxonomy.json`](../data/taxonomy.json) for controlled vocabulary.

## Fields

All fields are required. Unknown fields fail validation so misspelled field names
cannot silently disappear from the generated output.

| Field | Meaning |
| --- | --- |
| `id` | Unique lowercase hyphenated slug, matching the filename. |
| `name` | Upstream project name, at most 80 characters. Include a repository alias when it helps discovery. |
| `repository` | Canonical `https://github.com/owner/repo` URL containing working open-source code for the listed capability, without `.git`, path traversal segments, a trailing slash, query, or fragment. |
| `description` | Original factual one-sentence summary, at most 180 characters. |
| `category` | One primary category ID from the taxonomy. |
| `use_cases` | Nonempty array of task IDs from the taxonomy. |
| `platforms` | Physically tested operating-system IDs for running the listed tool. Explain split client/server roles in limitations. |
| `hardware` | Physically tested hardware IDs. Tags do not replace exact device or memory requirements. |
| `local_mode` | One of the modes below. |
| `compatibility` | Short statements about documented protocols, engines, or harness integrations. Back each claim with sources. |
| `limitations` | Requirements or caveats that change suitability, including preview status, model limits, telemetry, host execution, and permissions. |
| `license` | Object with `spdx` and `url`. Use a valid SPDX identifier or `AND`, `OR`, and `WITH` expression rather than placeholder words, and link to a 40-hex commit-pinned top-level `LICENSE` or `COPYING` file on `raw.githubusercontent.com`. |
| `sources` | Nonempty array of objects with `url` and `note`. Cite 40-hex commit-pinned `raw.githubusercontent.com` URLs for GitHub files without repeating `license.url`, and explain what each source supports. |
| `last_reviewed` | UTC date someone reviewed the cited documentation, in `YYYY-MM-DD` form. Shown in the README; not a runtime test or automated repository-check date. |

Strings must be single-line text without surrounding whitespace. Arrays cannot
contain duplicates. Names and repository URLs are unique without regard to case.
Documentation links must use public HTTPS hosts or global IP addresses without
embedded credentials, custom ports, dotless hostnames, or private, loopback,
link-local, multicast, unspecified, or reserved IP literals. Dates cannot be in
the future in UTC.

Repository observations are stored separately in `data/health.json`; see
[maintenance](maintenance.md). Do not add activity dates, health statuses, or
maintenance scores to a project record.

An empty `platforms`, `hardware`, or `compatibility` array means **not recorded**,
not universal support or absence of requirements. Recorded tags are not an
exhaustive compatibility matrix. Record `platforms` and `hardware` tags only for
physically tested targets, consolidate single-author or single-board companion
micro-utilities unless each ships independent releases, CI, and external
adoption, and introduce a new taxonomy ID only when at least two qualifying
catalog entries share it.

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
- `cloud-dependent`: new `cloud-dependent` submissions are retired except for
  bridges whose primary workflow connects a local model runtime to an external
  service. Legacy entries appear outside core categories in the cloud section
  with explicit credential, network, and cost requirements.

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

Cite 40-hex commit-pinned `https://raw.githubusercontent.com/<owner>/<repo>/<commit>/<path>`
URLs for GitHub file evidence and `license.url`, do not duplicate `license.url`
in `sources`, and back core capability, compatibility, and hardware claims with
repository-pinned files rather than ephemeral external pages. Benchmarks and
evaluation tools that run model-generated code must sandbox execution by default
or gate host execution behind an explicit opt-in flag. When updating an entry,
read the new revision, update the commit-pinned evidence links, and set the
actual UTC review date. Pinned evidence preserves what supported a claim; it
does not prove current compatibility.

New submissions must carry a top-level OSI-approved `LICENSE` or `COPYING` file
covering all first-party code directories, with clean dataset and weight
provenance. New submissions cannot use `license.spdx: null`, subdirectory-only
license claims, or seat-capped commercial source-available licenses in core
categories. Placeholder strings such as `Unknown`, `Proprietary`, or
`NOASSERTION` fail validation. Legacy records with `license.spdx: null` must
explain the uncertainty in `limitations` for maintainer review. The catalog's
own license never grants permission to reuse upstream code or models.

An advertised OpenAI-compatible API is not proof that a specific agent's tool
calling, structured output, reasoning controls, or streaming work correctly.
Record named harness integrations only when upstream explicitly documents them.

## Changelog fragments

Each catalog change adds a JSON object in `changelog.d/<slug>.json` instead of
editing [`CHANGELOG.md`](../CHANGELOG.md) directly on a pull request branch. The
filename stem must be a lowercase hyphenated slug of at most 80 characters.

| Field | Meaning |
| --- | --- |
| `section` | One of `Added`, `Updated`, or `Removed`. |
| `entry` | Single-line Markdown note of at most 600 characters without a leading list marker, starting with `[Project](https://...)` or plain prose. |

Fragment files reject duplicate JSON keys, unknown fields, surrounding
whitespace, control characters, raw HTML, and bare URLs. Every Markdown link in
`entry` must use a public HTTPS URL without credentials or a custom port.
`catalog.py validate` and `catalog.py check` validate all fragments, and
`catalog.py links` includes their URLs for link checking.

Maintainers compile fragments into [`CHANGELOG.md`](../CHANGELOG.md) by running
`python3 scripts/catalog.py changelog`, or
`python3 scripts/catalog.py changelog --week YYYY-MM-DD` for a specific Monday
in UTC. The command writes subsections in `Added`, `Updated`, `Removed` order,
omits empty subsections, preserves existing bullets in a target week, sorts new
bullets without regard to case, and deletes the consumed `.json` fragment files.
