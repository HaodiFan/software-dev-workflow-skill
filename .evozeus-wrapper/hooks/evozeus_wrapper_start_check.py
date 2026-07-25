#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MANIFEST_PATH = ".evozeus-wrapper/wrapper.json"
LATEST_VERSION_ENV = "EVOZEUS_WRAPPER_LATEST_VERSION"
ENFORCEMENT_ENV = "EVOZEUS_WRAPPER_HOOK_ENFORCEMENT"
LATEST_RELEASE_URL = "https://api.github.com/repos/MetaInFLow/EvoZeus-CoEvolve/releases/latest"
GLOBAL_CACHE_PATH = ".evozeus/cache/evozeus-wrapper-latest.json"
GLOBAL_CACHE_TTL_SECONDS = 3600


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def write_latest_cache(home: Path, version: str, checked_at_epoch: int) -> None:
    path = home / GLOBAL_CACHE_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(
                {"version": version, "checked_at_epoch": checked_at_epoch},
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError:
        pass


def version_key(tag: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def fetch_latest_release() -> dict[str, str | None]:
    request = Request(
        LATEST_RELEASE_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "EvoZeus-CoEvolve-hook",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"version": None, "url": None, "error": str(exc)}
    version = payload.get("tag_name") if isinstance(payload, dict) else None
    url = payload.get("html_url") if isinstance(payload, dict) else None
    if not isinstance(version, str) or not version:
        return {"version": None, "url": None, "error": "GitHub latest release has no tag_name"}
    return {"version": version, "url": url if isinstance(url, str) else None, "error": None}


def resolve_latest_version(
    current: str,
    environment: dict[str, str] | None = None,
    fetcher=None,
    home: Path | None = None,
    now_epoch: int | None = None,
) -> dict[str, str | None]:
    environment = os.environ if environment is None else environment
    checked_at = datetime.now(timezone.utc).isoformat()
    explicit = environment.get(LATEST_VERSION_ENV)
    if explicit:
        return {
            "version": explicit,
            "source": "environment",
            "checked_at": checked_at,
            "url": None,
            "error": None,
        }
    home = Path.home() if home is None else home.expanduser().resolve()
    now_epoch = int(time.time()) if now_epoch is None else now_epoch
    cache = read_json(home / GLOBAL_CACHE_PATH) or {}
    cached_version = cache.get("version")
    cached_at = cache.get("checked_at_epoch")
    if (
        isinstance(cached_version, str)
        and version_key(cached_version)
        and isinstance(cached_at, int)
        and max(0, now_epoch - cached_at) <= GLOBAL_CACHE_TTL_SECONDS
    ):
        return {
            "version": cached_version,
            "source": "global_dispatcher_cache",
            "checked_at": checked_at,
            "url": None,
            "error": None,
        }
    release = (fetcher or fetch_latest_release)()
    if release.get("version"):
        write_latest_cache(home, release["version"], now_epoch)
        return {
            "version": release["version"],
            "source": "github_latest_release",
            "checked_at": checked_at,
            "url": release.get("url"),
            "error": None,
        }
    return {
        "version": None,
        "source": "unavailable",
        "checked_at": checked_at,
        "url": None,
        "error": release.get("error") or "GitHub latest release is unavailable",
    }


def emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def block(reason: str, next_action: str) -> int:
    return emit(
        {
            "continue": False,
            "stopReason": reason,
            "systemMessage": reason,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    "EvoZeus-CoEvolve capability=repo_maintenance_hook; "
                    f"scope=canonical_repository; blocked start; next_action={next_action}"
                ),
            },
        }
    )


def allow(level: str, message: str, next_action: str) -> int:
    return emit(
        {
            "continue": True,
            "systemMessage": message,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    "EvoZeus-CoEvolve capability=repo_maintenance_hook; "
                    f"scope=canonical_repository; hook_start_check level={level}; "
                    f"next_action={next_action}; {message}"
                ),
            },
        }
    )


def main() -> int:
    try:
        json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        pass

    root = repo_root()
    manifest = read_json(root / MANIFEST_PATH)
    if not manifest:
        return block(
            "EvoZeus wrapper harness manifest is missing or unreadable.",
            "repair_or_adopt_before_wrapper_managed_execution",
        )

    current = str(manifest.get("wrapper_version") or "")
    enforcement = os.environ.get(ENFORCEMENT_ENV, "advisory").strip().lower()
    if enforcement not in {"advisory", "strict"}:
        enforcement = "advisory"

    latest_resolution = resolve_latest_version(current)
    latest = latest_resolution["version"]
    current_key = version_key(current)
    if not current_key:
        return block("EvoZeus wrapper harness version is missing or invalid.", "repair_wrapper_manifest")
    if not latest:
        detail = (
            "EvoZeus wrapper latest version is unavailable; "
            f"source={latest_resolution['source']}; checked_at={latest_resolution['checked_at']}; "
            f"error={latest_resolution['error']}"
        )
        if enforcement == "strict":
            return block(detail, "retry_latest_release_lookup")
        return allow("warn", detail, "retry_latest_release_lookup")
    latest_key = version_key(latest)
    if not latest_key:
        return block(
            f"EvoZeus wrapper latest version is invalid: {latest}",
            f"check_{LATEST_VERSION_ENV}_or_latest_release",
        )

    if latest_key == current_key:
        return allow("allow", "EvoZeus wrapper harness is current.", "none")
    if latest_key < current_key:
        return allow("allow", "EvoZeus wrapper harness is ahead of the configured latest version.", "do_not_downgrade")
    if latest_key[0] > current_key[0]:
        return block(
            "EvoZeus wrapper harness has a major upgrade available.",
            "confirm_and_plan_harness_upgrade",
        )
    if enforcement == "strict":
        return block(
            "EvoZeus wrapper harness has a non-breaking upgrade available under strict enforcement.",
            "create_harness_upgrade_pr",
        )
    return allow(
        "warn",
        "EvoZeus wrapper harness has a non-breaking upgrade available; continue in advisory mode.",
        "create_harness_upgrade_pr",
    )


if __name__ == "__main__":
    raise SystemExit(main())
