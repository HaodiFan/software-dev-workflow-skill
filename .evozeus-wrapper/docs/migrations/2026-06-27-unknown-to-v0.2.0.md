# Wrapper Migration: unknown to v0.2.0

## Summary

Adopt EvoZeus-wrapper `v0.2.0` for `engineering-everything`.

## From wrapper version

- None. This repo previously had no `.evozeus-wrapper/wrapper.json`.

## To wrapper version

- `v0.2.0`

## Reason

The Skill already had native self-evolution gates, but it was not wrapper-managed. The wrapper harness adds source discovery, feedback Issue intake, design docs, migration logging, preflight checks, and a release-aware dashboard.

## Planned files

- `SKILL.md` append-only wrapper sections.
- `.evozeus-wrapper/wrapper.json`.
- `.evozeus-wrapper/WRAPPER.md`.
- `.evozeus-wrapper/CHANGELOG.md`.
- `.evozeus-wrapper/docs/index.md`.
- `.evozeus-wrapper/docs/design-doc-template.md`.
- `.evozeus-wrapper/docs/designs/README.md`.
- `.evozeus-wrapper/docs/designs/2026-06-27-evozeus-wrapper-adoption.md`.
- `.evozeus-wrapper/docs/migrations/README.md`.
- `.github/ISSUE_TEMPLATE/skill-feedback.yml`.
- `.github/pull_request_template.md`.
- `.github/workflows/evozeus-wrapper-preflight.yml`.
- `.evozeus-wrapper/scripts/evozeus_wrapper_preflight.py`.

## SKILL.md handling

Append-only. The existing Engineering Everything routing rules remain in place. Wrapper sections only describe source discovery, wrapper routing, version records, and migration rules.

## Validation

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/self_evolve.py doctor --json`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py version --repo HaodiFan/engineering-everything --current-tag v0.10.0`

## Rollback

Revert the wrapper-managed files and root `SKILL.md` append-only sections in git. If runtime installs were converted to symlinks, remove the symlinks and restore the archived directories from `~/.codex/skill-archive/`.
