# Review dates and repository health

The catalog records two different kinds of evidence:

- **Documentation reviewed:** `last_reviewed` in a project record. A human read
  the cited upstream sources on that date. It is not a runtime test.
- **Repository checked:** a dated observation of public GitHub repository metadata
  in [`data/health.json`](../data/health.json). It does not update the human review date.

Last observed push is GitHub's repository-level `pushed_at`, not the date of a
release or necessarily a code change on the default branch. Recent activity does
not establish maintenance, security, quality, or compatibility. Inactivity does
not establish abandonment. Archived and disabled are GitHub flags, not catalog
inclusion decisions.

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

`reachable` means the API returned valid public repository metadata. It does not
mean a tool was installed or tested. `unavailable` covers HTTP 404, 410, or 451,
or a repository reported private; it does not prove deletion. Authentication,
rate-limit, server, network, TLS, or malformed-response failures are `check-failed`.

Failed or unavailable checks preserve the prior successful public metadata and
its date. The README labels it as retained rather than freshly verified. Private
metadata is never copied into the snapshot, even if a local token can access it.
Entries without a matching observation show “not checked yet.”

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
publish its branch and PR. Repository/organization settings must permit Actions
to create pull requests. Its actions-write permission dispatches `checks.yml`
against the bot branch. `GITHUB_TOKEN`-created PRs trigger ordinary PR workflows
in an approval-required state; the explicit dispatch runs CI without that prompt.
No personal token is required. Enable required
reviews and checks through GitHub branch protection; workflows alone do not
enforce review.

### Automatic merging of routine refreshes

The default-branch health workflow waits for the exact CI run ID returned by the
dispatch API, then runs the merge gate. It does not rely on `workflow_run` events,
which GitHub suppresses for bot-triggered activity. It merges only when:

- The PR belongs to `github-actions[bot]`, targets the default branch, and uses
  `automation/catalog-health` in this repository, not a fork.
- All four catalog, documentation, and upstream-link CI jobs passed on the exact
  PR head commit. Missing, skipped, pending, or failed jobs block merging.
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

The merge uses the normal GitHub merge operation, without administrator bypass,
automatic approval, or changes to branch protection. Required reviews still need
a person. GitHub's repository-wide native auto-merge setting is not needed.
Merges made with `GITHUB_TOKEN` do not trigger another push workflow; verification
comes from the catalog CI run before merging. Project submissions remain manual.

Review flagged repositories and failed checks before accepting a snapshot.
Corrections or removals need a separate catalog change with upstream evidence and
a `changelog.d/<slug>.json` fragment. Maintainers compile fragments into the
[weekly changelog](../CHANGELOG.md) with `python3 scripts/catalog.py changelog`,
using Monday-starting UTC weeks that describe catalog changes rather than
upstream releases. Routine health-only PRs skip changelog fragments so the
automatic merge gate stays limited to `data/health.json` and `README.md`.
