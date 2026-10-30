import unittest
from unittest import mock

from tkui.actions import Event, call_user, run_action


class FakeApp:
    def __init__(self):
        self.values = {"name": "old", "auto": False}
        self.notified = []
        self.navigated = []
        self.dialogs = []
        self.styles = []
        self.closed = False
        self.actions = {}

    def notify(self, message, **kwargs):
        self.notified.append((message, kwargs))

    def navigate(self, page):
        self.navigated.append(page)

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def dialog(self, message, **kwargs):
        self.dialogs.append((message, kwargs))

    def restart_in_style(self, style):
        self.styles.append(style)

    def close(self):
        self.closed = True


class ActionTests(unittest.TestCase):
    def test_call_user_zero_or_one_argument(self):
        calls = []
        call_user(None, lambda: calls.append("zero"), Event("click"))
        call_user(None, lambda event: calls.append(event.name), Event("click"))
        self.assertEqual(calls, ["zero", "click"])

    def test_named_action(self):
        app = FakeApp()
        seen = []
        app.actions["save"] = lambda event: seen.append(event.value)
        run_action(app, "save", Event("click", value=7))
        self.assertEqual(seen, [7])

    def test_builtin_notify_and_navigate(self):
        app = FakeApp()
        run_action(app, {"action": "notify", "message": "hi", "kind": "success"},
                   Event("click"))
        run_action(app, {"navigate": "settings"}, Event("click"))
        self.assertEqual(app.notified[0][0], "hi")
        self.assertEqual(app.notified[0][1]["kind"], "success")
        self.assertEqual(app.navigated, ["settings"])

    def test_builtin_set_toggle_chain(self):
        app = FakeApp()
        run_action(app, [{"action": "set", "target": "name", "value": "new"},
                         {"action": "toggle", "target": "auto"}], Event("click"))
        self.assertEqual(app.values["name"], "new")
        self.assertTrue(app.values["auto"])

    def test_style_value_placeholder(self):
        app = FakeApp()
        run_action(app, {"action": "style", "style": "$value"},
                   Event("change", value="win11"))
        self.assertEqual(app.styles, ["win11"])

    def test_dialog_and_quit(self):
        app = FakeApp()
        run_action(app, {"action": "dialog", "message": "x", "title": "t"},
                   Event("click"))
        run_action(app, {"action": "quit"}, Event("click"))
        self.assertEqual(app.dialogs[0][0], "x")
        self.assertTrue(app.closed)

    def test_missing_action_raises(self):
        app = FakeApp()
        with self.assertRaises(Exception):
            run_action(app, "missing", Event("click"))


if __name__ == "__main__":
    unittest.main()
