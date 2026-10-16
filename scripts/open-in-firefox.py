#!/usr/bin/python3
"""Open a selected or copied web address or local file URL in Firefox."""

import argparse
import subprocess
from urllib.parse import urlsplit


def web_url(text):
    url = text.strip()
    if not url or any(character.isspace() or ord(character) < 32 for character in url):
        return None

    try:
        parts = urlsplit(url)
        is_web_address = parts.scheme in ("http", "https") and bool(parts.hostname)
        is_local_file = (
            parts.scheme == "file"
            and parts.netloc in ("", "localhost")
            and parts.path.startswith("/")
        )
        # Accessing port validates malformed and out-of-range port numbers.
        parts.port
    except ValueError:
        return None

    return url if is_web_address or is_local_file else None


def open_url(selection):
    try:
        result = subprocess.run(
            ["xclip", "-selection", selection, "-o"],
            capture_output=True, text=True, check=True, timeout=2,
        )
        url = web_url(result.stdout)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        url = None

    if url is None:
        instruction = "Kopiera" if selection == "clipboard" else "Markera"
        subprocess.run([
            "rofi", "-e", f"{instruction} en hel http://-, https://- eller file://-adress och försök igen.",
        ], check=False)
        return 1

    # Pass the URL as one argument, never as a shell command.
    subprocess.Popen(["firefox", "--new-tab", url], start_new_session=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clipboard", action="store_true", help="Use copied text instead of selected text")
    args = parser.parse_args()
    raise SystemExit(open_url("clipboard" if args.clipboard else "primary"))
