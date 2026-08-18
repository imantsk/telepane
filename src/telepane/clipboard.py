"""Clipboard helpers. No shell: every call is an argv list through subprocess."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _run(args: list[str], text: str | None = None) -> bool:
    try:
        subprocess.run(args, input=text, text=True, capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def copy_text(text: str) -> bool:
    if sys.platform == "darwin" and shutil.which("pbcopy"):
        return _run(["pbcopy"], text)
    if shutil.which("wl-copy"):
        return _run(["wl-copy"], text)
    if shutil.which("xclip"):
        return _run(["xclip", "-selection", "clipboard"], text)
    if shutil.which("xsel"):
        return _run(["xsel", "-b", "-i"], text)
    return False


def copy_file(path: str) -> bool:
    """Put the file itself on the clipboard (macOS); elsewhere copy its text."""
    if sys.platform == "darwin" and shutil.which("osascript"):
        safe = path.replace("\\", "\\\\").replace('"', '\\"')
        script = f'set the clipboard to (POSIX file "{safe}")'
        if _run(["osascript", "-e", script]):
            return True
    try:
        return copy_text(Path(path).read_text())
    except OSError:
        return False
