# SPDX-License-Identifier: MIT
PYTHON ?= python3
AUDIT_ARGS ?=
CHANGELOG_ARGS ?= --by-commit-date

.PHONY: help verify render check test status audit health changelog

help:
	@printf "Targets:\n"
	@printf "  verify     Run catalog checks, unit tests, and available local linters\n"
	@printf "  render     Regenerate README.md and data/catalog.json\n"
	@printf "  check      Validate catalog, health, changelog, and generated outputs\n"
	@printf "  test       Run Python unit tests in scripts/\n"
	@printf "  status     Print offline maintainer dashboard\n"
	@printf "  audit      Run compliance and staleness auditor (pass AUDIT_ARGS=...)\n"
	@printf "  health     Refresh public GitHub metadata in data/health.json\n"
	@printf "  changelog  Compile changelog.d/ fragments into CHANGELOG.md\n"

verify:
	$(PYTHON) scripts/catalog.py verify

render:
	$(PYTHON) scripts/catalog.py render

check:
	$(PYTHON) scripts/catalog.py check

test:
	$(PYTHON) -m unittest discover -s scripts -p 'test_*.py'

status:
	$(PYTHON) scripts/catalog.py status

audit:
	$(PYTHON) scripts/audit.py $(AUDIT_ARGS)

health:
	$(PYTHON) scripts/health.py

changelog:
	$(PYTHON) scripts/catalog.py changelog $(CHANGELOG_ARGS)
