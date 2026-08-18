"""Draggable dividers: axis `x` resizes width, axis `y` resizes height; emits
`Committed` on release."""

from __future__ import annotations

from rich.text import Text
from textual import events
from textual.css.scalar import Unit
from textual.message import Message
from textual.widget import Widget

GRIP_V = "┆"
GRIP_H = "┄"
_FILL = 400


def clamp_size(value: int, extent: int, min_size: int) -> int:
    """Clamp a divider drag so both sides keep at least `min_size`."""
    return max(min_size, min(value, extent - min_size))


class Resizer(Widget):
    class Committed(Message):
        def __init__(self, key: str, size: int) -> None:
            self.key = key
            self.size = size
            super().__init__()

    def __init__(
        self, target: str, *, key: str, axis: str = "x", min_size: int = 20, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._target = target
        self._key = key
        self._axis = axis
        self._min = min_size
        self._dragging = False
        self._drag_size = 0
        self.tooltip = "drag to resize"

    def render(self) -> Text:
        if self._axis == "x":
            return Text("\n".join(GRIP_V for _ in range(_FILL)), no_wrap=True)
        return Text(GRIP_H * _FILL, no_wrap=True)

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._dragging = True
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self._dragging:
            return
        target = self.screen.query_one(self._target)
        if self._axis == "x":
            self._drag_size = clamp_size(event.screen_x, self.app.size.width, self._min)
            target.styles.width = self._drag_size
        else:
            self._drag_size = max(self._min, min(self._below(event), self.max_height()))
            self.apply_height(self._drag_size)
        event.stop()

    def _below(self, event: events.MouseMove) -> int:
        return self.app.size.height - event.screen_y - 1

    def apply_height(self, height: int) -> None:
        """Set the target height; hide the fr sibling at maximum."""
        self.screen.query_one(self._target).styles.height = height
        fr = self._fr_sibling()
        if fr is not None:
            fr.styles.display = "none" if height >= self.max_height() else "block"

    def _fr_sibling(self) -> Widget | None:
        if self.parent is None:
            return None
        target = self.screen.query_one(self._target)
        for sibling in self.parent.children:
            if sibling is self or sibling is target:
                continue
            height = sibling.styles.height
            if height is not None and height.unit == Unit.FRACTION:
                return sibling
        return None

    def max_height(self) -> int:
        if self.parent is None:
            return self._min
        target = self.screen.query_one(self._target)
        reserve = self.outer_size.height
        for sibling in self.parent.children:
            if sibling is self or sibling is target:
                continue
            height = sibling.styles.height
            if sibling.display and (height is None or height.unit != Unit.FRACTION):
                reserve += sibling.outer_size.height
        return max(self._min, self.parent.size.height - reserve)

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self.release_mouse()
        if self._drag_size:
            self.post_message(self.Committed(self._key, self._drag_size))
        event.stop()
