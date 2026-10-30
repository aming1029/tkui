import json
import unittest

import tkui
from tkui.catalog import COMPONENTS, canonical_type
from tkui.renderer import renderer_names


class CatalogTests(unittest.TestCase):
    def test_catalog_is_json_serializable(self):
        data = tkui.catalog()
        text = json.dumps(data, ensure_ascii=False)
        self.assertGreater(len(text), 1000)
        self.assertEqual(data["schema_version"], 1)

    def test_every_component_has_a_renderer(self):
        missing = set(COMPONENTS) - set(renderer_names())
        self.assertEqual(missing, {"tab"})  # tabs render their children directly

    def test_props_declare_kinds(self):
        valid = {"str", "int", "float", "bool", "list", "dict", "enum", "action"}
        for name, item in COMPONENTS.items():
            for prop, meta in item["props"].items():
                self.assertIn(meta["kind"], valid, f"{name}.{prop}")
                if meta["kind"] == "enum":
                    self.assertTrue(meta.get("values"), f"{name}.{prop}")

    def test_aliases_point_to_components(self):
        for alias in tkui.ALIASES:
            self.assertIn(canonical_type(alias), COMPONENTS)
            self.assertNotIn(alias, COMPONENTS)

    def test_schema_has_one_variant_per_component(self):
        schema = tkui.json_schema()
        self.assertEqual(len(schema["$defs"]["node"]["oneOf"]), len(COMPONENTS))
        json.dumps(schema)

    def test_markdown_catalog(self):
        text = tkui.to_markdown()
        for name in COMPONENTS:
            self.assertIn(f"`{name}`", text)


if __name__ == "__main__":
    unittest.main()
