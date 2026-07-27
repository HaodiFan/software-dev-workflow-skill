# Feedback Audit Rule

Use this rule at the end of any Skill turn when the user corrected the result, expressed dissatisfaction, identified a reusable Skill/wrapper defect, or asked to preserve a repeatable behavior.

Return a concise JSON decision with:

- `should_capture`: whether this feedback should become a tracked issue.
- `signal_id`: a non-sensitive short id for the current invocation.
- `capture_state`: `LOCAL_PENDING_CONFIRMATION` when feedback is detected.
- `capture_marker`: `🧙🏻‍♂️ [EvoZeus][进化信号已捕获｜本地待确认｜<signal_id>]`.
- `reason`: the specific reusable failure or improvement opportunity.
- `route`: `target_skill`, `wrapper`, or `both`.
- `severity`: `low`, `medium`, or `high`.
- `evidence_boundary`: what evidence can be recorded without exposing private session text, customer secrets, credentials, or unreleased commercial context.
- `writes`: always `false` during feedback audit.
- `next_action`: continue the original business flow and wait for explicit feedback-submission confirmation.

Capture when the issue is reusable beyond the current chat. Do not capture one-off user preferences unless they change the target Skill contract.

The capture state exists only in the current invocation and is not a persistent ledger entry. Do not create an Issue until the user explicitly confirms submission. Issue submission does not authorize a fix, branch, design doc, PR, release, or Harness change; each later write requires its own authorization.
