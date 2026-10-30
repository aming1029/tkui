import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class RenderTests(unittest.TestCase):
    def _run(self, style):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tests" / "_render_all.py"), style],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=120,
        )
        self.assertEqual(proc.returncode, 0,
                         f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        self.assertIn(f"OK {style}", proc.stdout)

    def test_render_web(self):
        self._run("web")

    def test_render_win11(self):
        self._run("win11")


if __name__ == "__main__":
    unittest.main()
