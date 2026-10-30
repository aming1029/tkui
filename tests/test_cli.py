import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*args):
    return subprocess.run([sys.executable, "-m", "tkui", *args], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", timeout=120)


class CliTests(unittest.TestCase):
    def test_catalog_json(self):
        proc = run("catalog")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIn("components", data)
        self.assertGreater(len(data["components"]), 30)

    def test_schema(self):
        proc = run("schema")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        schema = json.loads(proc.stdout)
        self.assertIn("$defs", schema)

    def test_prompt(self):
        proc = run("prompt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("TkUI", proc.stdout)
        self.assertIn("工作流", proc.stdout)

    def test_check_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.json"
            good.write_text(json.dumps({"version": 1, "body": {
                "type": "button", "text": "ok"}}), encoding="utf-8")
            proc = run("check", str(good))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("规格有效", proc.stdout)

            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"version": 1, "body": {"type": "nope"}}),
                           encoding="utf-8")
            proc = run("check", str(bad))
            self.assertEqual(proc.returncode, 1)

    def test_styles(self):
        proc = run("styles")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("win11", proc.stdout)

    def test_info(self):
        proc = run("info")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(set(data["loaded"]), {"web", "win11"})


if __name__ == "__main__":
    unittest.main()
