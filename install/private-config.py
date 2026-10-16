#!/usr/bin/env python3
"""Install private copies of tracked dotfiles, backing up replaced destinations."""

import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


REPOSITORY = Path(__file__).resolve().parents[1]
CONFIG_DIRECTORIES = ("i3", "nvim", "alacritty", "scripts", "lazygit", "rofi", "flameshot")
HOME_FILES = {
    "bash/.bashrc": ".bashrc",
    "bash/.bash_aliases": ".bash_aliases",
    "bash/.profile": ".profile",
    "tmux/.tmux.conf": ".tmux.conf",
}
EXCLUDED_FILES = {
    "scripts/home-three-monitors.sh",
    "scripts/map-touchscreen.py",
}


def private_content(relative_path, content):
    if relative_path == "bash/.bashrc":
        content = content.replace('/home/johan/.local/bin', '$HOME/.local/bin')
        content = re.sub(r"^# .*Codex installer.*\n", "", content, flags=re.M)
        content = content.replace('alias nmtui="$HOME/.local/bin/nmtui-themed"', '')
    elif relative_path == "bash/.bash_aliases":
        content = re.sub(r"^jira-[\w-]+\(\) \{\n.*?^\}\n", "", content, flags=re.M | re.S)
        content = re.sub(r"^alias screen-[23]=.*\n", "", content, flags=re.M)
    elif relative_path == "i3/config":
        content = "\n".join(
            line for line in content.splitlines()
            if not any(marker in line for marker in (
                "crx_", 'class="Slack"',
                "xinput set-prop", "map-touchscreen.py", "chatgpt.com", "ChatGPT",
            ))
        ) + "\n"
    elif relative_path == "i3/i3blocks.conf":
        content = content.replace("command=stand-up-timer", "command=$HOME/.config/i3/hydration-reminder")
    elif relative_path in ("scripts/system-menu.sh", "scripts/fix-workspaces.sh"):
        content = "\n".join(
            line for line in content.splitlines()
            if not any(marker in line for marker in (
                "Home · three monitors", "crx_", 'class="Slack"',
                "chatgpt.com",
            ))
        ) + "\n"
    elif relative_path == "flameshot/flameshot.ini":
        content = re.sub(r"^savePath=.*\n?", "", content, flags=re.M)
    elif relative_path == "scripts/lockscreen.sh":
        # The screenshot lock depends on an image missing from this repository.
        content = "#!/bin/sh\nexec i3lock -c 011423\n"
    return content


def install_config(home, *, apply=False):
    tracked_paths = subprocess.check_output(
        ["git", "-C", str(REPOSITORY), "ls-files", "-z"], text=True
    ).split("\0")
    selected_paths = [
        relative_path for relative_path in tracked_paths
        if relative_path and relative_path not in EXCLUDED_FILES
        and (relative_path.split("/")[0] in CONFIG_DIRECTORIES or relative_path in HOME_FILES)
    ]
    destinations = [f".config/{directory}" for directory in CONFIG_DIRECTORIES] + list(HOME_FILES.values())
    for destination in destinations:
        print(f"{'Installing' if apply else 'Would install'}: {home / destination}")
    if not apply:
        return None

    backup_directory = home / ".local/state/dotfiles-backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_directory.mkdir(parents=True, mode=0o700)
    with tempfile.TemporaryDirectory(prefix="dotfiles-private-") as temporary_directory:
        staging_directory = Path(temporary_directory)
        for relative_path in selected_paths:
            source = REPOSITORY / relative_path
            target = staging_directory / HOME_FILES.get(relative_path, f".config/{relative_path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(private_content(relative_path, source.read_text()))
            shutil.copymode(source, target)

        # Build every copy before replacing any active configuration.
        for relative_destination in destinations:
            destination = home / relative_destination
            backup = backup_directory / relative_destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() or destination.is_symlink():
                backup.parent.mkdir(parents=True, exist_ok=True)
                destination.rename(backup)
            shutil.move(str(staging_directory / relative_destination), destination)

    print(f"Backup: {backup_directory}")
    return backup_directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home(), help="Destination (also used for isolated tests)")
    parser.add_argument("--apply", action="store_true", help="Write copies; defaults to preview only")
    arguments = parser.parse_args()
    install_config(arguments.home.expanduser().absolute(), apply=arguments.apply)
