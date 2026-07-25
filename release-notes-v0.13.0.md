# Engineering Everything v0.13.0

## Plugin-first Skillware with CoEvolve governance

This release formalizes Engineering Everything as a plugin-first Skillware library and migrates its EvoZeus-CoEvolve lifecycle harness to the consolidated v2 layout.

## Skillware structure

- Runtime entrypoints live under `skills/*/SKILL.md`.
- `$using-engineering-everything` remains the recommended bootloader.
- `$engineering-everything` remains the direct kernel-router entry.
- All focused `engineering-*` Skills remain directly installable.

## CoEvolve harness

- Migrated the harness from `v0.3.0` scattered files to EvoZeus-CoEvolve `v0.11.2` under `.evozeus-wrapper/`.
- Added a governed Skill Feedback Issue → design doc → PR → changelog → release path.
- Aligned `scripts/install.py --target both` with its documented behavior so fresh Codex and Agents installs create canonical sub-Skill symlinks.
- Verified Codex and Agents runtime symlinks as direct sub-Skills within the canonical repository.
- Recorded the initial structure-gate failure and policy/pointer recovery in the migration ledger.

## Compatibility boundary

- Engineering routes, references, scenarios, and tool behavior remain unchanged by the harness migration.
- The project hook covers canonical repository maintenance.
- The recommended bootloader contains a prompt-enforced preflight.
- No native per-Skill invocation event is claimed.

## Verification

- Reference distribution check passed.
- Behavior scenario validation passed.
- Skill doctor and self-evolution check/doctor passed.
- Lesson validation passed.
- 9 unit tests passed.
- Python compilation passed.
- CoEvolve structure, source-contract doctor, and version checks passed.
- Codex and Agents installation checks passed for the canonical plugin Skill entries.

## License

The repository remains `UNLICENSED`.
