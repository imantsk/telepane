"""telepane: mouse-driven tmux control dashboard."""

from __future__ import annotations

import time
from dataclasses import replace

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.command import DiscoveryHit, Hit, Provider
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Static, Tree

from . import __version__, agents, browser, procname, screenshot, tmux, updates
from .config import Config, home_dir
from .widgets.info import render_server, render_target
from .widgets.modals import Confirm, Help, SplitPrompt, TextPrompt
from .widgets.resizer import Resizer
from .widgets.send_box import MessageArea, SendBox
from .widgets.settings_screen import SettingsScreen
from .widgets.tree import (
    KIND_PANE,
    KIND_SESSION,
    KIND_WINDOW,
    NodeRef,
    build_tree,
    refresh_labels,
)

_MIN_SIDEBAR = 20
_MIN_SEND = 6
_SEND_MAX = 100_000
_UPDATE_MIN_GAP = 600.0
_UPDATE_INTERVAL_MIN = 60


class _MenuCommands(Provider):
    """Command palette entries, fixed order."""

    def _items(self):
        app = self.screen.app
        latest = app._update_latest
        if app._update_ready:
            update_title: object = f"Update · {latest} ready"
            update_help = "Restart telepane to apply"
        elif latest:
            update_title = f"Update to {latest}"
            update_help = "Install the new version"
        else:
            update_title = Text("Update", style="dim")
            update_help = f"Already on latest: v{__version__}"
        return [
            ("Settings", "Open settings", app.action_settings),
            ("Screenshot", "Take a screenshot", app.action_screenshot),
            (update_title, update_help, app.action_update),
            ("Help", "Show key bindings", app.action_help),
            ("Quit", "Quit Telepane", app.action_quit),
        ]

    async def discover(self):
        for title, help_, callback in self._items():
            yield DiscoveryHit(title, callback, help=help_)

    async def search(self, query: str):
        matcher = self.matcher(query)
        for title, help_, callback in self._items():
            text = title if isinstance(title, str) else title.plain
            score = matcher.match(text)
            if score > 0:
                yield Hit(score, matcher.highlight(text), callback, help=help_)


