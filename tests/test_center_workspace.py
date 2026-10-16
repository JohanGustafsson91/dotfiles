import importlib.util
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "center_workspace", Path(__file__).resolve().parents[1] / "scripts/center-workspace.py"
)
center = importlib.util.module_from_spec(spec)
spec.loader.exec_module(center)


def output(name, x, active=True):
    return {"name": name, "active": active,
            "rect": {"x": x, "y": 0, "width": 1920, "height": 1080}}


class CenterWorkspaceTests(unittest.TestCase):
    def test_three_screens_use_position_even_when_connector_names_change(self):
        for middle in ("HDMI-1", "DP-3-8"):
            outputs = [output("DP-right", 3840), output("eDP-1", 0), output(middle, 1920),
                       output("disabled", 0, False)]
            self.assertEqual(center.choose_output(outputs, "eDP-1"), middle)

    def test_two_screens_prefer_external_on_either_side(self):
        for laptop_x, external_x in ((0, 1920), (1920, 0)):
            outputs = [output("eDP-1", laptop_x), output("DP-1", external_x)]
            self.assertEqual(center.choose_output(outputs, "eDP-1"), "DP-1")

    def test_one_screen_and_two_external_screens(self):
        self.assertEqual(center.choose_output([output("eDP-1", 0)], "eDP-1"), "eDP-1")
        self.assertEqual(center.choose_output([output("DP-1", 0), output("HDMI-1", 1920)],
                                              "HDMI-1"), "HDMI-1")

    def test_workspace_icons_are_sent_as_unicode_to_i3(self):
        with patch.object(center, "i3") as command:
            center.focus_workspace("1: ")
        command.assert_called_once_with("command", 'workspace --no-auto-back-and-forth "1: "')

    def test_workspace_is_focused_again_after_moving_to_another_output(self):
        with patch.object(center, "i3") as command:
            center.move_workspace({"name": "1: "}, "HDMI-1")
        command.assert_called_once_with("command", (
            'workspace --no-auto-back-and-forth "1: "; '
            'move workspace to output "HDMI-1"; '
            'workspace --no-auto-back-and-forth "1: "'
        ))

    def setUp(self):
        self.outputs = [output("eDP-1", 0), output("HDMI-1", 1920), output("DP-1", 3840)]
        self.workspaces = [
            {"id": 101, "num": 1, "name": "1: browser", "output": "DP-1", "visible": True, "focused": False},
            {"id": 102, "num": 2, "name": "2: editor", "output": "HDMI-1", "visible": True, "focused": True},
            {"id": 103, "num": 3, "name": "3: chat", "output": "eDP-1", "visible": True, "focused": False},
        ]

    def query_i3(self, message_type, command=None):
        return self.outputs if message_type == "get_outputs" else self.workspaces

    def test_toggle_saves_origin_and_restores_previous_center_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            with patch.object(center, "i3", side_effect=self.query_i3), \
                    patch.object(center, "move_workspace") as move, \
                    patch.object(center, "focus_workspace") as focus:
                center.toggle_workspace(1, state_path)
                move.assert_called_once_with(self.workspaces[0], "HDMI-1")
                self.workspaces[0]["output"] = "HDMI-1"
                self.workspaces[1]["visible"] = False
                center.toggle_workspace(1, state_path)
                self.assertEqual(move.call_args.args[1], "DP-1")
                self.assertEqual([call.args[0] for call in focus.call_args_list],
                                 ["2: editor", "1: browser"])
                self.assertFalse(state_path.exists())

    def test_changing_layout_does_not_restore_to_old_output(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            with patch.object(center, "i3", side_effect=self.query_i3), \
                    patch.object(center, "move_workspace") as move, \
                    patch.object(center, "focus_workspace"):
                center.toggle_workspace(1, state_path)
                self.workspaces[0]["output"] = "HDMI-1"
                self.outputs[2]["active"] = False
                move.reset_mock()
                center.toggle_workspace(1, state_path)
                move.assert_not_called()
                self.assertFalse(state_path.exists())

    def test_missing_workspace_leaves_existing_loan_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            with patch.object(center, "i3", side_effect=self.query_i3), \
                    patch.object(center, "move_workspace") as move:
                center.toggle_workspace(1, state_path)
                saved = state_path.read_text()
                with self.assertRaisesRegex(RuntimeError, "inte öppen"):
                    center.toggle_workspace(10, state_path)
                self.assertEqual(state_path.read_text(), saved)
                self.assertEqual(move.call_count, 1)

    def test_selecting_other_workspace_restores_existing_loan_first(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            with patch.object(center, "i3", side_effect=self.query_i3), \
                    patch.object(center, "move_workspace") as move, \
                    patch.object(center, "focus_workspace"):
                center.toggle_workspace(1, state_path)
                self.workspaces[0]["output"] = "HDMI-1"
                center.toggle_workspace(3, state_path)
                self.assertEqual([call.args[1] for call in move.call_args_list],
                                 ["HDMI-1", "DP-1", "HDMI-1"])


if __name__ == "__main__":
    unittest.main()
