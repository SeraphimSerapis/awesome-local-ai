# Review dates and repository health

The catalog records two different kinds of evidence:

- **Documentation reviewed:** `last_reviewed` in a project record. A human read
  the cited upstream sources on that date. It is not a runtime test.
- **Repository checked:** a dated observation of public GitHub repository metadata
  in [`data/health.json`](../data/health.json). It does not update the human review date.

Last observed push is GitHub's repository-level `pushed_at`, which advances on
pushes to any branch or tag, including unmerged bot branches. The collector also
records `last_default_branch_commit` from the latest commit on the upstream
default branch, and the generated README prints both dates whenever they differ.
Neither timestamp establishes human documentation review, active maintenance,
security, quality, or compatibility, and inactivity does not establish
abandonment. Archived and disabled are GitHub flags, not catalog inclusion
decisions.

## Snapshot format

The snapshot is an object keyed by catalog project ID. Each observation has these
fields; unknown or misspelled fields fail validation.

| Field | Meaning |
| --- | --- |
| `repository` | The catalog URL that was requested. Observations for a different URL or removed ID are not used. |
| `checked_at` | Latest check-attempt date, `YYYY-MM-DD` in UTC. |
| `status` | `reachable`, `unavailable`, or `check-failed`; defined below. |
| `detail` | A short failure explanation, or `null` after success. |
| `last_successful_check` | Date the retained public metadata was fetched successfully, or `null` if never observed. |
| `canonical_repository` | GitHub's reported repository URL, or `null` before a successful check. A changed URL flags a redirect for review. |
| `archived` | GitHub's archived flag, or `null` before a successful check. |
| `disabled` | GitHub's disabled flag, or `null` before a successful check. |
| `last_push` | GitHub's `pushed_at` UTC timestamp, or `null` if none was reported or never observed. |
| `last_default_branch_commit` | Latest commit UTC timestamp on the upstream `default_branch`, or `null` if unavailable, empty, disabled, or never observed. |

`reachable` means the API returned valid public repository metadata. It does not
mean a tool was installed or tested. `unavailable` covers HTTP 404, 410, or 451,
or a repository reported private; it does not prove deletion. Authentication,
rate-limit, server, network, TLS, or malformed-response failures are `check-failed`.

Failed or unavailable checks preserve the prior successful public metadata and
its date. The README labels it as retained rather than freshly verified. Private
metadata is never copied into the snapshot, even if a local token can access it.
Entries without a matching observation show "not checked yet."

## Local refresh

Only run a refresh when network access is authorized. It reads public metadata
through GitHub's REST API, not upstream source code or setup commands:

```sh
python3 scripts/health.py
python3 scripts/catalog.py render
python3 scripts/catalog.py check
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Python 3.11+ and its standard library are sufficient. `GH_TOKEN` or `GITHUB_TOKEN`
can supply an existing GitHub token for API rate limits; never commit credentials.
Requests stay on `api.github.com`, including redirects, and TLS verification stays
enabled. If Python has no working trust store, configure a trusted CA bundle via
`SSL_CERT_FILE` rather than disabling certificate verification.

The collector updates attempt dates even when checks fail and returns success
after writing a valid snapshot; inspect its status counts and PR diff. Invalid
catalog/snapshot data or a failed file write stops the refresh. The snapshot is
replaced only after a complete write. Changed or removed catalog URLs do not
inherit unrelated observations.

## Weekly workflow

[`health.yml`](../.github/workflows/health.yml) runs on Mondays at 07:43 UTC or by
manual dispatch on the default branch. Scheduled runs can be delayed by GitHub.
It uses pinned actions and proposes only `data/health.json` and the generated
README on `automation/catalog-health`. It opens or updates a PR and dispatches
catalog CI. It never removes entries or edits `last_reviewed`. The existing
weekly upstream-link check remains separate.

The bot uses `GITHUB_TOKEN` with contents and pull-request write permissions to
publish its branch and PR. Repository settings must permit Actions to create
pull requests. Whenever an open `automation/catalog-health` pull request exists,
including same-day reruns after a transient CI failure, its actions-write
permission dispatches `checks.yml` against the bot branch. Pull requests created
with `GITHUB_TOKEN` do not start ordinary `pull_request` workflows
automatically, so the explicit dispatch runs CI without a personal token.

### Automatic merging of routine refreshes

The default-branch health workflow waits for the exact CI run ID returned by the
dispatch API, then runs the merge gate. It does not rely on `workflow_run` events,
which GitHub suppresses for bot-triggered activity. It merges only when:

- The PR belongs to `github-actions[bot]`, targets the default branch, and uses
  `automation/catalog-health` in this repository, not a fork.
- The `Catalog / ubuntu-latest / Python 3.11`,
  `Catalog / windows-latest / Python 3.13`, and `Documentation` CI jobs passed
  on the exact PR head commit, and every job in the dispatched run completed
  with success. `Upstream links` runs in advisory mode on
  `automation/catalog-health` so unrelated third-party timeouts do not block
  routine repository snapshots.
- The head includes the current default branch and changes only `data/health.json`
  and the generated README. The README must exactly match regeneration from the
  trusted default-branch code, catalog, and manual README sections.
- The snapshot covers every catalog entry with a successful check dated today in
  UTC, no archived or disabled repositories, and no redirects.

The gate reads candidate files as data; it never checks out or runs code from
the bot branch. It checks the head again before merging and pins the merge to
the tested commit. If the base or head advances, the refresh needs another run.
Flagged snapshots and unexpected changes stay open for manual review; the gate
reports the reason in its workflow log. Failed CI or a timeout stops the workflow
before it invokes the merge gate.

The merge uses the normal GitHub merge operation without administrator bypass or
repository-wide native auto-merge. Merges made with `GITHUB_TOKEN` do not
trigger another push workflow; verification comes from the dispatched catalog CI
run before merging. Project submissions remain manual.

### Token and ruleset decision

- **Decision.** Keep `.github/workflows/health.yml` on the built-in
  `GITHUB_TOKEN` and keep `required_approving_review_count` at `0` in the
  `Protect main` ruleset rather than operating a custom GitHub App.
- **Trade-offs.** This avoids GitHub App registration and private-key rotation on
  a solo-maintained repository where `SeraphimSerapis` is the sole collaborator
  with merge access and cannot self-approve pull requests under
  `required_approving_review_count: 1`. Because `github-actions[bot]` cannot
  approve pull requests or appear in ruleset `bypass_actors`, human review on
  project, script, workflow, and documentation pull requests stays manual while
  `Protect main` blocks direct pushes, force-pushes, branch deletion, unresolved
  review threads, and failing status checks.
- **Condition to revisit.** Revisit adding a repository-scoped GitHub App in
  `bypass_actors` and raising `required_approving_review_count` to `1` if a
  second maintainer with merge permissions joins the repository.

Review flagged repositories and failed checks before accepting a snapshot.
Corrections or removals need a separate catalog change with upstream evidence and
a `changelog.d/<slug>.json` fragment. Maintainers compile fragments into the
[weekly changelog](../CHANGELOG.md) with `python3 scripts/catalog.py changelog`,
using Monday-starting UTC weeks that describe catalog changes rather than
upstream releases. Routine health-only PRs skip changelog fragments so the
automatic merge gate stays limited to `data/health.json` and `README.md`.
