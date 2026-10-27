import importlib.util
from pathlib import Path
import unittest
from unittest.mock import call, patch


spec = importlib.util.spec_from_file_location(
    "move_workspace", Path(__file__).resolve().parents[1] / "scripts/move-workspace.py"
)
workspace_mover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace_mover)


class MoveWorkspaceTests(unittest.TestCase):
    def test_pointer_and_focus_follow_original_container_even_if_focus_changes(self):
        original = {"id": 42, "focused": True}
        moved = {
            "id": 42, "focused": False,
            "rect": {"x": 2000, "y": 100, "width": 800, "height": 600},
        }
        other = {"id": 99, "focused": True}
        for children in ("nodes", "floating_nodes"):
            with self.subTest(children=children):
                before = {"id": 1, children: [original]}
                after = {"id": 1, children: [moved, other]}
                with patch.object(workspace_mover, "i3", side_effect=[
                    before, [{"success": True}], after, [{"success": True}],
                ]) as i3, patch.object(workspace_mover.subprocess, "run") as run:
                    workspace_mover.move_workspace("right")
                run.assert_called_once_with(
                    ["xdotool", "mousemove", "--sync", "2400", "400"], check=True,
                )
                self.assertEqual(i3.call_args_list, [
                    call("get_tree"),
                    call("command", "[con_id=42] move workspace to output right"),
                    call("get_tree"),
                    call("command", "[con_id=42] focus"),
                ])

    def test_empty_workspace_can_keep_focus_when_no_other_output_exists(self):
        workspace = {
            "id": 42, "type": "workspace", "focused": True,
            "rect": {"x": 0, "y": 30, "width": 1920, "height": 1050},
        }
        tree = {"id": 1, "nodes": [workspace]}
        with patch.object(workspace_mover, "i3", side_effect=[
            tree, [{"success": True}], tree, [{"success": True}],
        ]), patch.object(workspace_mover.subprocess, "run") as run:
            workspace_mover.move_workspace("up")
        run.assert_called_once_with(
            ["xdotool", "mousemove", "--sync", "960", "555"], check=True,
        )


if __name__ == "__main__":
    unittest.main()
