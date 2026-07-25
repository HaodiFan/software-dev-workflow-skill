# Engineering Everything as a CoEvolve Skillware Feasibility Target

## Related issue

- https://github.com/HaodiFan/engineering-everything/issues/17

## Optimization goal

Attach the current EvoZeus-CoEvolve harness to the existing plugin-first Skillware without changing its engineering routes, reference contracts, scenario behavior, or direct sub-Skill invocation model.

## Direction

Use `skills/using-engineering-everything/SKILL.md` as the recommended prompt-enforced preflight surface. Consolidate wrapper-owned lifecycle assets under `.evozeus-wrapper/`, preserve target-owned plugin entrypoints, and make runtime installations point to direct canonical sub-Skills.

## Implementation plan

1. Record the bootloader as the instruction surface in the legacy manifest.
2. Migrate scattered wrapper-owned files from v0.3.0 to the consolidated v2 layout.
3. Preserve the strict structure gate; restore missing feedback/audit policies from public CoEvolve templates.
4. Use CoEvolve v0.11.2 to accept manifest-managed direct `skills/<name>` pointers.
5. Align `scripts/install.py --target both` with the documented canonical-symlink contract.
6. Keep all target routing rules and references unchanged; update only release metadata and the bootloader-owned governance sections.

## Verification plan

- Run all native Engineering Everything gates from `docs/testing.md`.
- Run CoEvolve structure, doctor, upgrade, version, and release checks.
- Compare the changed files against baseline commit `abcd3bb26bb2c05236ac041d6cebf3af86a81357`.
- Verify an existing installation is idempotent.
- Install into a fresh synthetic HOME and require 24 symlinks across Codex and Agents with zero copied Skill directories.
- Verify release `v0.13.0`, then check out `v0.12.0` in a separate recovery workspace and rerun its documented native gates.

## Release plan

- Merge through a reviewed pull request linked to Issue #17.
- Publish `v0.13.0` using `release-notes-v0.13.0.md`.
- Keep EvoZeus-CoEvolve and Skillware release versions as independent axes.
- Record the final commits, release URLs, checks, and recovery result in the public CoEvolve paper artifact.

## Rollback plan

- Before merge: revert the migration commit on the feature branch.
- After release: reinstall `v0.12.0` from a separate clean checkout and verify its documented package gates.
- Keep the canonical GitHub repository and current working checkout intact during the recovery rehearsal.

## Evidence boundary

The public artifact may contain repository paths, commits, release URLs, aggregate test results, file-level diffs, and synthetic HOME installation evidence. It excludes private sessions, secrets, customer data, and unrelated local files.
