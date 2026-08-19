"""tmux backend: all calls go through `_run` (argv, no shell); objects are
addressed by tmux id (`$`/`@`/`%`)."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field

TMUX = "tmux"
_UNIT = "\t"
_ROW = "\n"


class TmuxError(RuntimeError):
    """A tmux invocation exited non-zero."""


def _run(args: list[str], *, check: bool = True) -> str:
    """Run `tmux <args>` with no shell. Return stdout (stripped of trailing NL)."""
    try:
        proc = subprocess.run(
            [TMUX, *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise TmuxError("tmux executable not found on PATH") from exc
    if proc.returncode != 0:
        if check:
            raise TmuxError(proc.stderr.strip() or f"tmux {args[0]} failed")
        return ""
    return proc.stdout.rstrip("\n")


def _rows(out: str) -> list[list[str]]:
    return [line.split(_UNIT) for line in out.split(_ROW) if line]


# ── availability ────────────────────────────────────────────────────────────


def is_installed() -> bool:
    return shutil.which(TMUX) is not None


def server_running() -> bool:
    try:
        subprocess.run(
            [TMUX, "info"],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ── models ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Pane:
    id: str
    index: int
    title: str
    command: str
    path: str
    active: bool
    pid: int
    width: int
    height: int
    tty: str = ""

    @property
    def target(self) -> str:
        return self.id


@dataclass(frozen=True)
class Window:
    id: str
    index: int
    name: str
    pane_count: int
    active: bool
    layout: str
    panes: list[Pane] = field(default_factory=list)

    @property
    def target(self) -> str:
        return self.id


@dataclass(frozen=True)
class Session:
    id: str
    name: str
    window_count: int
    attached: bool
    created: int
    activity: int
    path: str
    windows: list[Window] = field(default_factory=list)

    @property
    def target(self) -> str:
        return self.id


_SESSION_FMT = _UNIT.join(
    [
        "#{session_id}",
        "#{session_name}",
        "#{session_windows}",
        "#{session_attached}",
        "#{session_created}",
        "#{session_activity}",
        "#{session_path}",
    ]
)

_WINDOW_FMT = _UNIT.join(
    [
        "#{window_id}",
        "#{window_index}",
        "#{window_name}",
        "#{window_panes}",
        "#{window_active}",
        "#{window_layout}",
    ]
)

_PANE_FMT = _UNIT.join(
    [
        "#{pane_id}",
        "#{pane_index}",
        "#{pane_title}",
        "#{pane_current_command}",
        "#{pane_current_path}",
        "#{pane_active}",
        "#{pane_pid}",
        "#{pane_width}",
        "#{pane_height}",
        "#{pane_tty}",
    ]
)


def _int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# ── reads ─────────────────────────────────────────────────────────────────--


def list_panes(window_target: str) -> list[Pane]:
    out = _run(["list-panes", "-t", window_target, "-F", _PANE_FMT], check=False)
    panes: list[Pane] = []
    for r in _rows(out):
        if len(r) < 9:
            continue
        panes.append(
            Pane(
                id=r[0],
                index=_int(r[1]),
                title=r[2],
                command=r[3],
                path=r[4],
                active=r[5] == "1",
                pid=_int(r[6]),
                width=_int(r[7]),
                height=_int(r[8]),
                tty=r[9] if len(r) > 9 else "",
            )
        )
    return panes


def list_windows(session_target: str, *, with_panes: bool = True) -> list[Window]:
    out = _run(["list-windows", "-t", session_target, "-F", _WINDOW_FMT], check=False)
    windows: list[Window] = []
    for r in _rows(out):
        if len(r) < 6:
            continue
        wid = r[0]
        windows.append(
            Window(
                id=wid,
                index=_int(r[1]),
                name=r[2],
                pane_count=_int(r[3]),
                active=r[4] == "1",
                layout=r[5],
                panes=list_panes(wid) if with_panes else [],
            )
        )
    return windows


def list_sessions(*, deep: bool = True) -> list[Session]:
    out = _run(["list-sessions", "-F", _SESSION_FMT], check=False)
    sessions: list[Session] = []
    for r in _rows(out):
        if len(r) < 7:
            continue
        sid = r[0]
        sessions.append(
            Session(
                id=sid,
                name=r[1],
                window_count=_int(r[2]),
                attached=r[3] == "1",
                created=_int(r[4]),
                activity=_int(r[5]),
                path=r[6],
                windows=list_windows(sid) if deep else [],
            )
        )
    return sessions


_SNAPSHOT_FMT = _UNIT.join(
    [
        "#{session_id}",
        "#{session_name}",
        "#{session_attached}",
        "#{session_created}",
        "#{session_activity}",
        "#{session_path}",
        "#{session_windows}",
        "#{window_id}",
        "#{window_index}",
        "#{window_name}",
        "#{window_active}",
        "#{window_panes}",
        "#{window_layout}",
        "#{pane_id}",
        "#{pane_index}",
        "#{pane_title}",
        "#{pane_current_command}",
        "#{pane_current_path}",
        "#{pane_active}",
        "#{pane_pid}",
        "#{pane_width}",
        "#{pane_height}",
        "#{pane_tty}",
    ]
)


def snapshot() -> list[Session]:
    """The whole session/window/pane tree in a SINGLE fork (`list-panes -a`)."""
    out = _run(["list-panes", "-a", "-F", _SNAPSHOT_FMT], check=False)
    order: list[str] = []
    sess: dict[str, dict] = {}
    for r in _rows(out):
        if len(r) < 22:
            continue
        sid, wid = r[0], r[7]
        s = sess.get(sid)
        if s is None:
            s = {
                "id": sid,
                "name": r[1],
                "attached": r[2] == "1",
                "created": _int(r[3]),
                "activity": _int(r[4]),
                "path": r[5],
                "wcount": _int(r[6]),
                "wins": {},
                "worder": [],
            }
            sess[sid] = s
            order.append(sid)
        w = s["wins"].get(wid)
        if w is None:
            w = {
                "id": wid,
                "index": _int(r[8]),
                "name": r[9],
                "active": r[10] == "1",
                "pcount": _int(r[11]),
                "layout": r[12],
                "panes": [],
            }
            s["wins"][wid] = w
            s["worder"].append(wid)
        w["panes"].append(
            Pane(
                id=r[13],
                index=_int(r[14]),
                title=r[15],
                command=r[16],
                path=r[17],
                active=r[18] == "1",
                pid=_int(r[19]),
                width=_int(r[20]),
                height=_int(r[21]),
                tty=r[22] if len(r) > 22 else "",
            )
        )
    result: list[Session] = []
    for sid in order:
        s = sess[sid]
        wins = [
            Window(
                id=w["id"],
                index=w["index"],
                name=w["name"],
                pane_count=w["pcount"],
                active=w["active"],
                layout=w["layout"],
                panes=w["panes"],
            )
            for w in (s["wins"][wid] for wid in s["worder"])
        ]
        result.append(
            Session(
                id=s["id"],
                name=s["name"],
                window_count=s["wcount"],
                attached=s["attached"],
                created=s["created"],
                activity=s["activity"],
                path=s["path"],
                windows=wins,
            )
        )
    return result


def capture_pane(pane_target: str, *, scrollback: int = 0) -> str:
    args = ["capture-pane", "-p", "-t", pane_target]
    if scrollback > 0:
        args += ["-S", f"-{scrollback}"]
    return _run(args, check=False)


_version_cache: str | None = None


def version() -> str:
    """tmux version (cached)."""
    global _version_cache
    if _version_cache is None:
        if is_installed():
            _version_cache = _run(["-V"], check=False).split(" ")[-1] or "?"
        else:
            _version_cache = "?"
    return _version_cache


def server_info(sessions: list[Session] | None = None) -> dict[str, str]:
    """Server stats derived from `sessions`."""
    if sessions is None:
        sessions = snapshot()
    if not sessions and not server_running():
        return {"version": version(), "running": "no"}
    disp = _run(
        [
            "display-message",
            "-p",
            "-F",
            _UNIT.join(["#{pid}", "#{socket_path}", "#{client_termname}"]),
        ],
        check=False,
    ).split(_UNIT)
    windows = sum(s.window_count for s in sessions)
    panes = sum(len(w.panes) for s in sessions for w in s.windows)
    clients = len(_rows(_run(["list-clients", "-F", "#{client_name}"], check=False)))
    return {
        "version": version(),
        "running": "yes",
        "pid": disp[0] if len(disp) > 0 else "?",
        "socket": disp[1] if len(disp) > 1 else "?",
        "term": disp[2] if len(disp) > 2 else "?",
        "sessions": str(len(sessions)),
        "windows": str(windows),
        "panes": str(panes),
        "clients": str(clients),
    }


# ── the core feature: send text to a chosen pane ─────────────────────────────


def send_text(pane_target: str, text: str, *, enter: bool = True) -> None:
    """Send `text` literally to `pane_target`, optionally pressing Enter."""
    # tmux parses a trailing unescaped ";" in any argument as a command
    # separator, even in argv mode. Escape it or the last character is lost.
    if text.endswith(";"):
        text = text[:-1] + "\\;"
    if text and enter:
        _run(
            [
                "send-keys",
                "-t",
                pane_target,
                "-l",
                "--",
                text,
                ";",
                "send-keys",
                "-t",
                pane_target,
                "Enter",
            ]
        )
    elif text:
        _run(["send-keys", "-t", pane_target, "-l", "--", text])
    elif enter:
        _run(["send-keys", "-t", pane_target, "Enter"])


def send_keys(pane_target: str, keys: list[str]) -> None:
    """Send raw key names (e.g. ['C-c'], ['Escape']), interpreted, not literal."""
    _run(["send-keys", "-t", pane_target, *keys])


# ── writes / controls ────────────────────────────────────────────────────────


def new_session(name: str, path: str | None = None) -> None:
    args = ["new-session", "-d", "-s", name]
    if path:
        args += ["-c", path]
    _run(args)


def kill_session(session_target: str) -> None:
    _run(["kill-session", "-t", session_target])


def rename_session(session_target: str, new_name: str) -> None:
    _run(["rename-session", "-t", session_target, new_name])


def new_window(session_target: str, name: str | None = None) -> None:
    args = ["new-window", "-t", session_target]
    if name:
        args += ["-n", name]
    _run(args)


def kill_window(window_target: str) -> None:
    _run(["kill-window", "-t", window_target])


def rename_window(window_target: str, new_name: str) -> None:
    _run(["rename-window", "-t", window_target, new_name])


def split_window(
    pane_target: str,
    *,
    horizontal: bool = False,
    command: str | None = None,
    start_dir: str | None = None,
) -> None:
    args = ["split-window", "-h" if horizontal else "-v", "-t", pane_target]
    if start_dir:
        args += ["-c", start_dir]
    if command:
        args.append(command)
    _run(args)


def kill_pane(pane_target: str) -> None:
    _run(["kill-pane", "-t", pane_target])


def select_pane(pane_target: str) -> None:
    _run(["select-pane", "-t", pane_target])


# ── options ───────────────────────────────────────────────────────────────--

_SCOPE_FLAGS = {"session": ["-g"], "server": ["-s"], "window": ["-gw"]}


def set_option(name: str, value: str, *, scope: str = "session") -> None:
    _run(["set-option", *_SCOPE_FLAGS.get(scope, ["-g"]), name, str(value)])


def show_option(name: str, *, scope: str = "session") -> str:
    flags = _SCOPE_FLAGS.get(scope, ["-g"])
    return _run(["show-options", *flags, "-v", name], check=False).strip()


def show_all_options(scope: str = "session") -> dict[str, str]:
    """All options for a scope in ONE fork, parsed to {name: value}."""
    flags = _SCOPE_FLAGS.get(scope, ["-g"])
    out = _run(["show-options", *flags], check=False)
    result: dict[str, str] = {}
    for line in out.split(_ROW):
        if not line:
            continue
        name, _, value = line.partition(" ")
        result[name] = value.strip().strip('"')
    return result


def source_file(path: str) -> None:
    _run(["source-file", path])
