"""Installed agent CLI discovery for the split picker."""

from __future__ import annotations

import shutil

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
