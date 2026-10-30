import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tkui import theme


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = Path(self.tmp.name) / "config.json"
        self.env = mock.patch.dict(os.environ, {theme.CONFIG_ENV: str(self.config)},
                                   clear=False)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_normalize_aliases(self):
        self.assertEqual(theme.normalize_style("fluent"), "win11")
        self.assertEqual(theme.normalize_style("TkWebUI"), "web")
        self.assertEqual(theme.normalize_style("windows-11"), "win11")
        self.assertIsNone(theme.normalize_style("auto"))
        with self.assertRaises(theme.StyleError):
            theme.normalize_style("purple")

    def test_precedence_explicit_env_config_default(self):
        theme.save_style("win11")
        with mock.patch.dict(os.environ, {theme.ENV_VAR: "web"}):
            self.assertEqual(theme.resolve_style("web"), "web")
            self.assertEqual(theme.resolve_style(None), "web")
        self.assertEqual(theme.resolve_style(None), "win11")
        theme.write_config({})
        self.assertEqual(theme.resolve_style(None), "web")

    def test_config_roundtrip(self):
        path = theme.save_style("win11")
        self.assertEqual(path, self.config)
        self.assertEqual(theme.saved_style(), "win11")
        self.assertIn("win11", self.config.read_text(encoding="utf-8"))

    def test_describe(self):
        info = theme.describe("web")
        self.assertEqual(info["key"], "web")
        self.assertIn("library", info)


if __name__ == "__main__":
    unittest.main()
