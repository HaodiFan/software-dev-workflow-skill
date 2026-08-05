#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_NOTICE_POLICY: dict[str, Any] = {
    "schema_version": "v1",
    "tag_style": "markdown_code",
    "show_signal_id": False,
    "events": {
        "skill": {
            "tag": "EvoZeus · 受管 Skill",
            "show_state_label": False,
            "details_separator": " ",
            "states": {"active": {"icon": "🧙🏻‍♂️", "label": "运行中"}},
        },
        "lesson": {
            "tag": "EvoZeus · Lesson",
            "states": {
                "pending": {"icon": "💡", "label": "待记录"},
                "recorded": {"icon": "📝", "label": "已记录"},
            },
        },
        "evolution": {
            "tag": "EvoZeus · Evolution",
            "states": {
                "authorized": {"icon": "🛠️", "label": "已授权"},
                "running": {"icon": "🛠️", "label": "进行中"},
                "verified": {"icon": "🛠️", "label": "已验证"},
            },
        },
        "maintenance": {
            "tag": "EvoZeus · Maintenance",
            "states": {
                "pending": {"icon": "🔧", "label": "待授权"},
                "running": {"icon": "🔧", "label": "进行中"},
                "completed": {"icon": "🔧", "label": "已完成"},
            },
        },
        "advisory": {
            "tag": "EvoZeus · Advisory",
            "states": {"continue": {"icon": "⚠️", "label": "可继续"}},
        },
        "blocked": {
            "tag": "EvoZeus · Blocked",
            "states": {"blocked": {"icon": "🛑", "label": "已阻塞"}},
        },
        "uat": {
            "tag": "EvoZeus · UAT",
            "states": {
                "replaced": {"icon": "🧪", "label": "已覆盖"},
                "passed": {"icon": "🧪", "label": "已通过"},
                "failed": {"icon": "🧪", "label": "未通过"},
            },
        },
        "release": {
            "tag": "EvoZeus · Release",
            "states": {"published": {"icon": "🚀", "label": "已发布"}},
        },
    },
}


def _validate_policy(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("schema_version") != "v1":
        raise ValueError("notice policy schema_version must be v1")
    if policy.get("tag_style") != "markdown_code":
        raise ValueError("notice policy tag_style must be markdown_code")
    if not isinstance(policy.get("show_signal_id"), bool):
        raise ValueError("notice policy show_signal_id must be boolean")
    events = policy.get("events")
    if not isinstance(events, dict) or not events:
        raise ValueError("notice policy events must be a non-empty object")
    for kind, event in events.items():
        if not isinstance(event, dict) or not isinstance(event.get("tag"), str):
            raise ValueError(f"notice event {kind} must define tag")
        if "show_state_label" in event and not isinstance(event["show_state_label"], bool):
            raise ValueError(f"notice event {kind} show_state_label must be boolean")
        if "details_separator" in event and not isinstance(event["details_separator"], str):
            raise ValueError(f"notice event {kind} details_separator must be a string")
        states = event.get("states")
        if not isinstance(states, dict) or not states:
            raise ValueError(f"notice event {kind} must define states")
        for state, visual in states.items():
            if not isinstance(visual, dict):
                raise ValueError(f"notice event {kind}/{state} must be an object")
            if not isinstance(visual.get("icon"), str) or not visual["icon"].strip():
                raise ValueError(f"notice event {kind}/{state} must define icon")
            if not isinstance(visual.get("label"), str) or not visual["label"].strip():
                raise ValueError(f"notice event {kind}/{state} must define label")
    return policy


def default_policy_path() -> Path | None:
    candidate = Path(__file__).resolve().parents[1] / "policies" / "notice-policy.json"
    return candidate if candidate.is_file() else None


def load_notice_policy(path: Path | str | None = None) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve() if path is not None else default_policy_path()
    if resolved is None:
        return copy.deepcopy(DEFAULT_NOTICE_POLICY)
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("notice policy root must be an object")
    return _validate_policy(data)


def render_notice(
    *,
    kind: str,
    state: str,
    message: str | None = None,
    details: str | None = None,
    action: str | None = None,
    signal_id: str | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    effective_policy = _validate_policy(copy.deepcopy(policy or DEFAULT_NOTICE_POLICY))
    events = effective_policy["events"]
    if kind not in events:
        raise ValueError(f"unsupported notice kind: {kind}")
    event = events[kind]
    states = event["states"]
    if state not in states:
        raise ValueError(f"unsupported state for {kind}: {state}")
    normalized_message = message.strip() if message and message.strip() else None
    normalized_details = details.strip() if details and details.strip() else None
    if not normalized_message and not normalized_details:
        raise ValueError("notice message or details must not be empty")
    normalized_action = action.strip() if action and action.strip() else None
    visual = states[state]
    icon = visual["icon"].strip()
    tag = event["tag"].strip()
    state_label = visual["label"].strip()
    first_line = f"{icon} `{tag}`"
    if event.get("show_state_label", True):
        first_line += f" {state_label}"
    if signal_id and effective_policy["show_signal_id"]:
        first_line += f" · `{signal_id}`"
    if normalized_details:
        first_line += f"{event.get('details_separator', ' · ')}{normalized_details}"
    blocks = [first_line]
    if normalized_message:
        blocks.append(normalized_message)
    if normalized_action:
        blocks.append(normalized_action)
    result = {
        "schema_version": "v1",
        "kind": kind,
        "state": state,
        "icon": icon,
        "tag": tag,
        "state_label": state_label,
        "message": normalized_message,
        "action": normalized_action,
        "signal_id": signal_id,
        "display_text": "\n\n".join(blocks),
        "writes": False,
    }
    if normalized_details:
        result["details"] = normalized_details
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render an EvoZeus target-Skill notice.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser("render", help="Render one configured notice.")
    render.add_argument("--kind", required=True)
    render.add_argument("--state", required=True)
    render.add_argument("--message")
    render.add_argument("--details")
    render.add_argument("--action")
    render.add_argument("--signal-id")
    render.add_argument("--policy", type=Path)
    render.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        policy = load_notice_policy(args.policy)
        notice = render_notice(
            kind=args.kind,
            state=args.state,
            message=args.message,
            details=args.details,
            action=args.action,
            signal_id=args.signal_id,
            policy=policy,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(notice, ensure_ascii=False, indent=2))
    else:
        print(notice["display_text"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
