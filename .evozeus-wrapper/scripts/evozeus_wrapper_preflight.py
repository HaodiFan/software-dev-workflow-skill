#!/usr/bin/env python3
from __future__ import annotations

# ruff: noqa: E402

import sys


def _bootstrap_preflight_sources() -> tuple[dict, dict]:
    posix = __import__("posix")
    cwd = posix.getcwd()
    original_sys_path = tuple(sys.path)

    def lexical_absolute(raw: str) -> str:
        value = raw if raw.startswith("/") else cwd + "/" + raw
        parts: list[str] = []
        for part in value.split("/"):
            if part in {"", "."}:
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        return "/" + "/".join(parts)

    script = lexical_absolute(__file__)
    scripts_dir = script.rsplit("/", 1)[0]
    sidecar_root = scripts_dir.rsplit("/", 1)[0]
    system_roots = {
        lexical_absolute(sys.base_prefix),
        lexical_absolute(sys.prefix),
    }
    sys.path[:] = [
        item
        for item in original_sys_path
        if any(
            lexical_absolute(item or cwd) == root
            or lexical_absolute(item or cwd).startswith(root + "/")
            for root in system_roots
        )
    ]

    os_module = __import__("os")
    temp_root = os_module.path.realpath(
        os_module.environ.get("TMPDIR") or "/tmp"
    )
    if any(
        temp_root == root or temp_root.startswith(root + os_module.sep)
        for root in (os_module.path.realpath(sidecar_root),)
    ):
        raise RuntimeError("bytecode cache root must be outside the Harness")
    cache = ""
    for _attempt in range(32):
        candidate = os_module.path.join(
            temp_root,
            f"evozeus-pycache-{os_module.getpid()}-{os_module.urandom(16).hex()}",
        )
        try:
            os_module.mkdir(candidate, 0o700)
        except FileExistsError:
            continue
        cache = candidate
        break
    if not cache:
        raise RuntimeError("cannot allocate an external bytecode cache directory")
    sys.pycache_prefix = cache
    sys.dont_write_bytecode = True
    atexit_module = __import__("atexit")

    def remove_empty_cache() -> None:
        try:
            os_module.rmdir(cache)
        except OSError:
            pass

    atexit_module.register(remove_empty_cache)

    trusted_notice_source = globals().pop(
        "_EVOZEUS_TRUSTED_NOTICE_SOURCE",
        None,
    )
    trusted_notice_sha256 = globals().pop(
        "_EVOZEUS_TRUSTED_NOTICE_SHA256",
        None,
    )
    if (trusted_notice_source is None) != (trusted_notice_sha256 is None):
        raise RuntimeError("trusted notice source identity is incomplete")
    notice_path = scripts_dir + "/evozeus_notice.py"
    if trusted_notice_source is not None:
        if (
            not isinstance(trusted_notice_source, bytes)
            or not isinstance(trusted_notice_sha256, str)
            or len(trusted_notice_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in trusted_notice_sha256
            )
        ):
            raise RuntimeError("trusted notice source identity is invalid")
        hashlib_module = __import__("hashlib")
        if (
            hashlib_module.sha256(trusted_notice_source).hexdigest()
            != trusted_notice_sha256
        ):
            raise RuntimeError("trusted notice source digest changed")
        source = trusted_notice_source
        notice_path = "<evozeus-trusted-notice>"
    else:
        flags = posix.O_RDONLY | getattr(posix, "O_CLOEXEC", 0)
        nofollow = getattr(posix, "O_NOFOLLOW", 0)
        if nofollow == 0:
            raise RuntimeError("trusted notice loading requires O_NOFOLLOW")
        descriptor = posix.open(notice_path, flags | nofollow)
        try:
            metadata = posix.fstat(descriptor)
            if metadata.st_mode & 0o170000 != 0o100000:
                raise RuntimeError("trusted notice source is not a regular file")
            source = b""
            while len(source) < metadata.st_size:
                chunk = posix.read(descriptor, metadata.st_size - len(source))
                if not chunk:
                    raise RuntimeError("trusted notice source changed while reading")
                source += chunk
            if posix.read(descriptor, 1):
                raise RuntimeError("trusted notice source grew while reading")
            final_metadata = posix.fstat(descriptor)
            if (
                metadata.st_dev,
                metadata.st_ino,
                metadata.st_mode,
                metadata.st_size,
                metadata.st_mtime_ns,
                metadata.st_ctime_ns,
            ) != (
                final_metadata.st_dev,
                final_metadata.st_ino,
                final_metadata.st_mode,
                final_metadata.st_size,
                final_metadata.st_mtime_ns,
                final_metadata.st_ctime_ns,
            ):
                raise RuntimeError("trusted notice source changed while reading")
        finally:
            posix.close(descriptor)
    namespace = {"__file__": notice_path, "__name__": "_evozeus_notice"}
    exec(compile(source, notice_path, "exec", dont_inherit=True), namespace)
    return namespace, {"pycache_prefix": cache, "scripts_dir": scripts_dir}


_NOTICE_SOURCE, _TRUSTED_SOURCE_RUNTIME = _bootstrap_preflight_sources()

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

load_notice_policy = _NOTICE_SOURCE["load_notice_policy"]
render_notice = _NOTICE_SOURCE["render_notice"]


GLOBAL_EVOZEUS_HOME = ".evozeus"
GLOBAL_EVOZEUS_PROJECTS_DIR = ".projects"
TARGET_EVOINFRA_DIR = ".evozeus-wrapper"
LEGACY_TARGET_EVOINFRA_DIR = ".evozeus_evoinfra"
OLDEST_TARGET_EVOINFRA_DIR = ".evozeus"
TARGET_WRAPPER_MANIFEST = f"{TARGET_EVOINFRA_DIR}/wrapper.json"
LEGACY_TARGET_WRAPPER_MANIFEST = f"{LEGACY_TARGET_EVOINFRA_DIR}/wrapper.json"
OLDEST_TARGET_WRAPPER_MANIFEST = f"{OLDEST_TARGET_EVOINFRA_DIR}/wrapper.json"
TARGET_CHANGELOG = f"{TARGET_EVOINFRA_DIR}/CHANGELOG.md"
TARGET_WRAPPER_GUIDE = f"{TARGET_EVOINFRA_DIR}/WRAPPER.md"
TARGET_FEEDBACK_POLICY = f"{TARGET_EVOINFRA_DIR}/policies/feedback-policy.json"
TARGET_AUDIT_RULE = f"{TARGET_EVOINFRA_DIR}/policies/audit-rule.md"
TARGET_NOTICE_POLICY = f"{TARGET_EVOINFRA_DIR}/policies/notice-policy.json"
CODEX_HOOKS_CONFIG = ".codex/hooks.json"
CODEX_START_HOOK_SCRIPT = f"{TARGET_EVOINFRA_DIR}/hooks/evozeus_wrapper_start_check.py"
TARGET_DASHBOARD_INDEX = f"{TARGET_EVOINFRA_DIR}/docs/index.md"
TARGET_DASHBOARD_CONFIG = f"{TARGET_EVOINFRA_DIR}/docs/_config.yml"
TARGET_DESIGN_TEMPLATE = f"{TARGET_EVOINFRA_DIR}/docs/design-doc-template.md"
TARGET_DESIGNS_DIR = f"{TARGET_EVOINFRA_DIR}/docs/designs"
TARGET_DESIGNS_README = f"{TARGET_DESIGNS_DIR}/README.md"
TARGET_MIGRATIONS_DIR = f"{TARGET_EVOINFRA_DIR}/docs/migrations"
TARGET_MIGRATIONS_README = f"{TARGET_MIGRATIONS_DIR}/README.md"
TARGET_ONBOARDING_GUIDE = f"{TARGET_EVOINFRA_DIR}/docs/onboarding.md"
TARGET_PREFLIGHT_SCRIPT = f"{TARGET_EVOINFRA_DIR}/scripts/evozeus_wrapper_preflight.py"
TARGET_NOTICE_SCRIPT = f"{TARGET_EVOINFRA_DIR}/scripts/evozeus_notice.py"
TARGET_HARNESS_SKILL = f"{TARGET_EVOINFRA_DIR}/skills/using-evozeus-harness/SKILL.md"
TARGET_MIGRATION_CONTRACT = f"{TARGET_EVOINFRA_DIR}/contracts/harness-migration-contract-v1.json"
HARNESS_SKILL_VERSION = "v1.1.0"
MIGRATION_PROTOCOL_VERSION = "v1.0.0"
HARNESS_ENTRY_BEGIN = "<!-- evozeus-harness-entry:v1 -->"
HARNESS_ENTRY_END = "<!-- /evozeus-harness-entry -->"

REQUIRED_FILES = [
    TARGET_CHANGELOG,
    TARGET_WRAPPER_GUIDE,
    TARGET_WRAPPER_MANIFEST,
    TARGET_FEEDBACK_POLICY,
    TARGET_AUDIT_RULE,
    TARGET_NOTICE_POLICY,
    CODEX_HOOKS_CONFIG,
    CODEX_START_HOOK_SCRIPT,
    TARGET_DASHBOARD_INDEX,
    TARGET_DASHBOARD_CONFIG,
    TARGET_DESIGN_TEMPLATE,
    TARGET_DESIGNS_README,
    TARGET_MIGRATIONS_README,
    TARGET_ONBOARDING_GUIDE,
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/skill-feedback.yml",
    ".github/pull_request_template.md",
    ".github/workflows/evozeus-wrapper-preflight.yml",
    TARGET_PREFLIGHT_SCRIPT,
    TARGET_NOTICE_SCRIPT,
    TARGET_HARNESS_SKILL,
    TARGET_MIGRATION_CONTRACT,
]
MAINTAINER_REQUIRED_FILES = REQUIRED_FILES

ISSUE_TERMS = [
    ["不满意", "unsatisfactory", "bad result"],
    ["期望", "expected"],
    ["复现", "reproduction", "scenario", "场景"],
    ["证据边界", "evidence boundary"],
    ["影响", "impact"],
]

DESIGN_TERMS = [
    ["related issue", "修复", "issue"],
    ["optimization goal", "优化目标"],
    ["direction", "优化方向"],
    ["implementation plan", "怎么优化", "实现"],
    ["verification plan", "验证"],
    ["release plan", "release", "发布"],
]

