"""Send box. `enter_sends`: True → Enter sends / Shift+Enter newline; False → the
reverse."""

from __future__ import annotations

from textual import events
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Label, Switch, TextArea


class MessageArea(TextArea):
    enter_sends: bool = True

    class Submitted(Message):
        pass

    def set_markdown(self, enabled: bool) -> None:
        try:
            self.language = "markdown" if enabled else None
        except Exception:
            self.language = None

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
