import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "tkinter-ui"
SCRIPTS = SKILL / "scripts"


def run(script, *args):
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                          cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", timeout=120)


class SkillTests(unittest.TestCase):
    def test_skill_layout(self):
        self.assertTrue((SKILL / "SKILL.md").is_file())
        for name in ("research.md", "tkwebui.md", "tkwin11.md",
                     "components.md", "spec.md", "declarative.md"):
            self.assertTrue((SKILL / "references" / name).is_file(), name)
        for name in ("use_tkui.py", "scaffold.py", "check.py", "choose_style.py",
                     "selftest.py", "sync_runtime.py"):
            self.assertTrue((SCRIPTS / name).is_file(), name)
        self.assertTrue((SKILL / "runtime" / "tkui" / "__init__.py").is_file())

    def test_frontmatter_and_size(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        front, body = text.split("---", 2)[1:]
        self.assertIn("name: tkinter-ui", front)
        self.assertIn("description: Use when", front)
        self.assertLess(len(front), 1024)
        self.assertLess(len(body.splitlines()), 500)

    def test_runtime_is_in_sync(self):
        pairs = [
            (ROOT / "tkui", SKILL / "runtime" / "tkui"),
            (ROOT / "tkwebui-main" / "tkwebui",
             SKILL / "runtime" / "vendor" / "tkwebui"),
            (ROOT / "tkwin11-main" / "tkwin11",
             SKILL / "runtime" / "vendor" / "tkwin11"),
        ]
        for source, target in pairs:
            self.assertTrue((target / "LICENSE").is_file(), target)
            for path in source.glob("*.py"):
                mirror = target / path.name
                self.assertTrue(mirror.is_file(), path.name)
                self.assertEqual(path.read_text(encoding="utf-8"),
                                 mirror.read_text(encoding="utf-8"), path.name)

    def test_examples_validate(self):
        import tkui
        for path in (SKILL / "assets" / "examples").glob("*.json"):
            spec = json.loads(path.read_text(encoding="utf-8"))
            issues, _ = tkui.validate(spec)
            self.assertEqual([item for item in issues if item.level == "error"], [],
                             path.name)

    def test_machine_readable_assets_match_runtime(self):
        import tkui
        catalog = json.loads((SKILL / "assets" / "catalog.json").read_text(encoding="utf-8"))
        schema = json.loads((SKILL / "assets" / "tkui-1.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog, tkui.catalog())
        self.assertEqual(schema, tkui.json_schema())

    def test_scaffold_both_styles(self):
        with tempfile.TemporaryDirectory() as tmp:
            for style in ("web", "win11"):
                out = Path(tmp) / f"{style}.py"
                proc = run("scaffold.py", "--style", style, "--kind", "dashboard",
                           "--output", str(out))
                self.assertEqual(proc.returncode, 0, proc.stderr)
                compile(out.read_text(encoding="utf-8"), str(out), "exec")
                check = run("check.py", str(out))
                self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_check_detects_mixed_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.py"
            path.write_text("import tkwebui\nimport tkwin11\n", encoding="utf-8")
            proc = run("check.py", str(path))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("不能同时导入", proc.stdout)

    def test_use_tkui_check(self):
        proc = run("use_tkui.py", "check",
                   str(SKILL / "assets" / "examples" / "dashboard.json"), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["ok"])

    def test_selftest_without_display(self):
        proc = run("selftest.py")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("SELFTEST OK", proc.stdout)

    def test_standalone_copy_is_portable(self):
        """A copied skill folder must work without the repo or env overrides."""
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "tkinter-ui"
            shutil.copytree(
                SKILL, dst,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith("TKUI_") and key != "PYTHONPATH"}
            proc = subprocess.run(
                [sys.executable, str(dst / "scripts" / "selftest.py"), "--render"],
                cwd=tmp, env=env, capture_output=True, text=True,
                encoding="utf-8", timeout=180,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("SELFTEST OK", proc.stdout)

            for style in ("web", "win11"):
                out = Path(tmp) / f"standalone_{style}.py"
                proc = subprocess.run(
                    [sys.executable, str(dst / "scripts" / "scaffold.py"),
                     "--style", style, "--kind", "blank", "--output", str(out)],
                    cwd=tmp, env=env, capture_output=True, text=True,
                    encoding="utf-8", timeout=60,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                code = (
                    "import tkinter as tk, runpy\n"
                    "tk.Tk.mainloop=lambda self:(self.update_idletasks(),self.destroy())\n"
                    f"runpy.run_path({str(out)!r}, run_name='__main__')\n"
                )
                proc = subprocess.run(
                    [sys.executable, "-c", code], cwd=tmp, env=env,
                    capture_output=True, text=True, encoding="utf-8", timeout=60,
                )
                self.assertEqual(proc.returncode, 0,
                                 f"{style}\n{proc.stdout}\n{proc.stderr}")


if __name__ == "__main__":
    unittest.main()