HARNESS_SKILL_TERMS = [
    TARGET_WRAPPER_MANIFEST,
    TARGET_NOTICE_POLICY,
    "prompt_runtime_check",
    "bootstrap_skill",
    "integration.capabilities",
    "SkillInvoke",
    "runtime-only install",
    "doctor --target .",
    "identity --json",
    "Feedback Issue",
    "Issue-to-PR",
    "Harness 维护",
    "UAT",
    "Release",
    "rollback",
    "普通 Skill 调用不授权",
]

PLACEHOLDER_PATTERNS = [
    r"\{\{[A-Z_]+\}\}",
    r"<short title>",
    r"<path>",
    r"<design-doc>",
    r"\bTBD\b",
    r"待填写",
]

NOTICE_REQUIRED_STATES = {
    "skill": {"active"},
    "lesson": {"pending", "recorded"},
    "evolution": {"authorized", "running", "verified"},
    "maintenance": {"pending", "running", "completed"},
    "advisory": {"continue"},
    "blocked": {"blocked"},
    "uat": {"replaced", "passed", "failed"},
    "release": {"published"},
}

VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
RUNTIME_REFERENCE_RE = re.compile(
    r"(?P<path>(?:references|scripts|assets|templates|agents)/[A-Za-z0-9_.@()/+=,~-]+)",
)
PLUGIN_MANIFEST_CANDIDATES = [
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".kimi-plugin/plugin.json",
    ".opencode/INSTALL.md",
    "gemini-extension.json",
    "package.json",
]
WRAPPER_RUNTIME_SECTION_HEADINGS = {
    "## EvoZeus-CoEvolve 状态检查",
    "## EvoZeus-wrapper 状态检查",
    "## 自进化方法",
    "## EvoZeus-CoEvolve",
    "## EvoZeus-wrapper",
}
STATUS_PRELUDE_HEADINGS = (
    "## EvoZeus-CoEvolve 状态检查",
    "## EvoZeus-wrapper 状态检查",
)
BLOCKING_STATUS_PHRASES = [
    "Continue to the target Skill's main flow only after all three are OK.",
    "全部 OK 后",
    "只有检查结果为 OK",
    "才继续进入目标 Skill 原本主链路",
    "才继续进入下方原 Skill 流程",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"OK: {message}")


def warn(message: str) -> None:
    print(f"WARN: {message}")


