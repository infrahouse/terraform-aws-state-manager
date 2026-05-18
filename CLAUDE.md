# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## First Steps

**Your first tool call in this repository MUST be reading .claude/CODING_STANDARD.md.
Do not read any other files, search, or take any actions until you have read it.**
This contains InfraHouse's comprehensive coding standards for Terraform, Python, and general formatting rules.

## Module Overview

This is `terraform-aws-state-manager` — an InfraHouse Terraform module that creates an IAM role
for managing Terraform state files in S3 with DynamoDB locking. It supports read-only and read-write
permission modes, controlled via the `read_only_permissions` variable.

Current version: tracked in `.bumpversion.cfg` and `locals.tf` (`module_version`).

## Commands

```bash
make bootstrap        # Install Python dependencies (requires virtualenv)
make format           # Format Terraform + Python (terraform fmt, black)
make lint             # Check Terraform formatting (--check mode)
make test             # Run full pytest suite
make test-keep        # Run tests, keep AWS resources after (for debugging)
make test-clean       # Run tests, destroy resources after (use before PRs)
make clean            # Remove test artifacts
make release-patch    # Bump patch version and update CHANGELOG
make release-minor    # Bump minor version and update CHANGELOG
make release-major    # Bump major version and update CHANGELOG
```

Run a single test:
```bash
pytest -xvvs tests/test_module.py::test_module
pytest -xvvs tests/test_module.py::test_module_defaults
```

## Architecture

The module creates an IAM role with two IAM policies (read-only and read-write) for S3 state access
and DynamoDB lock table access. The read-write policy attachment is conditional on
`read_only_permissions = false`.

Key files:
- `main.tf` — IAM role, policies, and policy attachments
- `data_sources.tf` — IAM policy documents (assume role, RO permissions, RW permissions)
- `locals.tf` — `module_version` and resource tags
- `variables.tf` / `outputs.tf` — module interface

## Testing

Tests are pytest-based integration tests that deploy real AWS infrastructure using `pytest-infrahouse`
fixtures. Tests parametrize across AWS provider versions (`~> 5.11`, `~> 6.0`) and multiple
configurations (name lengths, read-only mode).

- Test root module: `test_data/state-manager/`
- Test code: `tests/test_module.py`
- Fixtures/config: `tests/conftest.py` (sets `TERRAFORM_ROOT_DIR = "test_data"`)
- AWS test role: `arn:aws:iam::303467602807:role/state-manager-tester`
  (configurable via `--test-role-arn`)

## Commit Messages

Conventional Commits format is enforced by a `commit-msg` hook. Valid types: `feat`, `fix`, `docs`,
`style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `security`.

## Versioning

Version is stored in two places (managed by `bumpversion`): `.bumpversion.cfg` and `locals.tf`.
The `README.md` usage example version is also bumped automatically. Do not update versions
manually — use `make release-*`.

## Files Managed Externally

These files are managed by Terraform in the `github-control` repository — do not edit directly:
- `hooks/pre-commit`, `hooks/commit-msg`
- `.terraform-docs.yml`, `mkdocs.yml`, `cliff.toml`
- `.claude/CODING_STANDARD.md`