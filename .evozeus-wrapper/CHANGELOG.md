# Changelog

All notable changes to engineering-everything are recorded here.

Wrapper harness migrations are recorded under `.evozeus-wrapper/docs/migrations/`. Add them here only when the migration also changes this Skill's release contract.

## [Unreleased]

### Skill changes

- Upgraded the managed EvoZeus-CoEvolve Harness from `v0.11.4` to `v0.12.1`.
- Added the per-invocation EvoZeus runtime identity header and staged feedback authorization contract to the wrapper-owned bootloader prelude.

### Feedback / Issues

- Owner-authorized batch Harness upgrade following the EvoZeus-CoEvolve `v0.12.1` release.

### Verification

- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py identity --json`
- `git diff --check`

## [v0.13.0] - 2026-07-25

### Skill changes

- Demoted root `SKILL.md`: runtime entrypoints now live only under `skills/*/SKILL.md`.
- Updated package, self-evolution, and wrapper preflight gates to use `.codex-plugin/plugin.json` plus the plugin skill library as the package contract.
- Updated wrapper/dashboard docs to describe plugin-first source governance.
- Migrated the EvoZeus-CoEvolve harness from scattered layout `v0.3.0` to consolidated layout `v0.11.2`.
- Kept `skills/using-engineering-everything/SKILL.md` as the recommended bootloader and preserved all direct sub-Skill entrypoints.
- Aligned `scripts/install.py --target both` with its documented contract by creating canonical sub-Skill symlinks for Codex and Agents on fresh installs.

### Feedback / Issues

- Owner request: use Engineering Everything as the first non-project Skillware feasibility target for EvoZeus-CoEvolve.
- Related issue: https://github.com/HaodiFan/engineering-everything/issues/17
- Migration recovery: the first structure gate exposed missing legacy policy files and root-only runtime pointer assumptions; CoEvolve v0.11.2 fixed both without weakening validation.

### Verification

- `python3 scripts/sync_references.py --check --json`
- `python3 scripts/eval_scenarios.py validate --json`
- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/self_evolve.py doctor --json`
- `python3 scripts/lesson.py validate`
- `python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/*.py`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py version --repo HaodiFan/engineering-everything --current-tag v0.13.0`

### Release notes

- Major pre-1.0 package transition: plugin-first runtime entrypoints replace the retired root Skill entry.
- CoEvolve adds lifecycle governance and a recommended-entry preflight; it does not change Engineering Everything routing decisions.
- Fresh plugin-library installs now maintain one canonical source through symlinks instead of copied runtime directories.
- Native per-Skill invocation hooks remain unavailable; the bootloader preflight depends on instruction compliance.
- License remains `UNLICENSED`.

## [v0.12.0] - 2026-06-28

### Skill changes

- Added `using-engineering-everything` as a bootloader skill for new sessions, resume handling, and task-switch rerouting.
- Added canonical output contracts, route contract notes, and Codex tool boundary references.
- Added `data/reference_distribution.yaml` plus `scripts/sync_references.py` to prevent reference drift and orphan runtime copies.
- Added behavior-eval scenario schemas under `evals/scenarios/` plus `scripts/eval_scenarios.py`.
- Extended `data/routes.yaml` with route contract fields: priority, conflicts, fallback, handoff, direct-call permission, and eval coverage.
- Hardened `scripts/install.py` with list/relink/uninstall lifecycle actions and symlink-safe removal.
- Extended `scripts/skill_doctor.py` to validate bootloader structure, route contracts, reference distribution, and eval scenario schemas.

### Feedback / Issues

- User request: learn from `obra/superpowers` plugin/skill structure and refactor Engineering Everything into a clearer AgentOS bootloader + router + subskill system.

### Verification

- `python3 scripts/sync_references.py --check --json`
- `python3 scripts/eval_scenarios.py validate --json`
- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/lesson.py validate`
- `python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/*.py`

### Release notes

- Non-breaking minor release: `$engineering-everything` remains valid, while `$using-engineering-everything` becomes the recommended bootloader entry.
- SessionStart hook remains deferred.
- License remains `UNLICENSED`; public distribution positioning still requires owner decision.

## [v0.11.0] - 2026-06-27

### Skill changes

- Upgraded EvoZeus-wrapper harness from `v0.2.0` to `v0.3.0`.
- Added `EvoZeus-wrapper 状态检查` as the first visible section after root `SKILL.md` frontmatter.
- Kept the Engineering Everything routing and subskill behavior unchanged.

### Feedback / Issues

- User request: target Skills wrapped by EvoZeus-wrapper must check current Skill release, wrapper harness version, source contract, and remediation path before entering the main Skill flow.

### Verification

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/self_evolve.py doctor --json`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py version --repo HaodiFan/engineering-everything --current-tag v0.11.0`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py release --tag v0.11.0 --release-notes /tmp/engineering-everything-v0.11.0-release-notes.md --skip-gh`

## [v0.10.0] - 2026-06-27

### Skill changes

- Adopted EvoZeus-wrapper `v0.2.0` as the GitHub-backed self-evolution harness.
- Added wrapper-managed feedback Issue, PR template, design docs, migration log, dashboard docs, and preflight checker.
- Preserved the existing Engineering Everything routing behavior while adding append-only wrapper migration rules.

### Feedback / Issues

- User request: use the current EvoZeus-wrapper to make engineering-everything self-evolving.

### Verification

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/self_evolve.py doctor --json`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py version --repo HaodiFan/engineering-everything --current-tag v0.10.0`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py release --tag v0.10.0 --release-notes release-notes.md --skip-gh`

## [v0.9.10] - 2026-06-27

### Skill changes

- Split Engineering Everything into the current router-plus-subskills library shape.

### Verification

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/self_evolve.py doctor --json`

## Release Notes Policy

Every release must include:

- The Skill behavior or harness contract that changed.
- The related feedback Issue or design doc.
- The verification performed.
- Known limitations or rollback notes.

Release tags must use `vMAJOR.MINOR.PATCH`:

- `MAJOR`: incompatible Skill behavior or output contract change.
- `MINOR`: new capability, new required evidence rule, or new harness behavior.
- `PATCH`: wording, examples, bug fixes, validation fixes, or non-breaking clarifications.
