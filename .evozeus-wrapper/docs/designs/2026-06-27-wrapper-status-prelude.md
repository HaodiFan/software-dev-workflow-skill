# Design Doc: Wrapper Status Prelude

## Related issue

- Issue: direct owner request in Codex thread.
- What was unsatisfactory: wrapped Skills could enter their main flow before checking whether the Skill release, wrapper harness, and canonical source contract were current.
- Expected behavior: the wrapper-owned status check appears before the target Skill main chain and gives concrete remediation steps.

## Optimization goal

Make `engineering-everything` runtime entry safer without changing its engineering routing behavior:

- Show current Skill release before any main-chain instruction.
- Show current EvoZeus-wrapper harness version before any main-chain instruction.
- Show source contract checks and repair order before runtime use.

## Direction

Adopt EvoZeus-wrapper `v0.3.0` and add the status prelude immediately after root `SKILL.md` frontmatter.

This is a harness migration, not a routing behavior change:

- Preserve Engineering Everything's existing route priority and subskill map.
- Keep Skill release version separate from wrapper harness version.
- Record the wrapper migration under `.evozeus-wrapper/docs/migrations/`.

## Implementation plan

- Add `EvoZeus-wrapper 状态检查` at the top of root `SKILL.md` after frontmatter.
- Update wrapper-managed dashboard files to record Skill `v0.11.0` and wrapper `v0.3.0`.
- Copy the `v0.3.0` wrapper preflight checker.
- Update `.evozeus-wrapper/wrapper.json` to `wrapper_version: v0.3.0`.
- Add changelog and migration records.

## Verification plan

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/self_evolve.py doctor --json`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py version --repo HaodiFan/engineering-everything --current-tag v0.11.0`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py release --tag v0.11.0 --release-notes /tmp/engineering-everything-v0.11.0-release-notes.md --skip-gh`

## Release plan

- Changelog entry: `v0.11.0`.
- Release tag: `v0.11.0`.
- Release description summary: upgrade EvoZeus-wrapper to `v0.3.0` and add the status prelude before the main Skill chain.

## Risks and rollback

- Risk: agents may treat the status prelude as a replacement for Engineering Everything's existing route logic.
- Mitigation: the status prelude explicitly says the main flow starts only after checks pass; it does not redefine routing.
- Rollback plan: revert the migration commit and restore `.evozeus-wrapper/wrapper.json` to `v0.2.0`.
