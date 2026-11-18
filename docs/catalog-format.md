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
| `repository` | Canonical `https://github.com/owner/repo` URL, without `.git`, a trailing slash, query, or fragment. |
| `description` | Original factual one-sentence summary, at most 180 characters. |
| `category` | One primary category ID from the taxonomy. |
| `use_cases` | Nonempty array of task IDs from the taxonomy. |
| `platforms` | Documented operating-system IDs for running the listed tool. Explain split client/server roles in limitations. |
| `hardware` | Relevant documented hardware IDs. Tags do not replace exact device or memory requirements. |
| `local_mode` | One of the modes below. |
| `compatibility` | Short statements about documented protocols, engines, or harness integrations. Back each claim with sources. |
| `limitations` | Requirements or caveats that change suitability, including preview status, model limits, telemetry, and permissions. |
| `license` | Object with `spdx` and `url`. Use an SPDX identifier or simple AND/OR expression and link to the license or package declaration. |
| `sources` | Nonempty array of objects with `url` and `note`. Explain what each upstream source supports. |
| `last_reviewed` | Date someone reviewed the cited documentation, in `YYYY-MM-DD` form. Shown in the README; not a runtime test or automated repository-check date. |

Strings must be single-line text without surrounding whitespace. Arrays cannot
contain duplicates. Names and repository URLs are unique without regard to case.
Documentation links must use HTTPS without embedded credentials or custom ports.
Dates cannot be in the future.

Repository observations are stored separately in `data/health.json`; see
[maintenance](maintenance.md). Do not add activity dates, health statuses, or
maintenance scores to a project record.

An empty `platforms`, `hardware`, or `compatibility` array means **not recorded**,
not universal support or absence of requirements. Recorded tags are not an
exhaustive compatibility matrix. Only add claims supported by evidence.

## Local modes

- `local`: the main workload runs on user-controlled hardware. Downloads, setup,
  updates, or telemetry may still use the network; record meaningful exceptions.
- `local-client`: a client, agent, benchmark tool, or skill can work with local
  infrastructure. A harness still needs a model, and a benchmark still needs an
  endpoint. Hosted providers may be optional.
- `cloud-dependent`: the listed workflow relies on cloud services. It appears
  outside the core categories in the cloud section, with explicit requirements.
  A collection may contain some local-only components; assess the selected component.

These modes describe the listed workflow, not a guarantee of offline operation.
If a mixed collection has no clear primary local workflow, use `cloud-dependent`
and explain the distinction.

## Evidence and licensing

Prefer upstream READMEs, configuration guides, license texts, or manifests.
The seed records link directly to raw evidence and license files at the reviewed
upstream commit. Repository links still lead to the current project. When updating an entry, read
the new revision, update the evidence links, and set the actual review date.
Pinned evidence preserves what supported a claim; it does not prove current compatibility.

Use `license.spdx: null` when the terms are unclear, and explain the uncertainty
in `limitations`. Link to the repository or declaration being reviewed, rather
than inventing a license URL. A maintainer must review this exception before merge.
The catalog's own license never grants permission to reuse upstream code or models.

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
