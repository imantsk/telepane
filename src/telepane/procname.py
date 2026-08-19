"""Human-readable foreground command names per tty. No shell: every call is an
argv list through subprocess."""

from __future__ import annotations

import re
import subprocess

_PS_ARGS = ["ps", "-axo", "tty=,stat=,pid=,ppid=,command="]

# Interpreters run scripts with the interpreter as argv[0]; the script name is
# the readable one.
_INTERPRETERS = re.compile(r"^(python[0-9.]*|node|bun|deno|ruby|perl)$", re.IGNORECASE)


def foreground_names() -> dict[str, str]:
    """Map a pane tty (`/dev/ttys003`, `/dev/pts/0`) to its foreground command
    name. The root of the tty's foreground group (the `+` process whose parent
    is outside the group) is the one the user invoked; its argv names it
    better than the kernel process name. Pids recycle, so pid order alone is
    not reliable."""
    try:
        out = subprocess.run(_PS_ARGS, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    groups: dict[str, list[tuple[int, int, str]]] = {}
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        tty, stat, pid_s, ppid_s, command = parts
        if "+" not in stat or tty in ("?", "??"):
            continue
        try:
            pid, ppid = int(pid_s), int(ppid_s)
        except ValueError:
            continue
        groups.setdefault(tty, []).append((pid, ppid, command))
    out_map: dict[str, str] = {}
    for tty, rows in groups.items():
        pids = {pid for pid, _, _ in rows}
        roots = [(pid, command) for pid, ppid, command in rows if ppid not in pids]
        pid, command = min(roots) if roots else min((p, c) for p, _, c in rows)
        out_map[f"/dev/{tty}"] = display_name(command)
    return out_map


def display_name(command: str) -> str:
    """The callable name behind a raw ps command string."""
    tokens = command.split()
    if not tokens:
        return command
    name = _basename(tokens[0])
    if _INTERPRETERS.match(name):
        for token in tokens[1:]:
            if not token.startswith("-"):
                script = _basename(token)
                if script:
                    return script
                break
    return name


def _basename(token: str) -> str:
    name = token.rsplit("/", 1)[-1]
    if name.lower().endswith(".exe"):
        name = name[: -len(".exe")]
    return name
