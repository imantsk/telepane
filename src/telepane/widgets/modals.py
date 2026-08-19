"""Modal dialogs: text prompt, confirm, and help."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView

from .. import agents


class TextPrompt(ModalScreen[Optional[str]]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, initial: str = "") -> None:
        super().__init__()
        self._title = title
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._title, classes="dialog-title")
            yield Input(value=self._initial, id="prompt-input")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("OK", id="ok", variant="primary")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value or None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.dismiss(self.query_one(Input).value or None)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class Confirm(ModalScreen[bool]):
    BINDINGS = [("escape", "no", "No")]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._message, classes="dialog-title")
            with Horizontal(classes="dialog-buttons"):
                yield Button("No", id="no")
                yield Button("Yes", id="yes", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def action_no(self) -> None:
        self.dismiss(False)


class SplitPrompt(ModalScreen[Optional[str]]):
    """Pick what runs in the new pane: the shell, an installed agent CLI, or a
    custom command. Dismisses with the command string ("" = shell), or None."""

    BINDINGS = [("escape", "cancel", "Cancel")]
    SHELL = "shell (default)"

    def __init__(self, *, horizontal: bool) -> None:
        super().__init__()
        self._horizontal = horizontal

    def compose(self) -> ComposeResult:
        arrow = "→" if self._horizontal else "↓"
        with Vertical(id="dialog"):
            yield Label(f"Split {arrow} and run", classes="dialog-title")
            items = [ListItem(Label(self.SHELL), name="")]
            items += [ListItem(Label(name), name=name) for name in agents.installed()]
            yield ListView(*items, id="split-agents")
            yield Input(placeholder="custom command · esc cancels", id="split-command")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is not None:
            self.dismiss(event.item.name or "")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.dismiss(event.value.strip())

    def action_cancel(self) -> None:
        self.dismiss(None)


class Help(ModalScreen[None]):
    BINDINGS = [("escape", "close", "Close"), ("question_mark", "close", "Close")]

    def __init__(self, bindings) -> None:
        super().__init__()
        self._bindings = bindings

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Key bindings", classes="dialog-title")
            with VerticalScroll(id="help-list"):
                for b in self._bindings:
                    key = getattr(b, "key", "")
                    desc = getattr(b, "description", "") or getattr(b, "action", "")
                    yield Label(f"[b]{key:<12}[/] {desc}")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Close", id="close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
