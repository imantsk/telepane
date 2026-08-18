"""Window > pane tree: root hidden, windows top-level, panes beneath."""

from __future__ import annotations

from dataclasses import dataclass

from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from ..tmux import Session

KIND_SESSION = "session"
KIND_WINDOW = "window"
KIND_PANE = "pane"


@dataclass(frozen=True)
class NodeRef:
    kind: str
    target: str
    send_target: str
    label: str


def _pane_label(p) -> str:
    mark = "◆" if p.active else "◇"
    return f"{mark} {p.id} [b]{p.command}[/]  [dim]{p.width}×{p.height}[/]"


def _window_label(prefix: str, w) -> str:
    mark = "▸" if w.active else " "
    return f"{mark} {prefix}{w.index}:{w.name}  [dim]{w.pane_count}p[/]"


def build_tree(tree: Tree[NodeRef], sessions: list[Session]) -> None:
    tree.clear()
    multi = len(sessions) > 1
    for s in sessions:
        prefix = f"[dim]{s.name}[/] " if multi else ""
        for w in s.windows:
            wsend = next(
                (p.id for p in w.panes if p.active),
                w.panes[0].id if w.panes else w.id,
            )
            w_node: TreeNode[NodeRef] = tree.root.add(
                _window_label(prefix, w),
                data=NodeRef(KIND_WINDOW, w.id, wsend, w.name),
                expand=w.active,
            )
            for p in w.panes:
                w_node.add_leaf(
                    _pane_label(p),
                    data=NodeRef(KIND_PANE, p.id, p.id, f"{w.name}.{p.index}"),
                )


def refresh_labels(tree: Tree[NodeRef], sessions: list[Session]) -> None:
    """Update pane labels in place."""
    panes = {p.id: p for s in sessions for w in s.windows for p in w.panes}
    for w_node in tree.root.children:
        for p_node in w_node.children:
            ref = p_node.data
            p = panes.get(ref.send_target) if ref else None
            if p is not None:
                p_node.set_label(_pane_label(p))
