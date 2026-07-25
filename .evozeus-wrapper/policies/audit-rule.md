# Feedback Audit Rule

Use this rule at the end of any Skill turn when the user corrected the result, expressed dissatisfaction, identified a reusable Skill/wrapper defect, or asked to preserve a repeatable behavior.

Return a concise JSON decision with:

- `should_capture`: whether this feedback should become a tracked issue.
- `reason`: the specific reusable failure or improvement opportunity.
- `route`: `target_skill`, `wrapper`, or `both`.
- `severity`: `low`, `medium`, or `high`.
- `evidence_boundary`: what evidence can be recorded without exposing private session text, customer secrets, credentials, or unreleased commercial context.

Capture when the issue is reusable beyond the current chat. Do not capture one-off user preferences unless they change the target Skill contract.
