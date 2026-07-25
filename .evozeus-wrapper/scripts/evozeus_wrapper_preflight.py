#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


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

REQUIRED_FILES = [
    TARGET_CHANGELOG,
    TARGET_WRAPPER_GUIDE,
    TARGET_WRAPPER_MANIFEST,
    TARGET_FEEDBACK_POLICY,
    TARGET_AUDIT_RULE,
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

SKILL_EVOLUTION_TERMS = [
    ["EvoZeus-CoEvolve 状态检查", "EvoZeus-wrapper 状态检查"],
    ["当前记录版本", "当前 Skill 版本", "Skill release"],
    ["解决顺序", "处理顺序", "解决方法"],
    ["自进化"],
    ["EvoZeus-CoEvolve", "EvoZeus-wrapper"],
    [TARGET_WRAPPER_MANIFEST],
    ["runtime-only install"],
    ["source discovery", "源头发现", "source of truth", "事实源"],
    ["~/.evozeus/.projects"],
    ["version --repo"],
    ["Skill Feedback Issue", "feedback issue"],
    [TARGET_DESIGNS_DIR, "design doc"],
    [TARGET_MIGRATIONS_DIR, "wrapper migration"],
    ["append-only", "追加"],
    ["wrapper harness version"],
    [TARGET_CHANGELOG],
    ["release tag", "release notes"],
]

PLACEHOLDER_PATTERNS = [
    r"\{\{[A-Z_]+\}\}",
    r"<short title>",
    r"<path>",
    r"<design-doc>",
    r"\bTBD\b",
    r"待填写",
]

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


def check_integration_contract(target: Path, manifest: dict | None) -> None:
    integration = (manifest or {}).get("integration") or {}
    registration = ((manifest or {}).get("hook_registration") or {}).get("codex") or {}
    mode = integration.get("mode")
    capabilities = integration.get("capabilities") or {}
    repo_hook = capabilities.get("repo_maintenance_hook") or {}
    global_dispatcher = capabilities.get("global_session_dispatcher") or {}
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
            fail("skill_entry_preflight installation requires the status prelude")
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
        if children.get("attachment") != "separate_wrapper_lifecycle":
            fail("generated child Skills must use a separate_wrapper_lifecycle attachment")
        if children.get("trust_review") != "/hooks":
            fail("generated child Skill hooks must require /hooks trust review")
        verification = children.get("verification") or ""
        required_terms = ["structure preflight", "consumer-project smoke test"]
        if not all(term in verification for term in required_terms):
            fail("generated child Skill verification must include structure preflight and consumer-project smoke test")
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


def content_after_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + len("\n---\n") :]


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
        if relative.is_absolute() or ".." in relative.parts:
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


def discover_runtime_bundle(target: Path) -> dict:
    manifest = load_wrapper_manifest(target)
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
    entry = target / bundle["instruction_surface"]
    check_runtime_safe_status_prelude(read_text(entry), bundle["instruction_surface"])
    ok("runtime bundle is complete")


def check_maintainer(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    missing = [path for path in MAINTAINER_REQUIRED_FILES if not (target / path).exists()]
    if missing:
        fail("missing required maintainer wrapper files:\n" + "\n".join(f"- {path}" for path in missing))
    manifest = load_wrapper_manifest(target)
    check_onboarding_contract(manifest)
    check_dashboard_contract(manifest)
    check_integration_contract(target, manifest)
    entry = root_entry_path(target)
    entry_text = read_text(entry)
    label = str(entry.relative_to(target))
    check_terms(entry_text, SKILL_EVOLUTION_TERMS, f"{label} self-evolution method")
    if label == "AGENTS.md":
        check_agents_status_prelude(entry_text)
    else:
        check_status_prelude(entry_text, label)
    check_runtime(args)
    ok("maintainer bundle contains required wrapper files")


def check_doctor(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    require_command("git")
    require_command("gh")

    auth = run_command(["gh", "auth", "status"])
    if auth.returncode != 0:
        fail("gh is installed but not authenticated; run gh auth login")
    ok("gh authenticated")

    repo = args.repo
    if repo and not GITHUB_REPO_RE.match(repo):
        fail(f"--repo must use OWNER/REPO format: {repo}")

    manifest = load_wrapper_manifest(target)
    if manifest:
        check_wrapper_managed_doctor(target, repo, manifest, args.allow_missing_repo)
        return

    git_root_result = run_command(["git", "-C", str(target), "rev-parse", "--show-toplevel"])
    if git_root_result.returncode == 0:
        git_root = Path(git_root_result.stdout.strip())
        remote_result = run_command(["git", "-C", str(git_root), "remote", "get-url", "origin"])
        if remote_result.returncode == 0:
            remote_repo = repo_from_remote(remote_result.stdout)
            if remote_repo:
                repo = repo or remote_repo
                ok(f"origin GitHub repo detected: {remote_repo}")
            else:
                fail(f"origin remote is not a GitHub repo: {remote_result.stdout.strip()}")
        elif not repo:
            fail("target is a git repo but origin remote is missing; pass --repo OWNER/REPO")
    elif not repo:
        candidates = discover_repo_candidates(target.name)
        if candidates:
            repo = candidates[0]
            ok(f"target is not a git repo; discovered candidate repo: {repo}")
        else:
            fail("target is not a git repo and no --repo was provided")

    if repo:
        view = run_command(["gh", "repo", "view", repo, "--json", "nameWithOwner,url,visibility"])
        if view.returncode != 0:
            detail = (view.stderr or view.stdout or "").strip()
            if args.allow_missing_repo and is_repo_not_found(detail):
                ok(f"GitHub repo is available to create: {repo}")
                return
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
    elif allow_missing_repo:
        warn("canonical repo has no GitHub origin yet; allowed only during pre-publish bootstrap")
    else:
        fail("canonical repo has no GitHub origin; publish or pass --allow-missing-repo only during bootstrap")

    view = run_command(["gh", "repo", "view", manifest_repo, "--json", "nameWithOwner,url,visibility"])
    if view.returncode != 0:
        detail = (view.stderr or view.stdout or "").strip()
        if allow_missing_repo and is_repo_not_found(detail):
            ok(f"GitHub repo is available to create: {manifest_repo}")
        else:
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
    doctor.add_argument("--allow-missing-repo", action="store_true", help="Allow --repo to be absent on GitHub when bootstrapping a new repo.")

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
