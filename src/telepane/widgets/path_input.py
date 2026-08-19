"""Directory input with Tab completion."""

from __future__ import annotations

import os

from textual import events
from textual.widgets import Input


def complete_dir(value: str, home: str) -> tuple[str, list[str]]:
    """Complete `value` to the longest common directory prefix.

    Returns (new_value, candidates). Candidates are the matching directory
    paths, in display form ("~" kept when the input used it).
    """
    raw = value.strip() or "~"
    expanded = raw.replace("~", home, 1) if raw.startswith("~") else raw
    base, partial = os.path.split(expanded)
    if not base:
        base = "."
    try:
        entries = sorted(
            entry.name
            for entry in os.scandir(base)
            if entry.is_dir(follow_symlinks=True) and entry.name.startswith(partial)
        )
    except OSError:
        return value, []
    if partial == "" and raw.endswith(os.sep):
        matches = entries
    else:
        matches = [name for name in entries if name.startswith(partial)]
    if not matches:
        return value, []
    common = os.path.commonprefix(matches)
    completed = os.path.join(base, common)
    if len(matches) == 1:
        completed += os.sep
    if raw.startswith("~") and home:
        completed = "~" + completed[len(home) :] if completed.startswith(home) else completed
    candidates = [os.path.join(base, name) for name in matches]
    return completed, candidates


class PathInput(Input):
    """Input for a directory path. Tab completes; repeated Tab cycles."""

    def __init__(self, *args, home: str = "", **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._home = home
        self._cycle: list[str] = []
        self._cycle_at = 0

    async def _on_key(self, event: events.Key) -> None:
        if event.key != "tab":
            self._cycle = []
            await super()._on_key(event)
            return
        event.stop()
        event.prevent_default()
        if self._cycle:
            self._cycle_at = (self._cycle_at + 1) % len(self._cycle)
            self.value = self._cycle[self._cycle_at] + os.sep
            self.cursor_position = len(self.value)
            return
        completed, candidates = complete_dir(self.value, self._home)
        if completed != self.value:
            self.value = completed
            self.cursor_position = len(self.value)
        if len(candidates) > 1 and completed == self.value:
            self._cycle = candidates
            self._cycle_at = -1
