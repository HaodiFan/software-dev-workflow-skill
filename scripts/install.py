#!/usr/bin/env python3
"""Install, update, link, list, or uninstall Engineering Everything skills."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


SKILL_NAME = "engineering-everything"
USING_SKILL_NAME = "using-engineering-everything"


def package_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def default_skill_roots(target: str) -> list[Path]:
    home = Path.home()
    destinations: list[Path] = []
    if target in {"codex", "both"}:
        destinations.append(home / ".codex/skills")
    if target in {"agents", "both"}:
        destinations.append(home / ".agents/skills")
    return destinations


def default_legacy_destinations(target: str) -> list[Path]:
    return [root / SKILL_NAME for root in default_skill_roots(target)]


def discover_skill_packages(source: Path) -> list[Path]:
    skills_dir = source / "skills"
    if not skills_dir.exists():
        return [source]
    packages = [path for path in sorted(skills_dir.iterdir()) if (path / "SKILL.md").exists()]
    return packages or [source]


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def safe_remove(dest: Path, canonical_root: Path, dry_run: bool) -> str:
    dest = dest.expanduser()
    if not dest.exists() and not dest.is_symlink():
        return f"skip {dest} (missing)"

    resolved = dest.resolve()
    canonical_root = canonical_root.resolve()
    if resolved == canonical_root or is_relative_to(resolved, canonical_root):
        if dest.is_symlink():
            if dry_run:
                return f"would unlink symlink {dest} -> {resolved}"
            dest.unlink()
            return f"unlinked symlink {dest}"
        raise RuntimeError(f"refusing to delete canonical repo path via install destination: {dest} -> {resolved}")

    if dry_run:
        return f"would remove {dest}"
    if dest.is_dir() and not dest.is_symlink():
        shutil.rmtree(dest)
    else:
        dest.unlink()
    return f"removed {dest}"


def copy_tree(source: Path, dest: Path, delete: bool, dry_run: bool) -> str:
    source = source.resolve()
    dest = dest.expanduser()
    canonical_root = package_dir().resolve()
    if dest.exists() or dest.is_symlink():
        resolved_dest = dest.resolve()
    else:
        resolved_dest = dest
    if source == resolved_dest:
        return f"skip {dest} (source and destination are the same)"
    if dry_run:
        action = "replace" if (dest.exists() or dest.is_symlink()) and delete else "copy"
        return f"would {action} {source} -> {dest}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if (dest.exists() or dest.is_symlink()) and delete:
        safe_remove(dest, canonical_root, dry_run=False)
    shutil.copytree(
        source,
        dest,
        dirs_exist_ok=not delete,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store"),
    )
    return f"installed {dest}"


def link_tree(source: Path, dest: Path, delete: bool, dry_run: bool) -> str:
    source = source.resolve()
    dest = dest.expanduser()
    if dest.exists() or dest.is_symlink():
        if dest.resolve() == source:
            return f"skip {dest} (already links to {source})"
        if not delete:
            return f"skip {dest} (already exists)"
        if dry_run:
            return f"would replace {dest} with symlink -> {source}"
        safe_remove(dest, package_dir(), dry_run=False)
    if dry_run:
        return f"would symlink {dest} -> {source}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(source, dest, target_is_directory=True)
    return f"linked {dest} -> {source}"


def install_library(source: Path, dest_root: Path, delete: bool, dry_run: bool) -> list[str]:
    results: list[str] = []
    for skill_package in discover_skill_packages(source):
        results.append(link_tree(skill_package, dest_root / skill_package.name, delete, dry_run))
    return results


def link_library(source: Path, dest_root: Path, delete: bool, dry_run: bool) -> list[str]:
    results: list[str] = []
    for skill_package in discover_skill_packages(source):
        results.append(link_tree(skill_package, dest_root / skill_package.name, delete, dry_run))
    return results


def uninstall_library(source: Path, dest_root: Path, dry_run: bool) -> list[str]:
    results: list[str] = []
    for skill_package in discover_skill_packages(source):
        results.append(safe_remove(dest_root / skill_package.name, source, dry_run))
    return results


def list_library(source: Path, dest_root: Path) -> list[str]:
    results: list[str] = []
    for skill_package in discover_skill_packages(source):
        dest = dest_root / skill_package.name
        status = "missing"
        if dest.is_symlink():
            status = f"symlink -> {dest.resolve()}"
        elif dest.exists():
            status = "copy"
        results.append(f"{skill_package.name}: {dest} ({status})")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Engineering Everything.")
    parser.add_argument(
        "action",
        nargs="?",
        choices=["install", "update", "relink", "uninstall", "list"],
        default="install",
        help="Lifecycle action. install, update, and relink maintain canonical symlink pointers.",
    )
    parser.add_argument(
        "--target",
        choices=["codex", "agents", "both"],
        default="both",
        help="Destination skill directory group.",
    )
    parser.add_argument(
        "--layout",
        choices=["library", "legacy"],
        default="library",
        help="Install skills/* as separate skills, or install the whole repo as the legacy single skill.",
    )
    parser.add_argument(
        "--dest",
        action="append",
        type=Path,
        help="Explicit destination. In library layout this is a skills root; in legacy layout this is the package destination.",
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Do not delete the existing destination before copying.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changing files.")
    args = parser.parse_args()

    source = package_dir()
    destinations = args.dest or (
        default_skill_roots(args.target)
        if args.layout == "library"
        else default_legacy_destinations(args.target)
    )
    if not destinations:
        print("install: no destinations selected", file=sys.stderr)
        return 1
    if args.layout == "legacy" and not (source / "SKILL.md").exists():
        print("install: legacy layout is retired; use the default library layout", file=sys.stderr)
        return 1
    try:
        for dest in destinations:
            if args.layout == "library":
                if args.action in {"install", "update"}:
                    results = install_library(source, dest, delete=not args.no_delete, dry_run=args.dry_run)
                elif args.action == "relink":
                    results = link_library(source, dest, delete=not args.no_delete, dry_run=args.dry_run)
                elif args.action == "uninstall":
                    results = uninstall_library(source, dest, dry_run=args.dry_run)
                else:
                    results = list_library(source, dest)
                for result in results:
                    print(result)
            else:
                if args.action in {"install", "update"}:
                    print(copy_tree(source, dest, delete=not args.no_delete, dry_run=args.dry_run))
                elif args.action == "relink":
                    print(link_tree(source, dest, delete=not args.no_delete, dry_run=args.dry_run))
                elif args.action == "uninstall":
                    print(safe_remove(dest, source, dry_run=args.dry_run))
                else:
                    print(f"{SKILL_NAME}: {dest} ({'present' if dest.exists() or dest.is_symlink() else 'missing'})")
    except RuntimeError as exc:
        print(f"install: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
