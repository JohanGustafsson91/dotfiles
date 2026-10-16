#!/usr/bin/python3
"""Temporarily bring an existing workspace to the screen in front of you."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
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


def choose_output(outputs, focused_output):
    active = sorted(
        (output for output in outputs if output["active"]),
        key=lambda output: output["rect"]["x"] + output["rect"]["width"] / 2,
    )
    if len(active) == 1:
        return active[0]["name"]
    if len(active) == 2:
        external = [output for output in active
                    if not output["name"].startswith(("eDP", "LVDS", "DSI"))]
        if len(external) == 1:
            return external[0]["name"]
    if len(active) == 3:
        return active[1]["name"]
    return focused_output


def layout_signature(outputs):
    return sorted(
        [[output["name"], output["rect"]] for output in outputs if output["active"]],
        key=lambda output: output[0],
    )


def focus_workspace(name):
    i3("command", f"workspace --no-auto-back-and-forth {json.dumps(name, ensure_ascii=False)}")


def move_workspace(workspace, output):
    workspace_name = json.dumps(workspace["name"], ensure_ascii=False)
    i3("command", (
        f"workspace --no-auto-back-and-forth {workspace_name}; "
        f"move workspace to output {json.dumps(output)}; "
        f"workspace --no-auto-back-and-forth {workspace_name}"
    ))


def restore_workspace(saved, workspaces, outputs):
    workspace = next((item for item in workspaces if item["id"] == saved["workspace_id"]), None)
    if (saved["layout"] != layout_signature(outputs) or workspace is None
            or workspace["output"] != saved["target_output"]):
        return False

    move_workspace(workspace, saved["original_output"])
    previous = next((item for item in workspaces
                     if item["id"] == saved["previous_workspace_id"]
                     and item["output"] == saved["target_output"]), None)
    if previous is not None:
        focus_workspace(previous["name"])
    focus_workspace(workspace["name"])
    return True


def toggle_workspace(number, state_path):
    outputs = i3("get_outputs")
    workspaces = i3("get_workspaces")
    selected = next((workspace for workspace in workspaces if workspace["num"] == number), None)
    if selected is None:
        raise RuntimeError(f"Workspace {number} är inte öppen. Öppna den med F{number} först.")

    focused_output = next(workspace["output"] for workspace in workspaces if workspace["focused"])
    target_output = choose_output(outputs, focused_output)
    saved = json.loads(state_path.read_text()) if state_path.exists() else None
    if saved is not None:
        restored = restore_workspace(saved, workspaces, outputs)
        state_path.unlink()
        if restored and saved["workspace_id"] == selected["id"]:
            return
        workspaces = i3("get_workspaces")
        selected = next(workspace for workspace in workspaces if workspace["num"] == number)

    if selected["output"] == target_output:
        focus_workspace(selected["name"])
        return

    previous = next((workspace for workspace in workspaces
                     if workspace["output"] == target_output and workspace["visible"]), None)
    saved = {
        "workspace_id": selected["id"],
        "original_output": selected["output"],
        "target_output": target_output,
        "previous_workspace_id": previous["id"] if previous else None,
        "layout": layout_signature(outputs),
    }
    # Keep recovery information even if a command fails after changing focus.
    state_path.write_text(json.dumps(saved))
    move_workspace(selected, target_output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=int, choices=range(1, 11))
    args = parser.parse_args()
    try:
        socket_path = subprocess.check_output(["i3", "--get-socketpath"], text=True).strip()
        session_id = hashlib.sha256(socket_path.encode()).hexdigest()[:16]
        state_path = Path(os.environ["XDG_RUNTIME_DIR"]) / f"i3-center-{session_id}.json"
        with state_path.with_suffix(".lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            toggle_workspace(args.workspace, state_path)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        subprocess.run(["rofi", "-e", f"Workspace till mitten: {error}"], check=False)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
