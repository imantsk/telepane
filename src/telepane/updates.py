"""Update check and in-place upgrade. The only remote call in telepane is the
PyPI JSON endpoint for this package; the upgrade is an argv pip call."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request

PYPI_URL = "https://pypi.org/pypi/telepane/json"
_TIMEOUT = 5.0
_SPLIT = re.compile(r"[._\-+]")


def latest_version() -> str | None:
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=_TIMEOUT) as response:
            return str(json.load(response)["info"]["version"])
    except Exception:
        return None


def is_newer(candidate: str, current: str) -> bool:
    return _key(candidate) > _key(current)


def _key(version: str) -> list[int]:
    return [int(part) if part.isdigit() else -1 for part in _SPLIT.split(version) if part]


def upgrade() -> bool:
    """Upgrade telepane inside the running interpreter's environment."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "telepane"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False
