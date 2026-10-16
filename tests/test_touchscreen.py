import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import call, patch


spec = importlib.util.spec_from_file_location(
    "touchscreen", Path(__file__).resolve().parents[1] / "scripts/map-touchscreen.py"
)
touchscreen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(touchscreen)


def layout(output="HDMI-1", geometry="1920x1080+0+0", rotation="", identity=None):
    identity = identity or touchscreen.DISPLAY_ID
    return (
        "Screen 0: minimum 320 x 200, current 7680 x 2160, maximum 16384 x 16384\n"
        f"{output} connected {geometry} {rotation} (normal left inverted right x axis y axis)\n"
        f"\tEDID: \n\t\t{identity}\n"
    )


def properties(enabled=1, matrix="1, 0, 0, 0, 1, 0, 0, 0, 1"):
    return (
        f"Device Enabled (188): {enabled}\n"
        f"Coordinate Transformation Matrix (190): {matrix}\n"
    )


class TouchscreenTests(unittest.TestCase):
    def test_follows_display_identity_and_position_instead_of_connector(self):
        for output in ("HDMI-1", "DP-3-8", "DP-2"):
            with self.subTest(output=output):
                matrix = touchscreen.target_matrix(layout(output, "1920x1080+3840+1080"))
                self.assertEqual(matrix, [0.25, 0, 0.5, 0, 0.5, 0.5, 0, 0, 1])

    def test_matches_only_target_when_other_displays_are_present(self):
        data = layout(identity="00ffffffffffff0010acc7a142565033") + layout("DP-3-8")
        self.assertEqual(touchscreen.target_matrix(data), [0.25, 0, 0, 0, 0.5, 0, 0, 0, 1])

    def test_missing_disabled_or_ambiguous_display_has_no_mapping(self):
        for data in ("", layout(geometry=""), layout(identity="0" * 32), layout() + layout("DP-1")):
            with self.subTest(data=data):
                self.assertIsNone(touchscreen.target_matrix(data))

    def test_rotation_maps_corners_inside_display(self):
        expected_corners = {
            "": [(0.25, 0.5), (0.5, 0.5), (0.25, 1)],
            "left": [(0.5, 0.5), (0.5, 1), (0.25, 0.5)],
            "right": [(0.25, 1), (0.25, 0.5), (0.5, 1)],
            "inverted": [(0.5, 1), (0.25, 1), (0.5, 0.5)],
        }
        for rotation, expected in expected_corners.items():
            with self.subTest(rotation=rotation):
                m = touchscreen.target_matrix(layout(geometry="1920x1080+1920+1080", rotation=rotation))
                corners = [(m[0]*x + m[1]*y + m[2], m[3]*x + m[4]*y + m[5])
                           for x, y in ((0, 0), (1, 0), (0, 1))]
                self.assertEqual(corners, expected)

    def test_reconnection_sets_mapping_before_enabling_touch(self):
        for name in (touchscreen.DEVICE, f"∼ {touchscreen.DEVICE}"):
            with self.subTest(name=name), patch.object(touchscreen, "run", side_effect=[
                name, layout(), properties(0), "", "",
            ]) as run:
                touchscreen.update_mapping()
            self.assertEqual(run.call_args_list[-2].args[:4],
                             ("xinput", "set-prop", touchscreen.DEVICE, touchscreen.MATRIX_PROPERTY))
            self.assertEqual(run.call_args_list[-1], call("xinput", "enable", touchscreen.DEVICE))

    def test_duplicate_attached_and_floating_devices_are_not_changed(self):
        devices = f"{touchscreen.DEVICE}\n∼ {touchscreen.DEVICE}\n"
        with patch.object(touchscreen, "run", return_value=devices) as run:
            touchscreen.update_mapping()
        self.assertEqual(run.call_count, 1)

    def test_disconnected_monitor_disables_touch_without_changing_other_devices(self):
        with patch.object(touchscreen, "run", side_effect=[touchscreen.DEVICE, layout(geometry=""), properties(), ""]) as run:
            touchscreen.update_mapping()
        self.assertEqual(run.call_args_list[-1], call("xinput", "disable", touchscreen.DEVICE))

    def test_correct_mapping_is_not_reapplied(self):
        with patch.object(touchscreen, "run", side_effect=[
            touchscreen.DEVICE, layout(), properties(matrix="0.25, 0, 0, 0, 0.5, 0, 0, 0, 1"),
        ]) as run:
            touchscreen.update_mapping()
        self.assertEqual(run.call_count, 3)

    def test_absent_touchscreen_does_not_change_anything(self):
        with patch.object(touchscreen, "run", return_value="PixArt USB Optical Mouse") as run:
            touchscreen.update_mapping()
        self.assertEqual(run.call_count, 1)

    def test_transient_error_is_retried(self):
        with patch.object(touchscreen, "update_mapping", side_effect=[
            subprocess.CalledProcessError(1, "xinput"), None,
        ]) as update, patch.object(touchscreen.time, "sleep", side_effect=[None, KeyboardInterrupt]), patch("builtins.print"):
            with self.assertRaises(KeyboardInterrupt):
                touchscreen.watch_touchscreen()
        self.assertEqual(update.call_count, 2)


if __name__ == "__main__":
    unittest.main()
