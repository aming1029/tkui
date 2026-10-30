import unittest

import tkui
from tkui.ai import EXAMPLE_SPEC


def errors(spec):
    issues, _ = tkui.validate(spec)
    return [item for item in issues if item.level == "error"]


class SpecTests(unittest.TestCase):
    def test_example_spec_is_valid(self):
        issues, actions = tkui.validate(EXAMPLE_SPEC)
        self.assertEqual([item for item in issues if item.level == "error"], [])
        self.assertEqual(actions, set())

    def test_unknown_type_has_suggestion(self):
        spec = {"version": 1, "body": {"type": "buton", "text": "x"}}
        issues = errors(spec)
        self.assertEqual(len(issues), 1)
        self.assertIn("button", issues[0].message)

    def test_duplicate_ids(self):
        spec = {"version": 1, "body": {"type": "column", "children": [
            {"type": "label", "id": "x", "text": "a"},
            {"type": "label", "id": "x", "text": "b"},
        ]}}
        messages = [item.message for item in errors(spec)]
        self.assertTrue(any("已在" in message for message in messages))

    def test_tab_outside_tabs(self):
        spec = {"version": 1, "body": {"type": "tab", "title": "x"}}
        self.assertTrue(any("tabs" in item.message for item in errors(spec)))

    def test_tabs_need_tabs(self):
        spec = {"version": 1, "body": {"type": "tabs", "children": []}}
        self.assertTrue(errors(spec))

    def test_children_on_leaf(self):
        spec = {"version": 1, "body": {"type": "label", "text": "x",
                                       "children": [{"type": "label", "text": "y"}]}}
        self.assertTrue(any("不是容器" in item.message for item in errors(spec)))

    def test_missing_body_or_pages(self):
        self.assertTrue(errors({"version": 1}))

    def test_chart_needs_data(self):
        spec = {"version": 1, "body": {"type": "chart", "kind": "line"}}
        self.assertTrue(errors(spec))
        spec = {"version": 1, "body": {"type": "chart", "kind": "pie",
                                       "values": [1, 2]}}
        self.assertTrue(errors(spec))

    def test_nav_selected_must_exist(self):
        spec = {"version": 1, "pages": {"a": {"title": "A"}},
                "nav": {"items": [{"key": "a", "label": "A"}], "selected": "b"}}
        self.assertTrue(any("selected" in item.path for item in errors(spec)))

    def test_action_names_collected(self):
        spec = {"version": 1, "body": {"type": "button", "text": "x",
                                       "command": "save"}}
        _, actions = tkui.validate(spec)
        self.assertEqual(actions, {"save"})

    def test_unknown_field_is_warning(self):
        spec = {"version": 1, "body": {"type": "label", "text": "x", "colour": "red"}}
        issues, _ = tkui.validate(spec)
        self.assertFalse([item for item in issues if item.level == "error"])
        self.assertTrue([item for item in issues if item.level == "warning"])

    def test_layout_validation(self):
        spec = {"version": 1, "body": {"type": "label", "text": "x",
                                       "layout": {"fill": "diagonal"}}}
        self.assertTrue(any("fill" in item.path for item in errors(spec)))

    def test_page_shorthand_is_normalized(self):
        spec = {"version": 1, "pages": {"home": {"title": "Home",
                                                 "children": [{"type": "label",
                                                               "text": "x"}]}}}
        node = tkui.page_node("home", spec["pages"]["home"])
        self.assertEqual(node["type"], "page")
        self.assertEqual(node["title"], "Home")

    def test_spec_error_message_is_readable(self):
        with self.assertRaises(tkui.SpecError) as ctx:
            tkui.check({"version": 1, "body": {"type": "nope"}})
        self.assertIn("$.body.type", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
