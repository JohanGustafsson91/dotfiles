#!/usr/bin/python3
"""Keep the ILITEK touchscreen mapped to its display as the layout changes."""

import fcntl
import os
import re
import subprocess
import time


DEVICE = "ILITEK ILITEK-TP"
# EDID header, manufacturer, product and serial; independent of the connector.
DISPLAY_ID = "00ffffffffffff002f34150201000000"
MATRIX_PROPERTY = "Coordinate Transformation Matrix"


def run(*args):
    return subprocess.run(
        args, check=True, capture_output=True, text=True, timeout=5,
        env={**os.environ, "LC_ALL": "C"},
    ).stdout


def target_matrix(layout):
    screen = re.search(r"current (\d+) x (\d+)", layout)
    if screen is None:
        return None

    screen_width, screen_height = map(int, screen.groups())
    targets = []
    for block in re.split(r"\n(?=\S+ (?:connected|disconnected))", layout):
        edid = re.search(r"EDID:\s*\n\s*([0-9a-fA-F]{32})", block)
        is_target = edid is not None and edid[1].lower() == DISPLAY_ID

        if not is_target:
            continue

        geometry = re.search(r" (\d+)x(\d+)\+(\d+)\+(\d+)", block.splitlines()[0])
        if geometry is None:
            continue

        width, height, left, top = map(int, geometry.groups())
        w, h = width / screen_width, height / screen_height
        x, y = left / screen_width, top / screen_height
        orientation = block.splitlines()[0][geometry.end():].split("(")[0].strip()
        matrices = {
            "": [w, 0, x, 0, h, y, 0, 0, 1],
            "normal": [w, 0, x, 0, h, y, 0, 0, 1],
            "left": [0, -w, x + w, h, 0, y, 0, 0, 1],
            "right": [0, w, x, -h, 0, y + h, 0, 0, 1],
            "inverted": [-w, 0, x + w, 0, -h, y + h, 0, 0, 1],
        }
        targets.append(matrices.get(orientation))

    # Do not guess if two displays report the same identity.
    return targets[0] if len(targets) == 1 else None


def update_mapping():
    # xinput prefixes floating (including disabled) devices even with --name-only.
    devices = [name.removeprefix("∼ ") for name in run("xinput", "list", "--name-only").splitlines()]
    if devices.count(DEVICE) != 1:
        return

    matrix = target_matrix(run("xrandr", "--current", "--prop"))
    properties = run("xinput", "list-props", DEVICE)
    enabled = re.search(r"Device Enabled \(\d+\):\s*(\d)", properties)
    if enabled is None:
        return

    if matrix is None:
        if enabled[1] == "1":
            run("xinput", "disable", DEVICE)
        return

    current = re.search(r"Coordinate Transformation Matrix \(\d+\):([^\n]+)", properties)
    if current is None:
        return

    values = [float(value) for value in current[1].split(",")]
    mapping_matches = len(values) == 9 and all(
        abs(actual - expected) < 0.000001 for actual, expected in zip(values, matrix)
    )

    if not mapping_matches:
        run("xinput", "set-prop", DEVICE, MATRIX_PROPERTY, *map(str, matrix))

    if enabled[1] == "0":
        run("xinput", "enable", DEVICE)


def watch_touchscreen():
    last_error = None
    while True:
        try:
            update_mapping()
            last_error = None
        except (OSError, subprocess.SubprocessError) as error:
            # USB and RandR devices can disappear between reading and updating.
            message = str(error)
            if message != last_error:
                print(f"Touchscreen mapping will retry: {message}", flush=True)
            last_error = message
        time.sleep(2)


if __name__ == "__main__":
    lock_path = os.path.join(os.environ["XDG_RUNTIME_DIR"], "map-touchscreen.lock")
    with open(lock_path, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(0)
        watch_touchscreen()
