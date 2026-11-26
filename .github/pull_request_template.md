# Project submission or update

## Project or change

What does this help someone do with local AI? State whether it runs local model
workloads directly (`local`) or integrates directly with local model servers,
weights, or hardware (`local-client`, `mcp`, `skills`).

## Evidence and limitations

Link to commit-pinned upstream documentation supporting the description,
platforms, hardware, compatibility, and license. List preview or experimental
status, model or memory limits, telemetry, update checks, bundled-asset `NOTICE`
licenses, host execution, or OS permissions.

## Affiliation

Do you maintain, work on, or have a commercial connection to this project?
Self-submissions are welcome; disclose the connection here.

## Checklist

- [ ] I read [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] Canonical public GitHub repository with working open-source code, direct local-AI execution or local-runtime integration, and runnable setup without mandatory cloud sign-in (Criteria 1 to 3).
- [ ] Public commit history spans at least 14 days across multiple UTC days (Criterion 4).
- [ ] Top-level OSI-approved `LICENSE` or `COPYING` file recorded as a valid SPDX identifier or expression (no `null` or non-OSI source-available licenses), with `license.url` pinned to a lowercase 40-hex `raw.githubusercontent.com` commit (Criterion 5).
- [ ] `platforms` and `hardware` reflect physically tested targets, companion repos are consolidated unless independent, and any new taxonomy ID is shared by at least two qualifying entries (Criterion 6).
- [ ] GitHub file `sources` use lowercase 40-hex commit-pinned `raw.githubusercontent.com` URLs without duplicating `license.url`, benchmarks sandbox or opt-in host execution, and `limitations` discloses telemetry, update checks, `NOTICE` terms, and restrictions (Criterion 7).
- [ ] I recorded an actual UTC `last_reviewed` date after reading the cited sources.
- [ ] I added a changelog fragment in `changelog.d/` and left `CHANGELOG.md` untouched (health-only refreshes skip this step).
- [ ] I regenerated `README.md` and `data/catalog.json` (`python3 scripts/catalog.py render`) and ran `python3 scripts/catalog.py verify`, or explained why I could not.
- [ ] I agree to the contributor licensing terms in [CONTRIBUTING.md](../CONTRIBUTING.md).
