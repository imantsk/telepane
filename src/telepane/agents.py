"""Agent CLI discovery and bypass-flag inference. No shell: every call is an
argv list through subprocess."""

from __future__ import annotations

import shutil
import subprocess

KNOWN = [
    "aider",
    "amp",
    "auggie",
    "claude",
    "cline",
    "codex",
    "cody",
    "copilot",
    "crush",
    "cursor-agent",
    "droid",
    "gemini",
    "goose",
    "kode",
    "opencode",
    "qwen",
]


def installed() -> list[str]:
    return [name for name in KNOWN if shutil.which(name)]


# Bypass-flag vocabulary across harnesses, most specific first. The flag for a
# given CLI is inferred from its own --help output, never from its name.
_BYPASS_FLAGS = [
    "--dangerously-bypass-approvals-and-sandbox",
    "--dangerously-skip-permissions",
    "--yolo",
    "--allow-all-tools",
    "--yes-always",
]
_HELP_TIMEOUT = 4.0
_flag_cache: dict[str, str | None] = {}


def bypass_flag(name: str) -> str | None:
    """The approval-bypass flag that `name --help` advertises, or None."""
    if name in _flag_cache:
        return _flag_cache[name]
    try:
        proc = subprocess.run(
            [name, "--help"],
            capture_output=True,
            text=True,
            timeout=_HELP_TIMEOUT,
            check=False,
        )
        text = proc.stdout + proc.stderr
    except (OSError, subprocess.SubprocessError):
        text = ""
    flag = next((f for f in _BYPASS_FLAGS if f in text), None)
    _flag_cache[name] = flag
    return flag
