# Design Doc: Adopt EvoZeus-wrapper Harness

## Related issue

- Issue: direct owner request in Codex thread.
- What was unsatisfactory: engineering-everything had its own self-evolution scripts, but it was not wrapper-managed and did not expose the EvoZeus-wrapper dashboard, manifest, migration log, or wrapper source contract.
- Expected behavior: engineering-everything should keep its existing GitHub release history while adding the current EvoZeus-wrapper harness.

## Optimization goal

Make `engineering-everything` self-evolving through both layers:

- Skill-native gates: `scripts/skill_doctor.py` and `scripts/self_evolve.py`.
- Wrapper-managed gates: `.evozeus-wrapper/wrapper.json`, feedback Issue template, design docs, migration log, and `.evozeus-wrapper/scripts/evozeus_wrapper_preflight.py`.

## Direction

Use `adopt`, not `bootstrap`, because the canonical repo already exists at `HaodiFan/engineering-everything` and latest release `v0.9.10` exists on GitHub.

The change is append-only for Skill runtime behavior:

- Preserve existing routing and reference files.
- Append wrapper source-discovery and migration sections to root `SKILL.md`.
- Record wrapper harness version in `.evozeus-wrapper/wrapper.json`.
- Keep wrapper version separate from Skill release version.

## Implementation plan

- Skill sections to change: append `## 自进化方法` and `## EvoZeus-wrapper` to root `SKILL.md`.
- Files to update: wrapper-managed templates, `.evozeus-wrapper/CHANGELOG.md`, version metadata, and migration docs.
- Backward compatibility: existing route seeds, references, and subskill routing remain unchanged.

## Verification plan

- Source discovery check: `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything`.
- Manual checks: confirm `.evozeus-wrapper/wrapper.json` has `wrapper_version: v0.2.0` and `canonical_repo: HaodiFan/engineering-everything`.
- Regression cases: verify `scripts/skill_doctor.py`, `scripts/self_evolve.py check`, and `scripts/self_evolve.py doctor` still pass.
- Preflight command: `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`.

## Release plan

- Changelog entry: `v0.10.0`.
- Release tag: `v0.10.0`.
- Release description summary: adopt EvoZeus-wrapper `v0.2.0` and preserve existing Engineering Everything behavior.

## Risks and rollback

- Risk: runtime installs could drift if they remain copied directories.
- Rollback plan: keep the canonical repo intact, archive copied runtime installs before replacing them with symlinks, and restore from the archive if Codex cannot load the symlinked Skill.
