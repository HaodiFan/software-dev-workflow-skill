from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_install_module():
    spec = importlib.util.spec_from_file_location("install", ROOT / "scripts/install.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.install = load_install_module()

    def test_safe_remove_unlinks_symlink_to_canonical_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            canonical = Path(temp) / "source"
            canonical.mkdir()
            (canonical / "SKILL.md").write_text("source", encoding="utf-8")
            dest = Path(temp) / "dest"
            dest.symlink_to(canonical, target_is_directory=True)

            message = self.install.safe_remove(dest, canonical, dry_run=False)

            self.assertIn("unlinked symlink", message)
            self.assertFalse(dest.exists())
            self.assertTrue((canonical / "SKILL.md").exists())

    def test_safe_remove_refuses_non_symlink_inside_canonical_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            canonical = Path(temp) / "source"
            child = canonical / "child"
            child.mkdir(parents=True)

            with self.assertRaises(RuntimeError):
                self.install.safe_remove(child, canonical, dry_run=False)

            self.assertTrue(child.exists())

    def test_discover_skill_packages_includes_bootloader(self) -> None:
        names = {path.name for path in self.install.discover_skill_packages(ROOT)}

        self.assertIn("using-engineering-everything", names)
        self.assertIn("engineering-everything", names)

    def test_install_library_creates_canonical_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            skill = source / "skills" / "example-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("example", encoding="utf-8")
            destination = Path(temp) / "runtime-skills"

            messages = self.install.install_library(
                source,
                destination,
                delete=True,
                dry_run=False,
            )

            installed = destination / "example-skill"
            self.assertTrue(installed.is_symlink())
            self.assertEqual(installed.resolve(), skill.resolve())
            self.assertIn("linked", messages[0])


if __name__ == "__main__":
    unittest.main()
