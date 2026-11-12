from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StatusBlocksTests(unittest.TestCase):
    def run_block(self, block, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            commands = {
                "cpu": ("mpstat", f"Average: all {100 - value}" if value is not None else ""),
                "memory": ("free", f"Mem: 100 0 0 0 0 {100 - value}" if value is not None else ""),
                "disk": ("df", f"Filesystem Blocks Used Available Capacity Mounted\n/dev/mock 100 0 0 {value}% /" if value is not None else ""),
            }
            source = (ROOT / "i3" / block).read_text()
            if block == "temperature":
                zone = path / "thermal_zone0"
                zone.mkdir()
                (zone / "type").write_text("x86_pkg_temp")
                if value is not None:
                    (zone / "temp").write_text(str(value * 1000))
                source = source.replace("/sys/class/thermal/thermal_zone*/", f"{path}/thermal_zone*/")
            else:
                command, output = commands[block]
                executable = path / command
                executable.write_text("#!/bin/sh\ncat <<'DATA'\n" + output + "\nDATA\n")
                executable.chmod(0o755)
            return subprocess.check_output(
                ["sh", "-c", source], text=True,
                env={**os.environ, "PATH": f"{path}:/usr/bin:/bin"},
            )

    def test_normal_warning_critical_and_missing_readings(self):
        for block, warning, critical in [("cpu", 70, 90), ("memory", 75, 90),
                                         ("temperature", 70, 85), ("disk", 75, 90)]:
            with self.subTest(block=block):
                self.assertEqual(self.run_block(block, warning - 1), "\n\n\n")
                self.assertIn("#FFCC66", self.run_block(block, warning))
                self.assertIn("#E52E2E", self.run_block(block, critical))
                self.assertIn("n/a", self.run_block(block, None))
