"""Send box. `enter_sends`: True → Enter sends / Shift+Enter newline; False → the
reverse."""

from __future__ import annotations

from textual import events
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.strip import Strip
from textual.widgets import Button, Label, Switch, TextArea

from . import md_render


class MessageArea(TextArea):
    enter_sends: bool = True
    open_links: bool = True

    class Submitted(Message):
        pass

    class LinkClicked(Message):
        def __init__(self, url: str) -> None:
            super().__init__()
            self.url = url

    async def _on_mouse_down(self, event: events.MouseDown) -> None:
        if event.shift and self.open_links:
            url = self._link_at(event)
            if url is not None:
                event.stop()
                self.post_message(self.LinkClicked(url))
                return
        await super()._on_mouse_down(event)

    def _link_at(self, event: events.MouseDown) -> str | None:
        try:
            row, column = self.get_target_document_location(event)
            lines = self.document.lines
            if row >= len(lines):
                return None
            links = md_render.line_links(lines[row])
            if not links:
                return None
            if len(links) == 1:
                return links[0][4]
            raw = self.cursor_location[0] == row
            for src_start, src_end, vis_start, vis_end, url in links:
                start, end = (src_start, src_end) if raw else (vis_start, vis_end)
                if start <= column < end:
                    return url
            return links[0][4]
        except Exception:
            return None

    def set_markdown(self, enabled: bool) -> None:
        if enabled:
            self._extend_markdown_query()
        try:
            self.language = "markdown" if enabled else None
        except Exception:
            self.language = None

    def _extend_markdown_query(self) -> None:
        # The builtin query leaves fence content on @none and @text.literal,
        # which no TextArea theme styles. Remap to styled captures.
        if getattr(self, "_md_query_extended", False):
            return
        try:
            from textual.widgets._text_area import _HIGHLIGHTS_PATH

            query = (_HIGHLIGHTS_PATH / "markdown.scm").read_text()
            query = query.replace("(code_fence_content) @none", "(code_fence_content) @string")
            query += "\n(language) @keyword\n"
            self.update_highlight_query("markdown", query)
            self._md_query_extended = True
        except Exception:
            pass

    def render_line(self, y: int) -> Strip:
        strip = super().render_line(y)
        try:
            return self._md_preview(y, strip)
        except Exception:
            return strip

    def _md_preview(self, y: int, strip: Strip) -> Strip:
        """Visual-only markdown preview. Source text and coordinates stay
        untouched; the cursor line and any broken syntax render as raw text."""
        if self.language != "markdown" or not self.text or self.show_line_numbers:
            return strip
        _, scroll_y = self.scroll_offset
        info = self.wrapped_document._offset_to_line_info
        y_offset = y + scroll_y
        if y_offset >= len(info):
            return strip
        line_index, section = info[y_offset]
        if section > 0 or len(self.wrapped_document._line_index_to_offsets[line_index]) > 1:
            return strip
        if self.cursor_location[0] == line_index:
            return strip
        selection = self.selection
        if selection.start != selection.end:
            low, high = sorted((selection.start[0], selection.end[0]))
            if low <= line_index <= high:
                return strip
        lines = self.document.lines
        fences = md_render.fence_map(lines)
        if line_index in md_render.fence_interior(fences):
            return strip
        width = strip.cell_length
        if line_index in fences:
            text = md_render.rule_text(width, fences[line_index] or "")
        else:
            transformed = md_render.transform_line(lines[line_index])
            if transformed is None:
                return strip
            if md_render.is_hrule(lines[line_index]):
                transformed = md_render.rule_text(width)
            text = transformed
        base = self.rich_style
        segments = list(text.render(self.app.console))
        return Strip(segments, text.cell_len).adjust_cell_length(width, base).apply_style(base)

    async def _on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            if self.enter_sends:
                self._submit(event)
            else:
                await super()._on_key(event)
            return
        if event.key == "shift+enter":
            if self.enter_sends:
                self._newline(event)
            else:
                self._submit(event)
            return
        await super()._on_key(event)

    def _submit(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()
        self.post_message(self.Submitted())

    def _newline(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()
        self.insert("\n")


class SendBox(Vertical):
    class Send(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class ModeChanged(Message):
        def __init__(self, enter_sends: bool) -> None:
            self.enter_sends = enter_sends
            super().__init__()

    def compose(self):
        yield MessageArea(id="send-input", tab_behavior="focus")
        with Horizontal(id="send-controls"):
            yield Label("⏎ to newline", id="send-nl-label")
            yield Switch(value=True, id="send-enter")
            yield Label("⏎ to send", id="send-send-label")
            yield Button("Clear", id="clear-btn")
            yield Button("Send ▶", id="send-btn", variant="primary")

    def set_enter_sends(self, value: bool) -> None:
        self.query_one("#send-enter", Switch).value = value
        self._apply_mode(value)

    def set_md_highlight(self, value: bool) -> None:
        self.query_one("#send-input", MessageArea).set_markdown(value)

    def set_open_links(self, value: bool) -> None:
        self.query_one("#send-input", MessageArea).open_links = value

    def _apply_mode(self, value: bool) -> None:
        self.query_one("#send-input", MessageArea).enter_sends = value
        off = "#4a4a4a"
        self.query_one("#send-send-label", Label).update(
            "⏎ to send" if value else f"[{off}]⏎ to send[/]"
        )
        self.query_one("#send-nl-label", Label).update(
            f"[{off}]⏎ to newline[/]" if value else "⏎ to newline"
        )

    def trigger_send(self) -> None:
        self.post_message(self.Send(self.query_one("#send-input", TextArea).text))

    def clear(self) -> None:
        self.query_one("#send-input", TextArea).text = ""

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "send-enter":
            self._apply_mode(event.value)
            self.post_message(self.ModeChanged(event.value))

    def on_message_area_submitted(self, event: MessageArea.Submitted) -> None:
        self.trigger_send()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.trigger_send()
        elif event.button.id == "clear-btn":
            self.clear()
