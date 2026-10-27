#!/usr/bin/python3
"""Move the focused workspace and keep its window and pointer together."""

import argparse
import json
import subprocess


def i3(message_type, command=None):
    arguments = ["i3-msg", "-t", message_type]
    if command is not None:
        arguments.append(command)
    result = subprocess.run(arguments, capture_output=True, text=True, check=True)
    response = json.loads(result.stdout)
    if message_type == "command" and any(not reply.get("success") for reply in response):
        raise RuntimeError(f"i3 kunde inte utföra kommandot: {response}")
    return response


def containers(node):
    yield node
    for child in node.get("nodes", []) + node.get("floating_nodes", []):
        yield from containers(child)


def move_workspace(direction):
    focused = next(node for node in containers(i3("get_tree")) if node.get("focused"))
    container_id = focused["id"]
    i3("command", f"[con_id={container_id}] move workspace to output {direction}")

    moved = next(
        node for node in containers(i3("get_tree")) if node["id"] == container_id
    )
    rectangle = moved["rect"]
    pointer_x = rectangle["x"] + rectangle["width"] // 2
    pointer_y = rectangle["y"] + rectangle["height"] // 2
    subprocess.run(
        ["xdotool", "mousemove", "--sync", str(pointer_x), str(pointer_y)],
        check=True,
    )
    # Reassert the original focus after any pointer-enter events from the move.
    i3("command", f"[con_id={container_id}] focus")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("direction", choices=("left", "right", "up", "down"))
    args = parser.parse_args()
    try:
        move_workspace(args.direction)
    except (OSError, ValueError, KeyError, StopIteration, RuntimeError,
            subprocess.SubprocessError) as error:
        subprocess.run(["rofi", "-e", f"Flytta workspace: {error}"], check=False)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