class TelepaneApp(App[None]):
    CSS_PATH = "styles.tcss"
    TITLE = "Telepane"
    COMMANDS = {_MenuCommands}

    BINDINGS = [
        Binding("ctrl+s", "send", "Send"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "new_session", "New"),
        Binding("R", "rename", "Rename"),
        Binding("k", "kill", "Kill"),
        Binding("s", "split_h", "Split →"),
        Binding("v", "split_v", "Split ↓"),
        Binding("p", "screenshot", "Screenshot"),
        Binding("comma", "settings", "Settings"),
        Binding("question_mark", "help", "Help"),
        Binding("f", "focus_tree", "Tree", show=False),
        Binding("i", "focus_input", "Input", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, config: Config | None = None) -> None:
        super().__init__()
        self.config = config or Config.load()
        self.selected: NodeRef | None = None
        self._panes: dict[str, tmux.Pane] = {}
        self._struct: tuple = ()
        self._sizes: tuple = ()
        self._stats_cache = ""
        self._home = home_dir()
        self._picker_arm: str | None = None
        self._pane_window: dict[str, tuple[str, str]] = {}
        self._update_latest: str | None = None
        self._update_ready = False
        self._update_checked_at = 0.0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with VerticalScroll(id="left"):
                yield Tree("tmux", id="tree")
            yield Resizer("#left", key="sidebar", min_size=_MIN_SIDEBAR, id="resizer")
            with Vertical(id="right"):
                yield Static(id="server-stats", classes="panel")
                yield Static(id="target-info", classes="panel")
                with VerticalScroll(id="preview-wrap"):
                    yield Static(id="preview")
                yield Resizer("#sendbox", key="send", axis="y", min_size=_MIN_SEND, id="resizer-y")
                yield SendBox(id="sendbox")
        yield Footer()

    def on_mount(self) -> None:
        if self.config.theme in self.available_themes:
            self.theme = self.config.theme
        self.query_one(SendBox).set_enter_sends(self.config.enter_sends)
        self.query_one(SendBox).set_md_highlight(self.config.md_highlight)
        self.query_one(SendBox).set_open_links(self.config.open_links)
        tree = self.query_one("#tree", Tree)
        tree.guide_depth = 3
        tree.show_root = False
        self.refresh_data()
        self._timer = self.set_interval(self.config.poll_interval, self._tick)
        self.call_after_refresh(self._apply_saved_sizes)
        self._check_updates()
        self._update_timer = self.set_interval(
            max(_UPDATE_INTERVAL_MIN, self.config.update_interval), self._check_updates
        )

    @property
    def _main(self):
        return self.screen_stack[0]

    def apply_config_live(self) -> None:
        """Re-apply saved settings live."""
        send = self._main.query_one(SendBox)
        send.set_enter_sends(self.config.enter_sends)
        send.set_md_highlight(self.config.md_highlight)
        send.set_open_links(self.config.open_links)
        self._clamp_sidebar()
        self._clamp_send_box()
        self._timer.stop()
        self._timer = self.set_interval(self.config.poll_interval, self._tick)
        if hasattr(self, "_update_timer"):
            self._update_timer.stop()
            self._update_timer = self.set_interval(
                max(_UPDATE_INTERVAL_MIN, self.config.update_interval), self._check_updates
            )

    def _apply_saved_sizes(self) -> None:
        self._clamp_sidebar()
        self._clamp_send_box()

    def _clamp_sidebar(self) -> None:
        try:
            widget = self._main.query_one("#left")
        except Exception:
            return
        max_w = max(_MIN_SIDEBAR, self.size.width - _MIN_SIDEBAR)
        widget.styles.width = max(_MIN_SIDEBAR, min(self.config.sidebar_width, max_w))

    def _clamp_send_box(self) -> None:
        try:
            resizer = self._main.query_one("#resizer-y", Resizer)
        except Exception:
            return
        height = max(_MIN_SEND, min(self.config.send_height, resizer.max_height()))
        resizer.apply_height(height)

    def on_mouse_down(self, event) -> None:
        if not getattr(event, "shift", False):
            return
        action = getattr(self.mouse_over, "action", None)
        if action in ("split_h", "split_v"):
            self._picker_arm = action

    def _consume_picker(self, action: str) -> bool:
        armed = self._picker_arm == action
        self._picker_arm = None
        return armed

    def on_resize(self, event) -> None:
        self._clamp_sidebar()
        self._clamp_send_box()

    def on_app_blur(self, event) -> None:
        if hasattr(self, "_timer"):
            self._timer.pause()

    def on_app_focus(self, event) -> None:
        if hasattr(self, "_timer"):
            self._timer.resume()
            self._tick()
        if time.monotonic() - self._update_checked_at > _UPDATE_MIN_GAP:
            self._check_updates()

    def on_resizer_committed(self, event: Resizer.Committed) -> None:
        if event.key == "sidebar":
            self.config.sidebar_width = event.size
        elif event.key == "send":
            resizer = self.query_one("#resizer-y", Resizer)
            maxed = event.size >= resizer.max_height()
            self.config.send_height = _SEND_MAX if maxed else event.size
        self.config.save()

    # ── data ─────────────────────────────────────────────────────────────

    @staticmethod
    def _struct_sig(sessions: list[tmux.Session]) -> tuple:
        return tuple(
            (
                s.id,
                s.name,
                s.attached,
                tuple(
                    (w.id, w.name, w.active, tuple((p.id, p.command, p.active) for p in w.panes))
                    for w in s.windows
                ),
            )
            for s in sessions
        )

    @staticmethod
    def _size_sig(sessions: list[tmux.Session]) -> tuple:
        return tuple(
            (p.id, p.width, p.height) for s in sessions for w in s.windows for p in w.panes
        )

    def _gather(self):
        """All blocking tmux reads for one refresh."""
        sessions = tmux.snapshot()
        if self.config.humanize_commands:
            self._humanize(sessions)
        info = tmux.server_info(sessions)
        preview = None
        if self.selected is not None:
            try:
                preview = tmux.capture_pane(self.selected.send_target)
            except tmux.TmuxError:
                preview = ""
        return sessions, info, preview

    @staticmethod
    def _humanize(sessions: list[tmux.Session]) -> None:
        names = procname.foreground_names()
        if not names:
            return
        for s in sessions:
            for w in s.windows:
                for i, p in enumerate(w.panes):
                    name = names.get(p.tty)
                    if name and name != p.command:
                        w.panes[i] = replace(p, command=name)

    def refresh_data(self) -> None:
        try:
            data = self._gather()
        except Exception:
            return
        self._render(*data, force=True)

    @work(exclusive=True, thread=True)
    def _poll(self) -> None:
        try:
            data = self._gather()
        except Exception:
            return
        self.call_from_thread(self._render, *data)

    def _tick(self) -> None:
        self._poll()

    def _render(self, sessions, info, preview, *, force: bool = False) -> None:
        try:
            tree: Tree[NodeRef] = self.query_one("#tree", Tree)
            struct = self._struct_sig(sessions)
            if force or struct != self._struct:
                self._panes = {p.id: p for s in sessions for w in s.windows for p in w.panes}
                self._pane_window = {
                    p.id: (w.id, w.name) for s in sessions for w in s.windows for p in w.panes
                }
                if sessions:
                    build_tree(tree, sessions)
                else:
                    tree.clear()
                self._struct = struct
                self._sizes = self._size_sig(sessions)
                self._refresh_target()
            elif (size := self._size_sig(sessions)) != self._sizes:
                self._panes = {p.id: p for s in sessions for w in s.windows for p in w.panes}
                refresh_labels(tree, sessions)
                self._sizes = size
                self._refresh_target()
            stats = render_server(info)
            if stats != self._stats_cache:
                self.query_one("#server-stats", Static).update(stats)
                self._stats_cache = stats
            self._set_preview(preview)
        except Exception:
            pass

    def _set_preview(self, text: str | None) -> None:
        try:
            widget = self.query_one("#preview", Static)
        except Exception:
            return
        if not self.selected:
            widget.update("[dim]No target is selected.[/]")
        elif text is None:
            widget.update("[dim]target unavailable[/]")
        else:
            tail = "\n".join(text.splitlines()[-self.config.preview_lines :])
            widget.update(tail or "[dim](empty pane)[/]")

    def _refresh_target(self) -> None:
        info = self.query_one("#target-info", Static)
        pane = self._panes.get(self.selected.send_target) if self.selected else None
        info.update(
            render_target(self.selected, pane, width=info.size.width or 80, home=self._home)
        )
        self.call_after_refresh(self._clamp_send_box)

    def _refresh_preview(self) -> None:
        if not self.selected:
            self._set_preview(None)
            return
        try:
            self._set_preview(tmux.capture_pane(self.selected.send_target))
        except tmux.TmuxError:
            self._set_preview(None)

    # ── events ───────────────────────────────────────────────────────────

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        ref = event.node.data
        if isinstance(ref, NodeRef):
            self.selected = ref
            self._refresh_target()
            self._refresh_preview()

    def on_send_box_send(self, event: SendBox.Send) -> None:
        if self.selected is None:
            self.notify("Select a pane in the tree first.", severity="warning")
            return
        if not event.text:
            self.notify("The message is empty.", severity="warning")
            return
        try:
            tmux.send_text(self.selected.send_target, event.text, enter=True)
        except Exception as exc:
            self.notify(f"Cannot send: {exc}", severity="error")
            return
        self.notify(f"Message sent to {self.selected.send_target}.")
        self.query_one(SendBox).clear()
        self.set_timer(0.15, self._refresh_preview)

    def on_message_area_link_clicked(self, event: MessageArea.LinkClicked) -> None:
        self._open_link(event.url)

    @work(thread=True)
    def _open_link(self, url: str) -> None:
        try:
            browser.open_url(url, self.config.browser)
        except Exception as exc:
            self.call_from_thread(self.notify, f"Cannot open the link: {exc}", severity="error")
            return
        self.call_from_thread(self.notify, f"Opened {url}")

    def on_send_box_mode_changed(self, event: SendBox.ModeChanged) -> None:
        self.config.enter_sends = event.enter_sends
        self.config.save()

    # ── updates ──────────────────────────────────────────────────────────

    @work(thread=True)
    def _check_updates(self) -> None:
        if not self.config.update_check:
            return
        self._update_checked_at = time.monotonic()
        latest = updates.latest_version()
        if latest is None or not updates.is_newer(latest, __version__):
            return
        self._update_latest = latest
        self.call_from_thread(self._show_update_notice, f"⬆ {latest}")
        if not self.config.auto_update:
            return
        self._install(latest)

    def _install(self, latest: str) -> None:
        if updates.upgrade():
            self._update_ready = True
            self.call_from_thread(self._show_update_notice, f"⬆ {latest} ready · restart")
            self.call_from_thread(self.notify, f"Updated to {latest}. Restart telepane.")
        else:
            self.call_from_thread(
                self.notify, f"Cannot auto-update to {latest}.", severity="warning"
            )

    @work(thread=True)
    def _install_worker(self, latest: str) -> None:
        self._install(latest)

    def action_update(self) -> None:
        if self._update_ready:
            self.notify(f"{self._update_latest} is installed. Restart telepane.")
            return
        if self._update_latest:
            self.notify(f"Updating to {self._update_latest}...")
            self._install_worker(self._update_latest)
            return
        self.notify(f"telepane {__version__} is the latest version.")

    def _show_update_notice(self, text: str) -> None:
        header = self.query_one(Header)
        try:
            notice = header.query_one("#update-notice", Static)
        except Exception:
            notice = Static(text, id="update-notice")
            header.mount(notice)
            return
        notice.update(text)

    # ── actions ──────────────────────────────────────────────────────────

    def action_send(self) -> None:
        self.query_one(SendBox).trigger_send()

    def action_refresh(self) -> None:
        self.refresh_data()

    def action_focus_tree(self) -> None:
        self.query_one("#tree", Tree).focus()

    def action_focus_input(self) -> None:
        self.query_one("#send-input").focus()

    def action_new_session(self) -> None:
        def done(name: str | None) -> None:
            if not name:
                return
            try:
                tmux.new_session(name)
            except tmux.TmuxError as exc:
                self.notify(f"Cannot create the session: {exc}", severity="error")
                return
            self.refresh_data()

        self.push_screen(TextPrompt("New session name"), done)

    def action_rename(self) -> None:
        """Rename the selected window, or the window of the selected pane."""
        ref = self.selected
        if ref is None:
            self.notify("Select a window or a pane first.", severity="warning")
            return
        if ref.kind == KIND_PANE:
            found = self._pane_window.get(ref.target)
            if found is None:
                self.notify("Cannot find the window of this pane.", severity="warning")
                return
            window_id, window_name = found
        else:
            window_id, window_name = ref.target, ref.label

        def done(name: str | None) -> None:
            if not name:
                return
            try:
                tmux.rename_window(window_id, name)
            except tmux.TmuxError as exc:
                self.notify(f"Cannot rename: {exc}", severity="error")
                return
            self.refresh_data()

        self.push_screen(TextPrompt(f"Rename window {window_name}", window_name), done)

    def action_kill(self) -> None:
        ref = self.selected
        if ref is None:
            self.notify("No target is selected.", severity="warning")
            return

        def do_kill() -> None:
            try:
                if ref.kind == KIND_SESSION:
                    tmux.kill_session(ref.target)
                elif ref.kind == KIND_WINDOW:
                    tmux.kill_window(ref.target)
                else:
                    tmux.kill_pane(ref.target)
            except tmux.TmuxError as exc:
                self.notify(f"Cannot kill: {exc}", severity="error")
                return
            self.selected = None
            self.refresh_data()

        if self.config.confirm_kill:

            def confirmed(yes: bool) -> None:
                if yes:
                    do_kill()

            self.push_screen(Confirm(f"Kill {ref.kind} {ref.label}?"), confirmed)
        else:
            do_kill()

    def _target_path(self) -> str:
        if self.selected is None:
            return ""
        pane = self._panes.get(self.selected.send_target)
        return pane.path if pane else ""

    def _split(
        self, horizontal: bool, command: str | None = None, start_dir: str | None = None
    ) -> None:
        if self.selected is None:
            self.notify("No target is selected.", severity="warning")
            return
        try:
            tmux.split_window(
                self.selected.send_target,
                horizontal=horizontal,
                command=command,
                start_dir=start_dir or self._target_path() or None,
            )
        except tmux.TmuxError as exc:
            self.notify(f"Cannot split: {exc}", severity="error")
            return
        self.refresh_data()

    def _split_picker(self, horizontal: bool) -> None:
        if self.selected is None:
            self.notify("No target is selected.", severity="warning")
            return

        def done(result: tuple | None) -> None:
            if result is None:
                return
            kind, value, yolo, path = result
            if kind == "agent":
                self._split_agent(value, horizontal=horizontal, yolo=yolo, start_dir=path)
            else:
                self._split(horizontal, command=value or None, start_dir=path)

        self.push_screen(
            SplitPrompt(horizontal=horizontal, path=self._target_path(), home=self._home), done
        )

    @work(thread=True)
    def _split_agent(self, name: str, *, horizontal: bool, yolo: bool, start_dir: str) -> None:
        command = name
        if yolo:
            flag = agents.bypass_flag(name)
            if flag:
                command = f"{name} {flag}"
        self.call_from_thread(self._split, horizontal, command, start_dir)

    def action_split_h(self) -> None:
        if self._consume_picker("split_h"):
            self._split_picker(horizontal=True)
            return
        self._split(horizontal=True)

    def action_split_v(self) -> None:
        if self._consume_picker("split_v"):
            self._split_picker(horizontal=False)
            return
        self._split(horizontal=False)

    def action_settings(self) -> None:
        self.push_screen(SettingsScreen(self.config))

    def action_help(self) -> None:
        self.push_screen(Help(self.BINDINGS))

    def action_screenshot(self) -> None:
        preview = ""
        if self.selected:
            try:
                preview = tmux.capture_pane(self.selected.send_target)
            except tmux.TmuxError:
                preview = ""
        try:
            svg = self.export_screenshot()
        except Exception as exc:
            self.notify(f"Cannot take the screenshot: {exc}", severity="error")
            return
        self._deliver_screenshot(svg, preview)

    @work(thread=True)
    def _deliver_screenshot(self, svg: str, preview: str) -> None:
        msg = screenshot.deliver(svg, preview, self.config, home=self._home)
        self.call_from_thread(self.notify, msg)