def read_text(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def has_any(text: str, terms: list[str]) -> bool:
    low = normalize(text)
    return any(term.lower() in low for term in terms)


def has_real_content(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 40:
        return False
    return not any(re.search(pattern, stripped, re.IGNORECASE) for pattern in PLACEHOLDER_PATTERNS)


def version_key(tag: str) -> tuple[int, int, int]:
    match = VERSION_RE.fullmatch(tag)
    if not match:
        fail(f"release tag must use vMAJOR.MINOR.PATCH format: {tag}")
    return tuple(int(part) for part in match.groups())


def run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        fail(f"missing required dependency: {command}")


def path_kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    if path.is_file():
        return "file"
    return "missing"


def resolve_path(path: Path) -> str | None:
    if not (path.exists() or path.is_symlink()):
        return None
    try:
        return str(path.resolve())
    except OSError:
        return None


def runtime_pointer_scope(canonical_path: Path, resolved_path: str | None) -> str | None:
    if not resolved_path:
        return None
    canonical = canonical_path.expanduser().resolve()
    resolved = Path(resolved_path).expanduser().resolve()
    if resolved == canonical:
        return "canonical_repo"
    if resolved.parent == canonical / "skills" and (resolved / "SKILL.md").is_file():
        return "canonical_subskill"
    return None


def wrapper_manifest_path(target: Path) -> Path:
    return target / TARGET_EVOINFRA_DIR / "wrapper.json"


def legacy_wrapper_manifest_path(target: Path) -> Path:
    return target / LEGACY_TARGET_EVOINFRA_DIR / "wrapper.json"


def oldest_wrapper_manifest_path(target: Path) -> Path:
    return target / OLDEST_TARGET_EVOINFRA_DIR / "wrapper.json"


def read_json_object(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid wrapper manifest JSON: {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"wrapper manifest must be a JSON object: {path}")
    return data


def load_wrapper_manifest(target: Path) -> dict | None:
    current_path = wrapper_manifest_path(target)
    legacy_paths = [legacy_wrapper_manifest_path(target), oldest_wrapper_manifest_path(target)]
    existing_legacy = [path for path in legacy_paths if path.exists()]
    if existing_legacy:
        fail(
            "legacy wrapper layout requires an upgrade migration before preflight: "
            + ", ".join(str(path.relative_to(target)) for path in existing_legacy)
        )
    if not current_path.exists():
        return None
    return read_json_object(current_path)


def project_pointer_path(repo: str) -> Path:
    owner, name = repo.split("/", 1)
    return Path.home() / GLOBAL_EVOZEUS_HOME / GLOBAL_EVOZEUS_PROJECTS_DIR / owner / name


def detected_hook_files(target: Path) -> list[str]:
    hooks = [
        path
        for path in [
            CODEX_HOOKS_CONFIG,
            ".codex/config.toml",
            CODEX_START_HOOK_SCRIPT,
        ]
        if (target / path).is_file()
    ]
    hooks_dir = target / "hooks"
    if hooks_dir.is_dir():
        hooks.extend(
            str(path.relative_to(target))
            for path in sorted(hooks_dir.iterdir())
            if path.is_file()
        )
    return list(dict.fromkeys(hooks))


def detected_plugin_manifests(target: Path) -> list[str]:
    return [path for path in PLUGIN_MANIFEST_CANDIDATES if (target / path).is_file()]


def _manifest_relative_file(target: Path, raw: object, label: str) -> Path:
    repair_hint = (
        "; run an approved Harness repair or migrate-layout"
        if label == "canonical Harness Skill"
        else ""
    )
    if not isinstance(raw, str) or not raw:
        fail(f"{label} must be a non-empty relative path{repair_hint}")
    if re.match(r"^[A-Za-z]:[\\/]", raw) or "\\" in raw:
        fail(f"{label} must stay inside target and use POSIX relative syntax{repair_hint}")
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        fail(f"{label} must stay inside target{repair_hint}")
    target = target.expanduser().resolve()
    candidate = target / relative
    cursor = candidate
    while cursor != target:
        if cursor.is_symlink():
            fail(f"{label} cannot contain a symlink: {cursor.relative_to(target)}{repair_hint}")
        cursor = cursor.parent
    if not candidate.exists():
        fail(f"missing {label}: {raw}{repair_hint}")
    if not candidate.is_file():
        fail(f"{label} must resolve to a regular file: {raw}{repair_hint}")
    try:
        candidate.resolve(strict=True).relative_to(target.resolve())
    except (OSError, ValueError):
        fail(f"{label} resolves outside target: {raw}{repair_hint}")
    return candidate


def check_harness_skill_contract(
    target: Path,
    manifest: dict,
    *,
    allow_legacy: bool,
) -> str:
    fields = ("harness_skill_path", "harness_skill_version", "harness_skill_managed")
    present = [field for field in fields if field in manifest]
    if not present:
        if allow_legacy:
            surface_rel = manifest.get("instruction_surface")
            if not isinstance(surface_rel, str) or not surface_rel:
                surface_rel = "SKILL.md" if (target / "SKILL.md").is_file() else "AGENTS.md"
            surface = _manifest_relative_file(target, surface_rel, "legacy instruction_surface")
            content = content_after_frontmatter(read_text(surface)).lstrip()
            lines = content.splitlines()
            has_legacy_prelude = content.startswith(STATUS_PRELUDE_HEADINGS) or bool(
                lines
                and lines[0].startswith("# ")
                and "\n".join(lines[1:]).lstrip().startswith(STATUS_PRELUDE_HEADINGS)
            )
            if not has_legacy_prelude:
                fail(
                    "legacy wrapper manifest has no compatible status prelude; "
                    "run an approved Harness repair or migrate-layout"
                )
            warn(
                "legacy wrapper manifest has no canonical Harness Skill identity; "
                "run migrate-layout before the next Harness write"
            )
            return "legacy_compatible"
        fail(f"{TARGET_WRAPPER_MANIFEST} missing canonical Harness Skill identity")
    if len(present) != len(fields):
        fail(f"{TARGET_WRAPPER_MANIFEST} has an incomplete canonical Harness Skill identity")

    path_value = manifest.get("harness_skill_path")
    if path_value != TARGET_HARNESS_SKILL:
        fail(f"harness_skill_path must use canonical path {TARGET_HARNESS_SKILL}")
    if manifest.get("harness_skill_version") != HARNESS_SKILL_VERSION:
        fail(
            "incompatible canonical Harness Skill version: "
            f"{manifest.get('harness_skill_version')}; expected {HARNESS_SKILL_VERSION}; "
            "run an approved compatible Harness migration"
        )
    if manifest.get("harness_skill_managed") is not True:
        fail("canonical Harness Skill must remain wrapper managed")
    managed_files = manifest.get("managed_files")
    if not isinstance(managed_files, list) or TARGET_HARNESS_SKILL not in managed_files:
        fail("canonical Harness Skill must be listed in managed_files")

    harness_path = _manifest_relative_file(target, path_value, "canonical Harness Skill")
    text = read_text(harness_path)
    frontmatter = re.match(r"\A---\r?\n(?P<body>.*?)\r?\n(?:---|\.\.\.)\r?\n", text, re.DOTALL)
    if not frontmatter:
        fail(
            "canonical Harness Skill frontmatter is missing or malformed; "
            "run an approved Harness repair or migrate-layout"
        )
    body = frontmatter.group("body")
    if not re.search(r"(?m)^name:[ \t]*[\"']?using-evozeus-harness[\"']?[ \t]*\r?$", body):
        fail(
            "canonical Harness Skill frontmatter name must be using-evozeus-harness; "
            "run an approved Harness repair"
        )
    metadata = re.search(
        r"(?m)^metadata:[ \t]*\r?\n(?P<values>(?:^[ \t]+[^\r\n]*(?:\r?\n|$))*)",
        body,
    )
    if not metadata or not re.search(
        rf"(?m)^[ \t]+version:[ \t]*[\"']?{re.escape(HARNESS_SKILL_VERSION)}[\"']?[ \t]*\r?$",
        metadata.group("values"),
    ):
        fail(
            f"canonical Harness Skill frontmatter version must be {HARNESS_SKILL_VERSION}; "
            "run an approved Harness repair"
        )
    missing_terms = [term for term in HARNESS_SKILL_TERMS if term not in text]
    if missing_terms:
        fail(
            "canonical Harness Skill missing required concepts: "
            + ", ".join(missing_terms)
            + "; run an approved Harness repair"
        )
    ok(f"canonical Harness Skill contract is valid: {TARGET_HARNESS_SKILL}@{HARNESS_SKILL_VERSION}")
    return "canonical"


def _canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def check_migration_contract(target: Path, manifest: dict) -> None:
    identity = manifest.get("migration_contract")
    if not isinstance(identity, dict):
        fail(f"{TARGET_WRAPPER_MANIFEST} missing migration_contract identity")
    expected_identity = {
        "migration_protocol_version": MIGRATION_PROTOCOL_VERSION,
        "contract_id": "evozeus-harness-migration",
        "contract_version": "v1.0.0",
        "path": TARGET_MIGRATION_CONTRACT,
    }
    mismatches = [
        field
        for field, expected in expected_identity.items()
        if identity.get(field) != expected
    ]
    if mismatches:
        fail(
            f"{TARGET_WRAPPER_MANIFEST} migration_contract identity mismatch: "
            + ", ".join(mismatches)
        )
    managed_files = manifest.get("managed_files")
    if not isinstance(managed_files, list) or TARGET_MIGRATION_CONTRACT not in managed_files:
        fail("migration contract must be listed in managed_files")
    path = _manifest_relative_file(target, identity.get("path"), "migration contract")
    actual_sha256 = f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
    if identity.get("sha256") != actual_sha256:
        fail(
            "migration contract hash does not match wrapper manifest: "
            f"expected={identity.get('sha256')}; actual={actual_sha256}"
        )
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"invalid migration contract: {exc}")
    if not isinstance(contract, dict):
        fail("migration contract must be a JSON object")
    if contract.get("schema_version") != "evozeus.coevolve.harness-migration-contract.v1":
        fail("migration contract schema_version is incompatible")
    if contract.get("migration_protocol_version") != MIGRATION_PROTOCOL_VERSION:
        fail("migration contract protocol version is incompatible")
    if contract.get("current_harness_skill_version") != HARNESS_SKILL_VERSION:
        fail("migration contract current Harness Skill version is incompatible")
    if contract.get("path_roots") != {
        "artifact_path": "contracts/v1",
        "repository_path": "repository_root",
        "target_path": "target_repository_root",
    }:
        fail("migration contract path roots are ambiguous")
    expected_official_upgrade = {
        "protocol_path": "migrations/protocols/official-upgrade-protocol-v1.json",
        "current_closure_pointer": "migrations/history/harness-skill/current.json",
        "current_profile_pointer": "migrations/profiles/current.json",
        "profile_schema": "migrations/schemas/official-upgrade-profile-v1.schema.json",
        "closure_schema": "migrations/schemas/target-closure-v1.schema.json",
        "candidate_execution": "trusted_base_verifier_candidate_blobs_as_data",
    }
    if contract.get("official_upgrade") != expected_official_upgrade:
        fail("migration contract official-upgrade locators are incompatible")
    profiles = contract.get("discovery_profiles")
    if not isinstance(profiles, list) or not profiles:
        fail("migration contract must declare discovery profiles")
    for profile in profiles:
        if not isinstance(profile, dict):
            fail("migration discovery profile must be an object")
        fields = (
            "profile_id",
            "profile_version",
            "adapter_id",
            "adapter_version",
            "adapter_sha256",
            "adapter_payload",
        )
        if any(not profile.get(field) for field in fields):
            fail("migration discovery profile identity is incomplete")
        payload = profile["adapter_payload"]
        if not isinstance(payload, dict):
            fail(f"migration adapter payload must be an object: {profile['profile_id']}")
        if profile["adapter_sha256"] != _canonical_json_sha256(payload):
            fail(f"migration adapter digest mismatch: {profile['profile_id']}")
        if (
            profile.get("automatic") is not False
            or profile.get("default_decision") != "manual_migration_required"
            or payload.get("destructive_authority") is not False
            or payload.get("discovery_candidates_are_authority") is not False
        ):
            fail(
                "migration discovery profile must be manual and zero-write: "
                f"{profile['profile_id']}"
            )
    expected_authority_rules = {
        "discovery_candidates_are_authority": False,
        "manifest_managed_flag_is_sufficient": False,
        "exact_preimage_hash_required": True,
        "snapshot_required_before_write": True,
        "post_verify_failure": "restore_snapshot",
        "automatic_authority_source": "external_hash_bound_official_upgrade_profile",
    }
    if contract.get("authority_rules") != expected_authority_rules:
        fail("migration contract authority rules are incompatible")
    ok(
        "stable migration contract is manifest-bound: "
        f"{TARGET_MIGRATION_CONTRACT}@{MIGRATION_PROTOCOL_VERSION}"
    )


def _canonical_harness_entry_block() -> str:
    return "\n".join(
        [
            HARNESS_ENTRY_BEGIN,
            "**CRITICAL — 进入业务主链路前 MUST 使用 Read 工具读取并执行",
            f"[{TARGET_HARNESS_SKILL}]({TARGET_HARNESS_SKILL})。**",
            HARNESS_ENTRY_END,
        ]
    )


def _mask_markdown_fenced_code(text: str) -> str:
    """Mask non-contract Markdown bytes while preserving offsets and newlines."""
    masked: list[str] = []
    offset = 0
    frontmatter_end = _frontmatter_end(text)
    fence: tuple[str, int] | None = None
    html_block: tuple[str, re.Pattern[str] | None] | None = None

    def mask_line(line: str) -> str:
        return "".join(character if character in "\r\n" else " " for character in line)

    def is_complete_html_tag(line: str) -> bool:
        match = re.match(r"^[ ]{0,3}</?[A-Za-z][A-Za-z0-9-]*", line)
        if not match:
            return False
        quote: str | None = None
        for index in range(match.end(), len(line)):
            character = line[index]
            if quote:
                if character == quote:
                    quote = None
                continue
            if character in {"'", '"'}:
                quote = character
                continue
            if character == ">":
                return not line[index + 1 :].strip()
        return False

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if offset < frontmatter_end:
            masked.append(mask_line(line))
            offset += len(line)
            continue
        if fence:
            fence_char, minimum_length = fence
            if re.match(
                rf"^[ ]{{0,3}}{re.escape(fence_char)}{{{minimum_length},}}[ \t]*$",
                content,
            ):
                fence = None
            masked.append(mask_line(line))
            offset += len(line)
            continue
        if html_block:
            mode, end_pattern = html_block
            if (mode == "blank" and not content.strip()) or (
                end_pattern is not None and end_pattern.search(content)
            ):
                html_block = None
            masked.append(mask_line(line))
            offset += len(line)
            continue
        fence_match = re.match(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$", content)
        if fence_match:
            marker = fence_match.group(1)
            fence = (marker[0], len(marker))
            masked.append(mask_line(line))
        elif re.fullmatch(
            rf"(?:{re.escape(HARNESS_ENTRY_BEGIN)}|{re.escape(HARNESS_ENTRY_END)})[ \t]*",
            content,
        ):
            masked.append(line)
        elif html_match := re.match(
            r"^[ ]{0,3}<(script|pre|style|textarea)(?:[ \t>]|$)",
            content,
            re.IGNORECASE,
        ):
            end_pattern = re.compile(rf"</{html_match.group(1)}[ \t]*>", re.IGNORECASE)
            if not end_pattern.search(content[html_match.end() :]):
                html_block = ("pattern", end_pattern)
            masked.append(mask_line(line))
        elif re.match(r"^[ ]{0,3}<!--", content):
            if "-->" not in content[content.find("<!--") + 4 :]:
                html_block = ("pattern", re.compile(r"-->"))
            masked.append(mask_line(line))
        elif re.match(r"^[ ]{0,3}<\?", content):
            if "?>" not in content[content.find("<?") + 2 :]:
                html_block = ("pattern", re.compile(r"\?>"))
            masked.append(mask_line(line))
        elif re.match(r"^[ ]{0,3}<![A-Z]", content):
            if ">" not in content[content.find("<!") + 2 :]:
                html_block = ("pattern", re.compile(r">"))
            masked.append(mask_line(line))
        elif re.match(r"^[ ]{0,3}<!\[CDATA\[", content):
            if "]]>" not in content[content.find("<![CDATA[") + 9 :]:
                html_block = ("pattern", re.compile(r"\]\]>"))
            masked.append(mask_line(line))
        elif re.match(
            r"^[ ]{0,3}</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:[ \t/>]|$)",
            content,
            re.IGNORECASE,
        ) or is_complete_html_tag(content):
            html_block = ("blank", None)
            masked.append(mask_line(line))
        elif re.match(r"^(?: {4,}|\t)", content):
            masked.append(mask_line(line))
        else:
            masked.append(line)
        offset += len(line)
    return "".join(masked)


def check_harness_entry_contract(target: Path, manifest: dict) -> None:
    if manifest.get("harness_skill_path") != TARGET_HARNESS_SKILL:
        fail(f"Harness entry manifest does not match canonical path {TARGET_HARNESS_SKILL}")
    surface_rel = manifest.get("instruction_surface")
    surface = _manifest_relative_file(target, surface_rel, "instruction_surface")
    text = read_text(surface).replace("\r\n", "\n")
    visible = _mask_markdown_fenced_code(text)
    canonical_block = _canonical_harness_entry_block()
    entry_pattern = re.compile(
        "^"
        + r"\n".join(re.escape(line) for line in canonical_block.splitlines())
        + r"[ \t]*$",
        re.MULTILINE,
    )
    entries = list(entry_pattern.finditer(visible))
    if len(entries) != 1:
        marker_pattern = re.compile(
            rf"^(?:(?P<begin>{re.escape(HARNESS_ENTRY_BEGIN)})|"
            rf"(?P<end>{re.escape(HARNESS_ENTRY_END)}))[ \t]*$",
            re.MULTILINE,
        )
        markers = list(marker_pattern.finditer(visible))
        begins = [match for match in markers if match.group("begin")]
        ends = [match for match in markers if match.group("end")]
        if (
            not entries
            and len(begins) == 1
            and len(ends) == 1
            and begins[0].start() < ends[0].start()
        ):
            fail("instruction surface Harness Skill link does not match the canonical manifest path")
        fail("instruction surface must contain exactly one canonical Harness Skill activation block")
    start = entries[0].start()
    end = start + len(canonical_block)
    block = text[start:end]
    if block != _canonical_harness_entry_block():
        fail("instruction surface Harness Skill link does not match the canonical manifest path")
    if len(block.splitlines()) > 8:
        fail("instruction surface Harness Skill activation block exceeds 8 lines")

    content = content_after_frontmatter(text).lstrip()
    lines = content.splitlines()
    at_entry = content.startswith(HARNESS_ENTRY_BEGIN)
    after_title = bool(
        lines
        and lines[0].startswith("# ")
        and "\n".join(lines[1:]).lstrip().startswith(HARNESS_ENTRY_BEGIN)
    )
    if not (at_entry or after_title):
        fail("canonical Harness Skill activation block must precede the business main flow")
    ok(f"instruction surface activates canonical Harness Skill: {surface_rel}")


def check_integration_contract(target: Path, manifest: dict | None) -> None:
    integration = (manifest or {}).get("integration") or {}
    registration = ((manifest or {}).get("hook_registration") or {}).get("codex") or {}
    mode = integration.get("mode")
    capabilities = integration.get("capabilities") or {}
    repo_hook = capabilities.get("repo_maintenance_hook") or {}
    global_dispatcher = capabilities.get("global_session_dispatcher") or {}
    prompt_watcher = capabilities.get("global_prompt_lesson_watcher") or {}
    skill_entry = capabilities.get("skill_entry_preflight") or {}
    invocation_hook = capabilities.get("skill_invocation_hook") or {}

    if repo_hook.get("covers_skill_invocation"):
        fail("repo_maintenance_hook cannot claim Skill-invocation coverage")
    if global_dispatcher.get("covers_skill_invocation"):
        fail("global_session_dispatcher cannot claim per-Skill invocation coverage")
    if global_dispatcher.get("installed") or global_dispatcher.get("native_enforced"):
        fail("portable manifest cannot persist user-level global dispatcher installation state")
    if global_dispatcher.get("trust_status") not in {None, "not_installed"}:
        fail("portable manifest cannot persist user-level global dispatcher trust state")
    if prompt_watcher.get("covers_skill_invocation"):
        fail("global_prompt_lesson_watcher cannot claim per-Skill invocation coverage")
    if prompt_watcher.get("installed") or prompt_watcher.get("native_enforced"):
        fail("portable manifest cannot persist user-level prompt watcher installation state")
    if prompt_watcher.get("trust_status") not in {None, "not_installed"}:
        fail("portable manifest cannot persist user-level prompt watcher trust state")
    if prompt_watcher and prompt_watcher.get("event") != "UserPromptSubmit":
        fail("global_prompt_lesson_watcher event must be UserPromptSubmit")
    if skill_entry.get("native_enforced"):
        fail("skill_entry_preflight is prompt-compliance based, not native enforcement")
    if skill_entry.get("installed"):
        surface_rel = (manifest or {}).get("instruction_surface") or integration.get("root_entry")
        if not isinstance(surface_rel, str) or not surface_rel:
            fail("skill_entry_preflight installation requires an instruction_surface")
        relative_surface = Path(surface_rel)
        if relative_surface.is_absolute() or ".." in relative_surface.parts:
            fail("skill_entry_preflight instruction_surface must stay inside target")
        surface = target / relative_surface
        cursor = surface
        while cursor != target:
            if cursor.is_symlink():
                fail("skill_entry_preflight instruction_surface cannot use symlink components")
            cursor = cursor.parent
        try:
            surface.resolve(strict=True).relative_to(target.resolve())
        except (OSError, ValueError):
            fail("skill_entry_preflight instruction_surface is missing or outside target")
        if not surface.is_file():
            fail("skill_entry_preflight instruction_surface is missing")
        if (manifest or {}).get("harness_skill_path") is not None:
            check_harness_entry_contract(target, manifest or {})
        else:
            content = content_after_frontmatter(surface.read_text(encoding="utf-8")).lstrip()
            lines = content.splitlines()
            if content.startswith(STATUS_PRELUDE_HEADINGS):
                has_status_prelude = True
            else:
                has_status_prelude = bool(
                    lines
                    and lines[0].startswith("# ")
                    and "\n".join(lines[1:]).lstrip().startswith(STATUS_PRELUDE_HEADINGS)
                )
            if not has_status_prelude:
                fail("legacy skill_entry_preflight installation requires the status prelude")
    if registration.get("capability") == "repo_maintenance_hook":
        if registration.get("scope") != "canonical_repository":
            fail("repo_maintenance_hook registration scope must be canonical_repository")
        if registration.get("covers_skill_invocation"):
            fail("repo_maintenance_hook registration cannot claim Skill-invocation coverage")

    if not mode:
        warn("wrapper manifest has no integration.mode; treating runtime checks as prompt/manual fallback")
        return

    if mode == "native_host_hook":
        if not integration.get("native_skill_invocation_hook_installed"):
            fail("native Skill-invocation coverage requires explicit invocation-hook evidence")
        if not invocation_hook.get("supported") or not invocation_hook.get("installed"):
            fail("native Skill-invocation coverage requires a supported installed SkillInvoke hook")
        ok("integration contract has native Skill-invocation hook evidence")
        return

    if mode in {"bootstrap_skill", "prompt_runtime_check", "manual_only"}:
        if integration.get("native_skill_invocation_hook_installed"):
            fail(f"integration.mode={mode} conflicts with native Skill-invocation hook installation")
        if integration.get("native_host_hook_installed"):
            fail("deprecated native_host_hook_installed cannot overstate Skill-invocation coverage")
        ok(f"integration contract declares non-native mode: {mode}")
        return

    fail(f"unknown integration.mode: {mode}")


def check_onboarding_contract(manifest: dict | None) -> None:
    def nonempty_string(value: object) -> bool:
        return isinstance(value, str) and bool(value.strip())

    onboarding = (manifest or {}).get("onboarding")
    if not isinstance(onboarding, dict):
        fail("wrapper manifest must contain an onboarding contract")

    installation = onboarding.get("installation")
    if not isinstance(installation, dict):
        fail("onboarding.installation must be an object")
    if installation.get("mode") != "canonical_repo_symlink":
        fail("onboarding.installation.mode must be canonical_repo_symlink")
    if not nonempty_string(installation.get("command")) or not nonempty_string(
        installation.get("verification")
    ):
        fail("onboarding.installation must provide command and verification")

    invocation = onboarding.get("invocation")
    if not isinstance(invocation, dict):
        fail("onboarding.invocation must be an object")
    if invocation.get("mode") != "host_skill_discovery" or invocation.get("owner") != "target_skill":
        fail("onboarding.invocation must use host_skill_discovery owned by target_skill")
    invocation_verification = invocation.get("verification")
    if not nonempty_string(invocation.get("instruction")) or not (
        isinstance(invocation_verification, str)
        and "consumer-project smoke test" in invocation_verification
    ):
        fail("onboarding.invocation must provide instructions and a consumer-project smoke test")

    initialization = onboarding.get("initialization")
    if not isinstance(initialization, dict):
        fail("onboarding.initialization must be an object")
    if initialization.get("owner") != "target_skill":
        fail("onboarding.initialization.owner must be target_skill")
    if not isinstance(initialization.get("required"), bool):
        fail("onboarding.initialization.required must be boolean")
    if initialization.get("required") and not (
        nonempty_string(initialization.get("command"))
        and nonempty_string(initialization.get("verification"))
    ):
        fail("required onboarding initialization must provide command and verification")

    children = onboarding.get("generated_child_skills")
    if not isinstance(children, dict):
        fail("onboarding.generated_child_skills must be an object")
    if children.get("hooks_inherited") is not False:
        fail("generated child Skills must explicitly declare hooks_inherited=false")
    if not isinstance(children.get("supported"), bool):
        fail("onboarding.generated_child_skills.supported must be boolean")
    if children.get("supported"):
        if children.get("repo_harness_inherited") is not True:
            fail("generated child Skills must inherit the parent repository Harness")
        if children.get("attachment") != "inherited_repo_harness":
            fail("generated child Skills must use inherited_repo_harness attachment")
        if children.get("separate_harness_boundary") != "independent_git_repository":
            fail("a generated child may own a separate Harness only as an independent Git repository")
        verification = children.get("verification") or ""
        required_terms = ["repository structure preflight", "consumer-project smoke test"]
        if not all(term in verification for term in required_terms):
            fail("generated child Skill verification must include parent repository preflight and consumer-project smoke test")
    ok("onboarding contract is complete")


def check_dashboard_contract(manifest: dict | None) -> None:
    dashboard = (manifest or {}).get("dashboard")
    if not isinstance(dashboard, dict):
        fail("wrapper manifest must contain a dashboard deployment contract")
    if dashboard.get("deployment_mode") != "opt_in_github_pages":
        fail("dashboard.deployment_mode must be opt_in_github_pages")
    if dashboard.get("enablement_variable") != "EVOZEUS_PAGES_ENABLED":
        fail("dashboard.enablement_variable must be EVOZEUS_PAGES_ENABLED")
    if dashboard.get("fallback") != "repository_only":
        fail("dashboard.fallback must be repository_only")
    ok("dashboard deployment contract is complete")


def skill_name_from_skill_md(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def target_canonical_path(target: Path) -> str:
    git_root_result = run_command(["git", "-C", str(target), "rev-parse", "--show-toplevel"])
    if git_root_result.returncode == 0 and git_root_result.stdout.strip():
        return str(Path(git_root_result.stdout.strip()).expanduser().resolve())
    return str(target.expanduser().resolve())


def git_origin_repo(path: Path) -> str | None:
    remote_result = run_command(["git", "-C", str(path), "remote", "get-url", "origin"])
    if remote_result.returncode != 0:
        return None
    return repo_from_remote(remote_result.stdout)


def repo_from_remote(remote_url: str) -> str | None:
    remote_url = remote_url.strip()
    match = re.match(r"^https://github\.com/([^/]+/[^/.]+)(?:\.git)?$", remote_url)
    if match:
        return match.group(1)
    match = re.match(r"^git@github\.com:([^/]+/[^/.]+)(?:\.git)?$", remote_url)
    if match:
        return match.group(1)
    return None


def gh_current_login() -> str | None:
    result = run_command(["gh", "api", "user", "--jq", ".login"])
    return result.stdout.strip() if result.returncode == 0 else None


def gh_orgs() -> list[str]:
    result = run_command(["gh", "api", "user/orgs", "--jq", ".[].login"])
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def gh_search_repos(query: str) -> list[str]:
    result = run_command(["gh", "search", "repos", query, "--json", "fullName", "--limit", "10"])
    if result.returncode != 0:
        return []
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return [row["fullName"] for row in rows if row.get("fullName")]


def discover_repo_candidates(skill_name: str) -> list[str]:
    candidates: list[str] = []
    login = gh_current_login()
    if login:
        candidates.extend(gh_search_repos(f"{skill_name} user:{login}"))
    for org in gh_orgs():
        for repo in gh_search_repos(f"{skill_name} org:{org}"):
            if repo not in candidates:
                candidates.append(repo)
    if candidates:
        return candidates
    for repo in gh_search_repos(skill_name):
        if repo not in candidates:
            candidates.append(repo)
    return candidates


def is_repo_not_found(output: str) -> bool:
    markers = [
        "Could not resolve to a Repository",
        "Not Found",
        "HTTP 404",
        "repository not found",
    ]
    return any(marker.lower() in output.lower() for marker in markers)


def check_terms(text: str, term_groups: list[list[str]], label: str) -> None:
    missing = []
    for group in term_groups:
        if not has_any(text, group):
            missing.append("/".join(group))
    if missing:
        fail(f"{label} missing required concepts: {', '.join(missing)}")


def _frontmatter_end(text: str) -> int:
    lines = text.splitlines(keepends=True)
    if not lines or not re.fullmatch(r"---[ \t]*", lines[0].rstrip("\r\n")):
        return 0
    offset = len(lines[0])
    body_lines: list[str] = []
    for line in lines[1:]:
        offset += len(line)
        if re.fullmatch(r"(?:---|\.\.\.)[ \t]*", line.rstrip("\r\n")):
            break
        body_lines.append(line.rstrip("\r\n"))
    else:
        return 0

    flow_lines = list(body_lines)
    while flow_lines and (not flow_lines[0].strip() or flow_lines[0].lstrip().startswith("#")):
        flow_lines.pop(0)
    while flow_lines and (not flow_lines[-1].strip() or flow_lines[-1].lstrip().startswith("#")):
        flow_lines.pop()
    flow_candidate = "\n".join(flow_lines).strip()
    if flow_candidate.startswith("{") and flow_candidate.endswith("}"):
        inner = flow_candidate[1:-1]
        quote: str | None = None
        quote_closes_key = False
        escaped = False
        comment = False
        frames = [
            {
                "kind": "map",
                "content": False,
                "separator": False,
                "items": 0,
                "key_closed": False,
                "closes_key": False,
                "value_started": False,
                "value_complete": False,
                "node_properties": False,
                "property_pending": False,
            }
        ]
        valid_flow = True
        for index, character in enumerate(inner):
            if comment:
                if character in "\r\n":
                    comment = False
                continue
            if escaped:
                escaped = False
                continue
            if quote == '"' and character == "\\":
                escaped = True
                continue
            if quote:
                if character == quote:
                    quote = None
                    if quote_closes_key:
                        frames[-1]["key_closed"] = True
                    quote_closes_key = False
                continue
            if character in {"'", '"'}:
                frame = frames[-1]
                if frame["value_complete"]:
                    valid_flow = False
                    break
                frame["property_pending"] = False
                quote = character
                quote_closes_key = not frame["content"] and not frame["separator"]
                if not quote_closes_key:
                    frame["key_closed"] = False
                frame["content"] = True
                if frame["separator"]:
                    frame["value_started"] = True
                    frame["node_properties"] = False
            elif character == "#" and (
                not frames[-1]["property_pending"]
                and (index == 0 or inner[index - 1].isspace() or inner[index - 1] in ",[]{}:")
            ):
                comment = True
            elif character in "[{":
                parent = frames[-1]
                parent["property_pending"] = False
                if parent["value_complete"] or (
                    parent["separator"]
                    and parent["value_started"]
                    and not parent["node_properties"]
                ) or (
                    not parent["separator"]
                    and parent["content"]
                    and not (parent["node_properties"] and not parent["value_started"])
                ):
                    valid_flow = False
                    break
                closes_key = (
                    not parent["separator"]
                    and not parent["value_started"]
                    and (not parent["content"] or parent["node_properties"])
                )
                parent["content"] = True
                if parent["separator"]:
                    parent["value_started"] = True
                parent["node_properties"] = False
                if not closes_key:
                    parent["key_closed"] = False
                frames.append(
                    {
                        "kind": "sequence" if character == "[" else "map",
                        "content": False,
                        "separator": False,
                        "items": 0,
                        "key_closed": False,
                        "closes_key": closes_key,
                        "value_started": False,
                        "value_complete": False,
                        "node_properties": False,
                        "property_pending": False,
                    }
                )
            elif character in "]}":
                expected = "sequence" if character == "]" else "map"
                if len(frames) == 1 or frames[-1]["kind"] != expected:
                    valid_flow = False
                    break
                frame = frames.pop()
                if frame["property_pending"] or (
                    frame["node_properties"] and not frame["value_started"]
                ):
                    valid_flow = False
                    break
                if frame["content"]:
                    frame["items"] += 1
                if frame["closes_key"]:
                    frames[-1]["key_closed"] = True
                else:
                    frames[-1]["value_complete"] = True
                    frames[-1]["value_started"] = True
            elif character == ",":
                frame = frames[-1]
                if frame["property_pending"]:
                    continue
                if (
                    not frame["content"]
                    or frame["property_pending"]
                    or (frame["node_properties"] and not frame["value_started"])
                ):
                    valid_flow = False
                    break
                frame["items"] += 1
                frame["content"] = False
                frame["separator"] = False
                frame["key_closed"] = False
                frame["value_started"] = False
                frame["value_complete"] = False
                frame["node_properties"] = False
                frame["property_pending"] = False
            elif character == ":":
                frame = frames[-1]
                if frame["property_pending"]:
                    continue
                if frame["value_complete"]:
                    valid_flow = False
                    break
                next_character = inner[index + 1 : index + 2]
                is_separator = (
                    not next_character
                    or next_character.isspace()
                    or next_character in ",[]{}"
                    or bool(frame["key_closed"])
                )
                if not is_separator:
                    frame["content"] = True
                    frame["key_closed"] = False
                    if frame["separator"]:
                        frame["value_started"] = True
                    continue
                if frame["kind"] == "map":
                    if not frame["content"]:
                        valid_flow = False
                        break
                    if frame["separator"]:
                        valid_flow = False
                        break
                    else:
                        frame["separator"] = True
                        frame["key_closed"] = False
                        frame["value_started"] = False
                        frame["value_complete"] = False
                        frame["node_properties"] = False
                else:
                    if not frame["content"]:
                        valid_flow = False
                        break
                    if frame["separator"]:
                        valid_flow = False
                        break
                    else:
                        frame["separator"] = True
                        frame["key_closed"] = False
                        frame["value_started"] = False
                        frame["value_complete"] = False
                        frame["node_properties"] = False
            elif character in "&!":
                frame = frames[-1]
                if frame["value_complete"]:
                    valid_flow = False
                    break
                if frame["property_pending"]:
                    continue
                if (
                    not frame["content"]
                    or (frame["separator"] and not frame["value_started"])
                    or (frame["node_properties"] and not frame["value_started"])
                ):
                    frame["content"] = True
                    frame["node_properties"] = True
                    frame["property_pending"] = True
                    frame["key_closed"] = False
                else:
                    frame["key_closed"] = False
            elif not character.isspace():
                frame = frames[-1]
                if frame["value_complete"]:
                    valid_flow = False
                    break
                if frame["property_pending"]:
                    continue
                frame["content"] = True
                frame["key_closed"] = False
                if frame["separator"]:
                    frame["value_started"] = True
                    frame["node_properties"] = False
                elif frame["node_properties"]:
                    frame["value_started"] = True
                    frame["node_properties"] = False
        valid_flow = valid_flow and quote is None and len(frames) == 1
        root = frames[0]
        if root["content"]:
            root["items"] += 1
        if valid_flow and (not inner.strip() or root["items"]):
            return offset
        return 0

    def mapping_key_separator(line: str) -> int | None:
        quote: str | None = None
        escaped = False
        for index, character in enumerate(line):
            if escaped:
                escaped = False
                continue
            if quote == '"' and character == "\\":
                escaped = True
                continue
            if quote:
                if character == quote:
                    quote = None
                continue
            if character in {"'", '"'}:
                quote = character
                continue
            if character == ":" and (index + 1 == len(line) or line[index + 1] in " \t"):
                return index if line[:index].strip() else None
        return None

    saw_mapping_key = False
    explicit_key = False
    mapping_tag = False
    allows_indentless_sequence = False
    for line in body_lines:
        stripped = line.strip()
        if not stripped or line.lstrip().startswith("#"):
            continue
        if stripped in {"{}", "!!map {}"} and not saw_mapping_key:
            saw_mapping_key = True
            continue
        if stripped == "!!map" and not saw_mapping_key:
            mapping_tag = True
            continue
        if line.startswith((" ", "\t")) and (saw_mapping_key or mapping_tag):
            continue
        if allows_indentless_sequence and (line == "-" or line.startswith("- ")):
            continue
        if line.startswith("? "):
            explicit_key = True
            continue
        if explicit_key and (line == ":" or line.startswith(": ")):
            saw_mapping_key = True
            explicit_key = False
            continue
        separator = mapping_key_separator(line)
        if separator is not None:
            saw_mapping_key = True
            allows_indentless_sequence = not line[separator + 1 :].strip()
            continue
        return 0
    return offset if saw_mapping_key and not explicit_key else 0


def content_after_frontmatter(text: str) -> str:
    return text[_frontmatter_end(text) :]


def check_status_prelude(skill_text: str, label: str = "SKILL.md") -> None:
    content = content_after_frontmatter(skill_text).lstrip()
    if not content.startswith(STATUS_PRELUDE_HEADINGS):
        fail(f"{label} must start with the EvoZeus-CoEvolve status check after frontmatter")
    check_runtime_safe_status_prelude(skill_text, label)


def root_entry_path(target: Path) -> Path:
    manifest = load_wrapper_manifest(target)
    if manifest and manifest.get("instruction_surface"):
        raw_surface = manifest["instruction_surface"]
        relative = Path(raw_surface) if isinstance(raw_surface, str) else Path("")
        if (
            not isinstance(raw_surface, str)
            or re.match(r"^[A-Za-z]:[\\/]", raw_surface)
            or "\\" in raw_surface
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            fail(f"manifest instruction_surface must stay inside target: {raw_surface}")
        manifest_surface = target / relative
        cursor = manifest_surface
        while cursor != target:
            if cursor.is_symlink():
                fail(
                    "manifest instruction_surface cannot use symlink components: "
                    f"{raw_surface}"
                )
            cursor = cursor.parent
        try:
            manifest_surface.resolve(strict=True).relative_to(target.resolve())
        except (OSError, ValueError):
            fail(f"manifest instruction_surface is missing or outside target: {raw_surface}")
        if manifest_surface.is_file():
            return manifest_surface
        fail(f"manifest instruction_surface is missing: {manifest['instruction_surface']}")
    skill = target / "SKILL.md"
    if skill.exists():
        return skill
    agents = target / "AGENTS.md"
    if agents.exists():
        return agents
    fail(
        "target must contain a detectable evolution instruction surface: "
        f"root SKILL.md, root AGENTS.md, or {TARGET_WRAPPER_MANIFEST} instruction_surface selected by diagnosis"
    )


def check_agents_status_prelude(agents_text: str) -> None:
    content = content_after_frontmatter(agents_text).lstrip()
    if content.startswith(STATUS_PRELUDE_HEADINGS):
        check_runtime_safe_status_prelude(agents_text, "AGENTS.md")
        return
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        rest = "\n".join(lines[1:]).lstrip()
        if rest.startswith(STATUS_PRELUDE_HEADINGS):
            check_runtime_safe_status_prelude(agents_text, "AGENTS.md")
            return
    fail("AGENTS.md must put the EvoZeus-CoEvolve status check before the main runtime instructions")


def normalize_relative_path(raw: str) -> str:
    cleaned = raw.strip().strip("`'\"").strip()
    cleaned = cleaned.rstrip(".,;:)")
    return cleaned.replace("\\", "/")


def referenced_runtime_files(text: str) -> list[str]:
    files: list[str] = []
    for match in RUNTIME_REFERENCE_RE.finditer(text):
        rel = normalize_relative_path(match.group("path"))
        if rel and rel not in files:
            files.append(rel)
    return files


def strip_wrapper_runtime_sections(text: str) -> str:
    kept: list[str] = []
    skipping = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in WRAPPER_RUNTIME_SECTION_HEADINGS:
            skipping = True
            continue
        if skipping and re.match(r"^#{1,6}\s+", stripped) and stripped not in WRAPPER_RUNTIME_SECTION_HEADINGS:
            skipping = False
        if not skipping:
            kept.append(line)
    return "\n".join(kept)


def add_tree_files(target: Path, dirname: str, files: list[str]) -> None:
    root = target / dirname
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(target))
            if rel not in files:
                files.append(rel)


def add_harness_runtime_files(files: list[str]) -> None:
    """Add the complete file closure required by the canonical Harness contract."""
    for path in REQUIRED_FILES:
        if path not in files:
            files.append(path)


def discover_runtime_bundle(target: Path) -> dict:
    manifest = load_wrapper_manifest(target)
    harness_runtime_path = None
    if manifest and any(
        field in manifest
        for field in ("harness_skill_path", "harness_skill_version", "harness_skill_managed")
    ):
        if (
            manifest.get("harness_skill_path") != TARGET_HARNESS_SKILL
            or manifest.get("harness_skill_version") != HARNESS_SKILL_VERSION
            or manifest.get("harness_skill_managed") is not True
        ):
            fail("runtime bundle has an invalid canonical Harness Skill identity")
        harness_runtime_path = TARGET_HARNESS_SKILL
    runtime_bundle = manifest.get("runtime_bundle") if manifest else None
    if isinstance(runtime_bundle, dict):
        instruction_surface = str(runtime_bundle.get("instruction_surface") or "SKILL.md")
        required = [
            normalize_relative_path(path)
            for path in runtime_bundle.get("required_files", [])
            if isinstance(path, str) and path.strip()
        ]
        if instruction_surface not in required:
            required.insert(0, instruction_surface)
        if harness_runtime_path:
            add_harness_runtime_files(required)
        optional = [
            normalize_relative_path(path)
            for path in runtime_bundle.get("optional_files", [])
            if isinstance(path, str) and path.strip()
        ]
        return {
            "instruction_surface": instruction_surface,
            "required_files": list(dict.fromkeys(required)),
            "optional_files": list(dict.fromkeys(optional)),
            "external_tools": runtime_bundle.get("external_tools", []),
            "source": f"{TARGET_WRAPPER_MANIFEST} runtime_bundle",
        }

    entry = root_entry_path(target)
    instruction_surface = str(entry.relative_to(target))
    required_files = [instruction_surface]
    text = entry.read_text(encoding="utf-8", errors="ignore")
    if TARGET_HARNESS_SKILL in text:
        harness_runtime_path = TARGET_HARNESS_SKILL
    if harness_runtime_path:
        add_harness_runtime_files(required_files)
    business_text = strip_wrapper_runtime_sections(text)
    for rel in referenced_runtime_files(business_text):
        if rel not in required_files:
            required_files.append(rel)
    for dirname in ["references", "assets", "templates"]:
        if f"{dirname}/" in business_text:
            add_tree_files(target, dirname, required_files)
    if "scripts/" in business_text:
        add_tree_files(target, "scripts", required_files)
    for metadata in ["agents/openai.yaml"]:
        if (target / metadata).is_file() and metadata not in required_files:
            required_files.append(metadata)
    return {
        "instruction_surface": instruction_surface,
        "required_files": required_files,
        "optional_files": [],
        "external_tools": [],
        "source": "discovered_from_instruction_surface",
    }


def check_runtime_safe_status_prelude(text: str, label: str) -> None:
    if not any(heading.removeprefix("## ") in text for heading in STATUS_PRELUDE_HEADINGS):
        return
    if "runtime-only install" not in text:
        fail(f"{label} wrapper status prelude must include runtime-only install fallback language")
    lowered = text.lower()
    for phrase in BLOCKING_STATUS_PHRASES:
        if phrase.lower() in lowered:
            fail(
                f"{label} wrapper status prelude contains blocking runtime language; "
                f"remove it and keep the runtime-only install fallback: {phrase}"
            )


def check_runtime(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    bundle = discover_runtime_bundle(target)
    missing = [path for path in bundle["required_files"] if not (target / path).is_file()]
    if missing:
        fail("missing required runtime files:\n" + "\n".join(f"- {path}" for path in missing))
    if TARGET_HARNESS_SKILL in bundle["required_files"]:
        manifest = load_wrapper_manifest(target)
        if manifest is None:
            fail(f"missing wrapper manifest: {TARGET_WRAPPER_MANIFEST}")
        check_harness_skill_contract(target, manifest, allow_legacy=False)
        check_migration_contract(target, manifest)
        check_harness_entry_contract(target, manifest)
    entry = target / bundle["instruction_surface"]
    check_runtime_safe_status_prelude(read_text(entry), bundle["instruction_surface"])
    ok("runtime bundle is complete")


def check_notice_policy(target: Path) -> None:
    path = target / TARGET_NOTICE_POLICY
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid notice policy {TARGET_NOTICE_POLICY}: {exc}")
    if not isinstance(policy, dict) or policy.get("schema_version") != "v1":
        fail(f"{TARGET_NOTICE_POLICY} schema_version must be v1")
    if policy.get("tag_style") != "markdown_code":
        fail(f"{TARGET_NOTICE_POLICY} tag_style must be markdown_code")
    if not isinstance(policy.get("show_signal_id"), bool):
        fail(f"{TARGET_NOTICE_POLICY} show_signal_id must be boolean")
    events = policy.get("events")
    if not isinstance(events, dict):
        fail(f"{TARGET_NOTICE_POLICY} events must be an object")
    for kind, required_states in NOTICE_REQUIRED_STATES.items():
        event = events.get(kind)
        if not isinstance(event, dict) or not isinstance(event.get("tag"), str):
            fail(f"{TARGET_NOTICE_POLICY} missing notice event: {kind}")
        if "show_state_label" in event and not isinstance(event["show_state_label"], bool):
            fail(f"{TARGET_NOTICE_POLICY} {kind} show_state_label must be boolean")
        if "details_separator" in event and not isinstance(event["details_separator"], str):
            fail(f"{TARGET_NOTICE_POLICY} {kind} details_separator must be a string")
        states = event.get("states")
        if not isinstance(states, dict) or not required_states.issubset(states):
            missing = sorted(required_states - set(states or {}))
            fail(f"{TARGET_NOTICE_POLICY} {kind} missing states: {', '.join(missing)}")
        for state in required_states:
            visual = states[state]
            if not isinstance(visual, dict) or not all(
                isinstance(visual.get(field), str) and visual[field].strip()
                for field in ("icon", "label")
            ):
                fail(f"{TARGET_NOTICE_POLICY} {kind}/{state} must define icon and label")
    ok("notice policy satisfies the target-Skill visual contract")


def check_maintainer(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    missing = [path for path in MAINTAINER_REQUIRED_FILES if not (target / path).exists()]
    if missing:
        fail("missing required maintainer wrapper files:\n" + "\n".join(f"- {path}" for path in missing))
    manifest = load_wrapper_manifest(target)
    if manifest is None:
        fail(f"missing wrapper manifest: {TARGET_WRAPPER_MANIFEST}")
    check_harness_skill_contract(target, manifest, allow_legacy=False)
    check_migration_contract(target, manifest)
    check_harness_entry_contract(target, manifest)
    check_notice_policy(target)
    check_onboarding_contract(manifest)
    check_dashboard_contract(manifest)
    check_integration_contract(target, manifest)
    check_runtime(args)
    ok("maintainer bundle contains required wrapper files")


def check_doctor(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    require_command("git")
    require_command("gh")

    git_root_result = run_command(["git", "-C", str(target), "rev-parse", "--show-toplevel"])
    if git_root_result.returncode != 0 or not git_root_result.stdout.strip():
        fail("Evolution Harness requires an independent Git repository")
    git_root = Path(git_root_result.stdout.strip()).resolve()
    if git_root != target:
        fail(f"Harness doctor must run at the Git repository root: {git_root}")

    auth = run_command(["gh", "auth", "status"])
    if auth.returncode != 0:
        fail("gh is installed but not authenticated; run gh auth login")
    ok("gh authenticated")

    repo = args.repo
    if repo and not GITHUB_REPO_RE.match(repo):
        fail(f"--repo must use OWNER/REPO format: {repo}")

    manifest = load_wrapper_manifest(target)
    if manifest:
        harness_state = check_harness_skill_contract(target, manifest, allow_legacy=True)
        if harness_state == "canonical":
            check_migration_contract(target, manifest)
        if manifest.get("harness_skill_path") is not None:
            check_harness_entry_contract(target, manifest)
        check_wrapper_managed_doctor(target, repo, manifest, args.allow_missing_repo)
        return

    remote_result = run_command(["git", "-C", str(git_root), "remote", "get-url", "origin"])
    if remote_result.returncode == 0:
        remote_repo = repo_from_remote(remote_result.stdout)
        if remote_repo:
            repo = repo or remote_repo
            ok(f"origin GitHub repo detected: {remote_repo}")
        else:
            fail(f"origin remote is not a GitHub repo: {remote_result.stdout.strip()}")
    else:
        fail("target independent Git repository has no GitHub origin")

    if repo:
        view = run_command(["gh", "repo", "view", repo, "--json", "nameWithOwner,url,visibility"])
        if view.returncode != 0:
            detail = (view.stderr or view.stdout or "").strip()
            fail(f"cannot access GitHub repo {repo}: {detail}")
        ok(f"GitHub repo accessible: {repo}")


def check_wrapper_managed_doctor(
    target: Path,
    requested_repo: str | None,
    manifest: dict,
    allow_missing_repo: bool,
) -> None:
    manifest_repo = manifest.get("canonical_repo")
    if not manifest_repo or not GITHUB_REPO_RE.match(manifest_repo):
        fail(f"{TARGET_WRAPPER_MANIFEST} must contain canonical_repo in OWNER/REPO format")
    if requested_repo and requested_repo != manifest_repo:
        fail(f"--repo {requested_repo} does not match wrapper canonical_repo {manifest_repo}")
    ok(f"wrapper manifest detected: canonical_repo={manifest_repo}")

    canonical_path = target_canonical_path(target)
    pointer = project_pointer_path(manifest_repo)
    if not pointer.exists() and not pointer.is_symlink():
        fail(f"project pointer is missing: {pointer}")
    if not pointer.is_symlink():
        fail(f"project pointer must be a symlink to the canonical repo: {pointer}")
    pointer_resolved = resolve_path(pointer)
    if pointer_resolved != canonical_path:
        fail(f"project pointer mismatch: {pointer} -> {pointer_resolved}; expected {canonical_path}")
    ok(f"project pointer resolves to canonical repo: {pointer} -> {pointer_resolved}")

    origin_repo = git_origin_repo(Path(canonical_path))
    if origin_repo:
        if origin_repo != manifest_repo:
            fail(f"canonical repo origin {origin_repo} does not match wrapper canonical_repo {manifest_repo}")
        ok(f"canonical repo origin matches wrapper manifest: {origin_repo}")
    else:
        fail("canonical independent Git repository has no GitHub origin")

    view = run_command(["gh", "repo", "view", manifest_repo, "--json", "nameWithOwner,url,visibility"])
    if view.returncode != 0:
        detail = (view.stderr or view.stdout or "").strip()
        fail(f"cannot access GitHub repo {manifest_repo}: {detail}")
    else:
        ok(f"GitHub repo accessible: {manifest_repo}")

    skill_name = skill_name_from_skill_md(target / "SKILL.md") or target.name
    manifest_install_paths = [
        Path(item).expanduser()
        for item in manifest.get("install_links", [])
        if isinstance(item, str) and item.strip()
    ]
    install_paths = manifest_install_paths or [
        Path.home() / ".codex" / "skills" / skill_name,
        Path.home() / ".agents" / "skills" / skill_name,
    ]
    install_paths = list(dict.fromkeys(install_paths))
    found_install = False
    for install_path in install_paths:
        if not install_path.exists() and not install_path.is_symlink():
            continue
        found_install = True
        kind = path_kind(install_path)
        resolved = resolve_path(install_path)
        pointer_scope = runtime_pointer_scope(Path(canonical_path), resolved)
        if kind == "symlink" and pointer_scope == "canonical_repo":
            ok(f"runtime install points to canonical repo: {install_path} -> {resolved}")
        elif kind == "symlink" and pointer_scope == "canonical_subskill":
            ok(f"runtime install points to canonical sub-Skill: {install_path} -> {resolved}")
        elif kind == "symlink":
            fail(
                f"runtime install symlink mismatch: {install_path} -> {resolved}; "
                f"expected {canonical_path} or a direct canonical skills/<name> entry"
            )
        elif kind == "directory":
            warn(f"runtime install is a real directory copy, not a source of truth: {install_path}")
        else:
            warn(f"runtime install is not a usable pointer: {install_path} ({kind})")
    if not found_install:
        ok("no runtime install pointers found; canonical repo remains the only discovered source")


def check_structure(args: argparse.Namespace) -> None:
    check_maintainer(args)


def check_issue(args: argparse.Namespace) -> None:
    body = read_text(Path(args.file))
    check_terms(body, ISSUE_TERMS, "issue")
    if not has_real_content(body):
        fail("issue body looks empty or placeholder-only")
    ok("issue body satisfies feedback template concepts")


def find_design_doc(target: Path) -> Path:
    docs_dir = target / TARGET_DESIGNS_DIR
    candidates = [
        path
        for path in docs_dir.glob("*.md")
        if path.name.lower() != "readme.md" and "template" not in path.name.lower()
    ]
    if not candidates:
        fail(f"no design doc found under {TARGET_DESIGNS_DIR}/*.md")
    return sorted(candidates)[-1]


def changelog_has_unreleased_entry(changelog: str) -> bool:
    match = re.search(r"^## \[?Unreleased\]?.*?(?=^## |\Z)", changelog, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not match:
        return False
    section = match.group(0)
    lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip().startswith("-") and "none yet" not in line.lower()
    ]
    return bool(lines)


def check_design_doc(path: Path) -> None:
    text = read_text(path)
    check_terms(text, DESIGN_TERMS, f"design doc {path}")
    if not has_real_content(text):
        fail(f"design doc looks placeholder-only: {path}")
    ok(f"design doc has required concepts: {path}")


def check_pr(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    design_doc = Path(args.design_doc).resolve() if args.design_doc else find_design_doc(target)
    check_design_doc(design_doc)

    changelog = read_text(target / TARGET_CHANGELOG)
    if not changelog_has_unreleased_entry(changelog):
        fail(f"{TARGET_CHANGELOG} must contain a non-empty Unreleased entry for the PR")
    ok(f"{TARGET_CHANGELOG} has an Unreleased entry")

    if args.pr_body:
        body = read_text(Path(args.pr_body))
        if "design doc" not in normalize(body) and "设计" not in body:
            fail("PR body should reference the design doc")
        if TARGET_CHANGELOG not in body:
            fail(f"PR body should confirm {TARGET_CHANGELOG} was updated")
        ok("PR body references design doc and changelog")


def changelog_has_tag(changelog: str, tag: str) -> bool:
    escaped = re.escape(tag)
    return bool(re.search(rf"^##\s+\[?{escaped}\]?\b", changelog, re.MULTILINE))


def latest_changelog_tag(changelog: str) -> str | None:
    for match in re.finditer(r"^##\s+\[?(v\d+\.\d+\.\d+)\]?\b", changelog, re.MULTILINE):
        return match.group(1)
    return None


CHANNEL_LABELS = {
    "development": "开发版",
    "uat": "UAT",
    "stable": "正式版",
}


def classify_runtime_channel(
    *,
    branch: str,
    clean: bool,
    head: str | None,
    skill_release: str | None,
    latest_release_tag: str | None,
    latest_release_commit: str | None,
    declared_channel: str | None = None,
) -> str:
    if not clean:
        return "development"
    if declared_channel == "uat" or branch.startswith("uat/"):
        return "uat"
    if (
        branch in {"", "main", "master"}
        and head
        and skill_release
        and latest_release_tag == skill_release
        and latest_release_commit == head
    ):
        return "stable"
    return "development"


def latest_release_for_identity(repo: str) -> dict[str, object]:
    result = run_command(["gh", "release", "view", "--repo", repo, "--json", "tagName,url,publishedAt"])
    if result.returncode != 0:
        return {
            "available": False,
            "tag": None,
            "url": None,
            "error": (result.stderr or result.stdout).strip() or "latest release unavailable",
        }
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"available": False, "tag": None, "url": None, "error": "invalid release response"}
    tag = data.get("tagName")
    if not isinstance(tag, str) or not tag:
        return {"available": False, "tag": None, "url": data.get("url"), "error": "release tag missing"}
    return {"available": True, "tag": tag, "url": data.get("url"), "error": None}


def collect_runtime_git_facts(target: Path, release_tag: str | None) -> dict[str, object]:
    def output(args: list[str]) -> str | None:
        result = run_command(["git", "-C", str(target), *args])
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    status = output(["status", "--porcelain"])
    return {
        "branch": output(["branch", "--show-current"]) or "",
        "clean": status == "" if status is not None else False,
        "head": output(["rev-parse", "HEAD"]),
        "release_commit": output(["rev-list", "-n", "1", release_tag]) if release_tag else None,
        "origin_repo": git_origin_repo(target),
    }


def runtime_channel_reason(
    *,
    channel: str,
    branch: str,
    clean: bool,
    skill_release: str | None,
    latest_release_tag: str | None,
    head: str | None,
    latest_release_commit: str | None,
) -> str:
    if not clean:
        return "dirty_worktree"
    if channel == "uat":
        return "declared_uat_channel"
    if channel == "stable":
        return "exact_release_commit"
    if not skill_release:
        return "skill_unpublished"
    if not latest_release_tag:
        return "release_unverified"
    if branch not in {"", "main", "master"}:
        return "development_branch"
    if not head or not latest_release_commit or head != latest_release_commit:
        return "head_not_release_commit"
    return "development_fallback"


def build_runtime_identity(
    target: Path,
    *,
    latest_release: dict[str, object] | None = None,
    git_facts: dict[str, object] | None = None,
) -> dict[str, object]:
    target = target.expanduser().resolve()
    manifest = load_wrapper_manifest(target)
    if not manifest:
        fail(f"missing wrapper manifest: {TARGET_WRAPPER_MANIFEST}")

    canonical_repo = manifest.get("canonical_repo")
    if not isinstance(canonical_repo, str) or not GITHUB_REPO_RE.fullmatch(canonical_repo):
        fail(f"{TARGET_WRAPPER_MANIFEST} must contain canonical_repo in OWNER/REPO format")
    harness_version = manifest.get("wrapper_version")
    if not isinstance(harness_version, str) or not VERSION_RE.fullmatch(harness_version):
        fail(f"{TARGET_WRAPPER_MANIFEST} must contain wrapper_version in vMAJOR.MINOR.PATCH format")

    changelog_path = target / TARGET_CHANGELOG
    skill_release = (
        latest_changelog_tag(changelog_path.read_text(encoding="utf-8"))
        if changelog_path.is_file()
        else None
    )
    release = latest_release if latest_release is not None else latest_release_for_identity(canonical_repo)
    latest_release_tag = release.get("tag") if release.get("available") else None
    if not isinstance(latest_release_tag, str):
        latest_release_tag = None
    facts = git_facts if git_facts is not None else collect_runtime_git_facts(target, latest_release_tag)
    origin_repo = facts.get("origin_repo")
    if origin_repo != canonical_repo:
        fail(f"canonical repo origin {origin_repo or 'missing'} does not match wrapper canonical_repo {canonical_repo}")

    branch = facts.get("branch") if isinstance(facts.get("branch"), str) else ""
    clean = facts.get("clean") is True
    head = facts.get("head") if isinstance(facts.get("head"), str) else None
    release_commit = (
        facts.get("release_commit") if isinstance(facts.get("release_commit"), str) else None
    )
    declared_channel = manifest.get("runtime_channel")
    channel = classify_runtime_channel(
        branch=branch,
        clean=clean,
        head=head,
        skill_release=skill_release,
        latest_release_tag=latest_release_tag,
        latest_release_commit=release_commit,
        declared_channel=declared_channel if isinstance(declared_channel, str) else None,
    )
    channel_label = CHANNEL_LABELS[channel]
    skill_display = skill_release or "未发布"
    canonical_url = f"https://github.com/{canonical_repo}"
    notice_policy_path = target / TARGET_NOTICE_POLICY
    notice_policy = load_notice_policy(notice_policy_path if notice_policy_path.is_file() else None)
    identity_notice = render_notice(
        kind="skill",
        state="active",
        details=(
            f"[{canonical_repo}]({canonical_url}) · Skill {skill_display} · "
            f"Harness {harness_version} · `渠道：{channel_label}`"
        ),
        policy=notice_policy,
    )
    display_line = identity_notice["display_text"]
    return {
        "schema_version": "v1",
        "managed_by": "EvoZeus-CoEvolve",
        "icon": "🧙🏻‍♂️",
        "canonical_repo": canonical_repo,
        "canonical_url": canonical_url,
        "skill_release": skill_display,
        "harness_version": harness_version,
        "channel": channel,
        "channel_label": channel_label,
        "channel_reason": runtime_channel_reason(
            channel=channel,
            branch=branch,
            clean=clean,
            skill_release=skill_release,
            latest_release_tag=latest_release_tag,
            head=head,
            latest_release_commit=release_commit,
        ),
        "display_once_scope": "skill_invocation",
        "display_line": display_line,
        "notice": identity_notice,
    }


def release_body_from_gh(tag: str, repo: str | None) -> str | None:
    cmd = ["gh", "release", "view", tag, "--json", "body", "-q", ".body"]
    if repo:
        cmd.extend(["--repo", repo])
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout


def latest_release_from_gh(repo: str) -> dict[str, str]:
    cmd = ["gh", "release", "view", "--repo", repo, "--json", "tagName,url,publishedAt"]
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    except FileNotFoundError:
        fail("gh CLI is required to check the latest GitHub release")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        fail(f"could not read latest GitHub release for {repo}: {detail}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        fail(f"could not parse gh release output for {repo}")
    if not data.get("tagName"):
        fail(f"latest GitHub release for {repo} has no tagName")
    return data


def check_release(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    version_key(args.tag)
    changelog = read_text(target / TARGET_CHANGELOG)
    if not changelog_has_tag(changelog, args.tag):
        fail(f"{TARGET_CHANGELOG} must contain a release entry for {args.tag}")
    ok(f"{TARGET_CHANGELOG} contains {args.tag}")

    body = ""
    if args.release_notes:
        body = read_text(Path(args.release_notes))
    elif not args.skip_gh:
        body = release_body_from_gh(args.tag, args.repo) or ""

    if not has_real_content(body):
        fail("release description is missing, too short, or placeholder-only")
    ok("release description is present")


def check_version(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    changelog = read_text(target / TARGET_CHANGELOG)
    current_tag = args.current_tag or latest_changelog_tag(changelog)
    if not current_tag:
        fail(f"could not infer current version from {TARGET_CHANGELOG}; pass --current-tag vMAJOR.MINOR.PATCH")
    current_key = version_key(current_tag)

    latest = latest_release_from_gh(args.repo)
    latest_tag = latest["tagName"]
    latest_key = version_key(latest_tag)
    if latest_key > current_key:
        fail(f"newer Skill release available: {latest_tag} > local {current_tag}. Update before running.")
    if latest_key < current_key:
        if args.no_release_needed:
            ok(
                f"local changelog version {current_tag} is ahead of latest GitHub release {latest_tag}; "
                "--no-release-needed explicitly bypassed release creation"
            )
            return
        fail(
            f"local changelog version {current_tag} is ahead of latest GitHub release {latest_tag}. "
            "Create the GitHub release or rerun with --no-release-needed only for changes that do not affect the installable artifact."
        )
        return
    ok(f"local Skill version matches latest GitHub release: {current_tag}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight checks for an EvoZeus-CoEvolve Skill repo.")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check local git/gh dependencies and source repo access.")
    doctor.add_argument("--target", default=".", help="Target wrapped Skill repo path.")
    doctor.add_argument("--repo", help="GitHub repo in OWNER/REPO format. Defaults to origin remote or discovered candidate.")
    doctor.add_argument("--allow-missing-repo", action="store_true", help=argparse.SUPPRESS)

    runtime = sub.add_parser("runtime", help="Check runtime-copy runnable Skill files.")
    runtime.add_argument("--target", default=".", help="Target Skill runtime or wrapped repo path.")

    maintainer = sub.add_parser("maintainer", help="Check maintainer wrapper governance files.")
    maintainer.add_argument("--target", default=".", help="Target wrapped Skill repo path.")

    structure = sub.add_parser("structure", help="Check required wrapper files.")
    structure.add_argument("--target", default=".", help="Target wrapped Skill repo path.")

    issue = sub.add_parser("issue", help="Check a Skill feedback issue body.")
    issue.add_argument("--target", default=".", help="Target wrapped Skill repo path.")
    issue.add_argument("--file", required=True, help="Markdown file containing the issue body.")

    pr = sub.add_parser("pr", help="Check Skill evolution PR readiness.")
    pr.add_argument("--target", default=".", help="Target wrapped Skill repo path.")
    pr.add_argument("--design-doc", help="Path to the design doc for this PR.")
    pr.add_argument("--pr-body", help="Optional PR body markdown file.")

    release = sub.add_parser("release", help="Check release readiness.")
    release.add_argument("--target", default=".", help="Target wrapped Skill repo path.")
    release.add_argument("--tag", required=True, help="Release tag, such as v0.1.0.")
    release.add_argument("--release-notes", help="Markdown file containing release notes.")
    release.add_argument("--repo", help="GitHub repo in OWNER/REPO format for gh release lookup.")
    release.add_argument("--skip-gh", action="store_true", help="Do not call gh release view when release notes are omitted.")

    version = sub.add_parser("version", help="Check whether GitHub has a newer Skill release.")
    version.add_argument("--target", default=".", help="Target wrapped Skill repo path.")
    version.add_argument("--repo", required=True, help="GitHub repo in OWNER/REPO format.")
    version.add_argument(
        "--current-tag",
        help=f"Current local Skill version. Defaults to latest release tag in {TARGET_CHANGELOG}.",
    )
    version.add_argument(
        "--no-release-needed",
        action="store_true",
        help="Explicitly allow local changelog to be ahead when the change does not affect the installable artifact.",
    )

    identity = sub.add_parser("identity", help="Render the EvoZeus runtime identity for this Skill invocation.")
    identity.add_argument("--target", default=".", help="Target wrapped Skill repo path.")
    identity.add_argument("--json", action="store_true", help="Return the versioned runtime_identity JSON object.")

    args = parser.parse_args()
    if args.command == "doctor":
        check_doctor(args)
    elif args.command == "runtime":
        check_runtime(args)
    elif args.command == "maintainer":
        check_maintainer(args)
    elif args.command == "structure":
        check_structure(args)
    elif args.command == "issue":
        check_issue(args)
    elif args.command == "pr":
        check_pr(args)
    elif args.command == "release":
        check_release(args)
    elif args.command == "version":
        check_version(args)
    elif args.command == "identity":
        runtime_identity = build_runtime_identity(Path(args.target))
        if args.json:
            print(json.dumps({"runtime_identity": runtime_identity}, ensure_ascii=False))
        else:
            print(runtime_identity["display_line"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
