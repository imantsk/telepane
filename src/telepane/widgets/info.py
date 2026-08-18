"""Rich-markup renderers for the server-stats and selected-target panels."""

from __future__ import annotations

from ..tmux import Pane
from .tree import NodeRef

_SEP = "  [dim]·[/]  "
_SEP_LEN = 5


def compact_path(path: str, home: str = "") -> str:
    """Compact a path: home → ~, parent dirs to their first letter."""
    if home and (path == home or path.startswith(home + "/")):
        path = "~" + path[len(home) :]
    parts = path.split("/")
    if len(parts) <= 1:
        return path
    head = [p[:1] if p else "" for p in parts[:-1]]
    return "/".join([*head, parts[-1]])


def _fit(value: str, budget: int) -> tuple[str, bool]:
    """Truncate to `budget` with …; own_line=True when under half would show."""
    if budget >= len(value):
        return value, False
    if budget < len(value) / 2:
        return value, True
    return value[: max(1, budget - 1)] + "…", False


def render_server(info: dict) -> str:
    """One-line stats header. Rendered in a wrapping Static: it stays on a single
    line while the viewport is wide and folds onto more lines as it narrows."""
    if info.get("running") != "yes":
        return f"[b]tmux[/] {info.get('version', '?')}   [red]server not running[/]"
    parts = [
        f"[green]{info['sessions']}[/] sess",
        f"[green]{info['windows']}[/] win",
        f"[green]{info['panes']}[/] pane",
        f"[green]{info['clients']}[/] client",
        f"[b]tmux[/] {info['version']}",
        f"[dim]pid[/] {info['pid']}",
        f"[dim]socket[/] {info['socket']}",
    ]
    return _SEP.join(parts)


def render_target(
    ref: NodeRef | None, pane: Pane | None, *, width: int = 80, home: str = ""
) -> str:
    """Target status bar. Short identity/meta fields sit inline; the long fields
    (path, title) are compacted and ellipsised to fit the width, and drop to
    their own line when truncation would hide more than half."""
    if ref is None:
        return "[dim]Select a session, window, or pane.[/]"

    fixed = [
        (f"[b]target[/] [yellow]{ref.send_target}[/]", len("target ") + len(ref.send_target)),
        (f"[dim]{ref.kind}[/] {ref.label}", len(ref.kind) + 1 + len(ref.label)),
    ]
    if pane is not None:
        size = f"{pane.width}×{pane.height}"
        fixed += [
            (f"[dim]cmd[/] {pane.command}", 4 + len(pane.command)),
            (f"[dim]pid[/] {pane.pid}", 4 + len(str(pane.pid))),
            (f"[dim]size[/] {size}", 5 + len(size)),
        ]

    lines: list[str] = []
    cur: list[str] = []
    cur_len = 0

    def flush() -> None:
        nonlocal cur, cur_len
        if cur:
            lines.append(_SEP.join(cur))
            cur, cur_len = [], 0

    for markup, plen in fixed:
        add = plen + (_SEP_LEN if cur else 0)
        if cur and cur_len + add > width:
            flush()
            add = plen
        cur.append(markup)
        cur_len += add

    if pane is not None:
        tail = [("path", compact_path(pane.path, home))]
        if pane.title:
            tail.append(("title", pane.title))
        for label, value in tail:
            avail = width - (cur_len + _SEP_LEN if cur else 0) - (len(label) + 1)
            text, own = _fit(value, max(0, avail))
            seg = f"[dim]{label}[/] {text}"
            if own or avail <= 0:
                flush()
                lines.append(f"[dim]{label}[/] {value}")
            else:
                cur.append(seg)
                cur_len += (len(label) + 1 + len(text)) + (_SEP_LEN if len(cur) > 1 else 0)
    flush()
    return "\n".join(lines)
