"""Open links in the system default or a chosen browser. No shell: every call
is an argv list through subprocess."""

from __future__ import annotations

import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

SYSTEM = "System default"

_MAC_APPS = [
    "Safari",
    "Google Chrome",
    "Firefox",
    "Arc",
    "Brave Browser",
    "Microsoft Edge",
    "Opera",
    "Vivaldi",
    "Chromium",
    "Orion",
    "Zen",
]
_LINUX_BINS = [
    "firefox",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "microsoft-edge",
    "opera",
    "vivaldi",
]


def installed() -> list[str]:
    """Browsers available for the picker, always headed by the system default."""
    if sys.platform == "darwin":
        found = [
            name
            for name in _MAC_APPS
            if Path(f"/Applications/{name}.app").exists()
            or Path(f"/System/Applications/{name}.app").exists()
            or Path(f"/System/Cryptexes/App/System/Applications/{name}.app").exists()
        ]
    elif sys.platform.startswith("linux"):
        found = [binary for binary in _LINUX_BINS if shutil.which(binary)]
    else:
        found = []
    return [SYSTEM, *found]


def open_url(url: str, browser: str = "") -> None:
    """Open `url` in `browser`, or in the system default when blank.

    Only http and https links open. Everything else raises ValueError.
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http and https links open")
    if not browser or browser == SYSTEM:
        webbrowser.open(url)
        return
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", browser, "--", url], check=True, capture_output=True)
    else:
        subprocess.run([browser, url], check=True, capture_output=True)
