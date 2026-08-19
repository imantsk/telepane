"""Full-screen settings view: subsection sidebar + field list."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, ListItem, ListView, RadioButton, RadioSet, Switch

from .. import __version__, browser, tmux
from ..config import Config
from ..tmux_schema import CATEGORIES, COLORS, CUSTOM, PROFILES, Opt

_TELEPANE = "Telepane"
_APP_SUBSECTIONS = [_TELEPANE, "Theme", "Screenshot"]

_FREQ_PRESETS = {"1d": 86400, "1h": 3600, "15m": 900}
_FREQ_CUSTOM = "custom"
_HHMM = re.compile(r"^(\d{1,3})(?::([0-5]?\d))?$")


def _hhmm_to_seconds(value: str) -> int:
    match = _HHMM.match(value.strip())
    if match is None:
        raise ValueError("needs hh:mm, for example 2:30")
    seconds = int(match[1]) * 3600 + int(match[2] or 0) * 60
    if not 60 <= seconds <= 604800:
        raise ValueError("needs 0:01 to 168:00")
    return seconds


def _seconds_to_hhmm(seconds: int) -> str:
    return f"{seconds // 3600}:{(seconds % 3600) // 60:02d}"


def _int_in(value, lo: int, hi: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (ValueError, TypeError):
        raise ValueError(f"needs a whole number {lo}-{hi}") from None
    if not lo <= parsed <= hi:
        raise ValueError(f"needs a whole number {lo}-{hi}")
    return parsed


def _float_in(value, lo: float, hi: float) -> float:
    try:
        parsed = float(str(value).strip())
    except (ValueError, TypeError):
        raise ValueError(f"needs a number {lo}-{hi}") from None
    if not lo <= parsed <= hi:
        raise ValueError(f"needs a number {lo}-{hi}")
    return parsed


_GROUP = {"bool": 0, "choice": 1, "color": 1, "text": 2, "number": 3}


def _swatch(name: str, hex_: str) -> str:
    return f"[on {hex_}]  [/] {name}" if hex_ else f"[dim]▨[/] {name}"


class SettingsScreen(Screen):
    BINDINGS = [("escape", "back", "Back")]

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self._apply: dict[str, Callable[[object], None]] = {}
        self._section = _TELEPANE
        self._opts: dict[str, dict[str, str]] = {}

    def compose(self) -> ComposeResult:
        with Horizontal(id="settings-topbar"):
            yield Button("[<]", id="settings-back")
            yield Label("Settings", id="settings-title")
        with Horizontal(id="settings-body"):
            items = [ListItem(Label(s), name=s) for s in self._sections()]
            yield ListView(*items, id="settings-nav")
            yield VerticalScroll(id="settings-fields")
        yield Label(f"telepane {__version__}", id="settings-version")

    def _sections(self) -> list[str]:
        return [*_APP_SUBSECTIONS, *CATEGORIES.keys()]

    def on_mount(self) -> None:
        for scope in ("session", "server", "window"):
            self._opts[scope] = tmux.show_all_options(scope)
        self._show_section(self._section)

    # ── navigation ────────────────────────────────────────────────────────

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item is not None and event.item.name:
            self._show_section(event.item.name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings-back":
            self.action_back()

    def action_back(self) -> None:
        self.app.pop_screen()

    # ── field building ──────────────────────────────────────────────────────

    def _show_section(self, section: str) -> None:
        self._section = section
        self._apply.clear()
        fields = self.query_one("#settings-fields", VerticalScroll)
        fields.remove_children()
        specs = sorted(self._section_fields(section), key=lambda gw: gw[0])
        if specs:
            fields.mount(*[w for _, w in specs])

    def _section_fields(self, section: str):
        if section == _TELEPANE:
            yield from self._telepane_fields()
        elif section == "Theme":
            yield self._theme_field()
        elif section == "Screenshot":
            yield from self._screenshot_fields()
        elif section in CATEGORIES:
            for opt in CATEGORIES[section]:
                yield self._opt_field(opt)

    def _bool(self, key: str, label: str, value: bool, setter: Callable[[bool], None]):
        wid = f"f-{key}"
        self._apply[wid] = setter  # type: ignore[assignment]
        row = Horizontal(Switch(value=value, id=wid), Label(label), classes="setting-row")
        return (_GROUP["bool"], row)

    def _choice(
        self,
        key: str,
        label: str,
        choices,
        value: str,
        setter: Callable[[str], None],
        *,
        swatch: bool = False,
    ):
        wid = f"f-{key}"
        self._apply[wid] = setter  # type: ignore[assignment]
        buttons = []
        for c in choices:
            text = _swatch(*c) if swatch else str(c)
            val = c[0] if swatch else c
            buttons.append(RadioButton(text, value=(val == value), name=str(val)))
        block = VerticalScroll(
            Label(label, classes="field-label"), RadioSet(*buttons, id=wid), classes="field-block"
        )
        return (_GROUP["color" if swatch else "choice"], block)

    def _textnum(
        self, key: str, label: str, value, setter: Callable[[str], None], *, numeric: bool = False
    ):
        wid = f"f-{key}"
        self._apply[wid] = setter  # type: ignore[assignment]
        inp = Input(value=str(value), id=wid, type="number" if numeric else "text")
        block = VerticalScroll(Label(label, classes="field-label"), inp, classes="field-block")
        return (_GROUP["number" if numeric else "text"], block)

    # ── sections ──────────────────────────────────────────────────────────

    def _telepane_fields(self):
        c = self.config
        yield self._profile_field()
        yield self._browser_field()
        yield self._bool(
            "enter_sends",
            "Enter sends (off: newline)",
            c.enter_sends,
            lambda v: self._set_cfg("enter_sends", v),
        )
        yield self._bool(
            "confirm_kill",
            "Confirm before kill",
            c.confirm_kill,
            lambda v: self._set_cfg("confirm_kill", v),
        )
        yield self._bool(
            "md_highlight",
            "Markdown highlight in input",
            c.md_highlight,
            lambda v: self._set_cfg("md_highlight", v),
        )
        yield self._bool(
            "humanize_commands",
            "Humanize pane commands",
            c.humanize_commands,
            lambda v: self._set_cfg("humanize_commands", v),
        )
        yield self._bool(
            "open_links",
            "Shift+Click opens links",
            c.open_links,
            lambda v: self._set_cfg("open_links", v),
        )
        yield self._bool(
            "update_check",
            "Check for updates",
            c.update_check,
            lambda v: self._set_cfg("update_check", v),
        )
        yield self._bool(
            "auto_update",
            "Auto update",
            c.auto_update,
            lambda v: self._set_cfg("auto_update", v),
        )
        current = next(
            (label for label, secs in _FREQ_PRESETS.items() if secs == c.update_interval),
            _FREQ_CUSTOM,
        )
        yield self._choice(
            "update_interval",
            "Update check frequency",
            [*_FREQ_PRESETS, _FREQ_CUSTOM],
            current,
            self._set_frequency,
        )
        yield self._textnum(
            "update_interval_custom",
            "Custom frequency (hh:mm)",
            "" if current != _FREQ_CUSTOM else _seconds_to_hhmm(c.update_interval),
            self._set_frequency_custom,
        )
        yield self._textnum(
            "poll_interval",
            "Refresh interval (s)",
            c.poll_interval,
            lambda v: self._set_cfg("poll_interval", _float_in(v, 0.5, 3600)),
            numeric=True,
        )
        yield self._textnum(
            "preview_lines",
            "Preview lines",
            c.preview_lines,
            lambda v: self._set_cfg("preview_lines", _int_in(v, 1, 10000)),
            numeric=True,
        )
        yield self._textnum(
            "sidebar_width",
            "Sidebar width",
            c.sidebar_width,
            lambda v: self._set_cfg("sidebar_width", _int_in(v, 20, 500)),
            numeric=True,
        )
        yield self._textnum(
            "send_height",
            "Send box height",
            c.send_height,
            lambda v: self._set_cfg("send_height", _int_in(v, 1, 100000)),
            numeric=True,
        )

    def _set_frequency(self, value) -> None:
        label = str(value)
        if label == _FREQ_CUSTOM:
            raw = self.query_one("#f-update_interval_custom", Input).value
            if not raw.strip():
                raise ValueError("type a custom hh:mm first")
            self._set_cfg("update_interval", _hhmm_to_seconds(raw))
            return
        self._set_cfg("update_interval", _FREQ_PRESETS[label])
        custom = self.query_one("#f-update_interval_custom", Input)
        custom.value = ""

    def _set_frequency_custom(self, value) -> None:
        self._set_cfg("update_interval", _hhmm_to_seconds(str(value)))
        self._press_radio("f-update_interval", _FREQ_CUSTOM)

    def _press_radio(self, wid: str, name: str) -> None:
        radio_set = self.query_one(f"#{wid}", RadioSet)
        with radio_set.prevent(RadioSet.Changed):
            for button in radio_set.query(RadioButton):
                button.value = button.name == name

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "f-update_interval_custom" and event.value.strip():
            self._press_radio("f-update_interval", _FREQ_CUSTOM)

    def _browser_field(self):
        options = browser.installed()
        current = self.config.browser or browser.SYSTEM
        if current not in options:
            options.append(current)
        return self._choice(
            "browser",
            "Link browser",
            options,
            current,
            lambda v: self._set_cfg("browser", "" if v == browser.SYSTEM else v),
        )

    def _theme_field(self):
        themes = list(self.app.available_themes)
        return self._choice("theme", "Theme", themes, self.config.theme, self._set_theme)

    def _valid_dir(self, value) -> str:
        raw = str(value).strip()
        if not raw:
            return ""
        path = raw.replace("~", str(self.app._home), 1) if raw.startswith("~") else raw
        if not Path(path).is_dir():
            raise ValueError("needs an existing directory, or blank for home")
        return raw

    def _screenshot_fields(self):
        c = self.config
        yield self._bool(
            "screenshot_save_file",
            "Save file",
            c.screenshot_save_file,
            lambda v: self._set_cfg("screenshot_save_file", v),
        )
        yield self._bool(
            "screenshot_clipboard",
            "Copy to clipboard",
            c.screenshot_clipboard,
            lambda v: self._set_cfg("screenshot_clipboard", v),
        )
        yield self._choice(
            "screenshot_format",
            "Format",
            ("svg", "png", "md"),
            c.screenshot_format,
            lambda v: self._set_cfg("screenshot_format", v),
        )
        yield self._textnum(
            "screenshot_dir",
            "Save directory (blank = home)",
            c.screenshot_dir,
            lambda v: self._set_cfg("screenshot_dir", self._valid_dir(v)),
        )

    def _profile_field(self):
        names = [p.name for p in PROFILES]
        return self._choice(
            "tmux_profile", "Profile", names, self.config.tmux_profile, self._apply_profile
        )

    def _opt_field(self, opt: Opt):
        current = self._opts.get(opt.scope, {}).get(opt.name) or opt.default
        if opt.type == "bool":
            return self._bool(
                opt.name,
                opt.label,
                current in ("on", "1", "yes"),
                lambda v, o=opt: self._set_tmux(o, "on" if v else "off"),
            )
        if opt.type == "choice":
            return self._choice(
                opt.name, opt.label, opt.choices, current, lambda v, o=opt: self._set_tmux(o, v)
            )
        if opt.type == "color":
            return self._choice(
                opt.name,
                opt.label,
                COLORS,
                current,
                lambda v, o=opt: self._set_tmux(o, v),
                swatch=True,
            )
        if opt.type == "number":
            return self._textnum(
                opt.name,
                opt.label,
                current,
                lambda v, o=opt: self._set_tmux(o, str(_int_in(v, 0, 10_000_000))),
                numeric=True,
            )
        return self._textnum(
            opt.name,
            opt.label,
            current,
            lambda v, o=opt: self._set_tmux(o, str(v).strip()),
        )

    # ── apply ───────────────────────────────────────────────────────────--

    def _set_cfg(self, attr: str, value) -> None:
        setattr(self.config, attr, value)
        self.config.save()
        self.app.apply_config_live()

    def _set_theme(self, value: str) -> None:
        self.config.theme = value
        self.config.save()
        self.app.theme = value

    def _set_tmux(self, opt: Opt, value: str) -> None:
        try:
            tmux.set_option(opt.name, value, scope=opt.scope)
        except tmux.TmuxError as exc:
            self.notify(f"{opt.name} failed: {exc}", severity="error")
            return
        if self.config.tmux_profile != CUSTOM:
            self.config.tmux_profile = CUSTOM
        self.config.save()

    def _apply_profile(self, name: str) -> None:
        profile = next((p for p in PROFILES if p.name == name), None)
        if profile is None or name == CUSTOM:
            return
        try:
            if name == "Optimized":
                conf = Path(self.app._home or "~").expanduser() / ".tmux.conf"
                tmux.source_file(str(conf))
            else:
                for opt_name, value, scope in profile.options:
                    tmux.set_option(opt_name, value, scope=scope)
        except tmux.TmuxError as exc:
            self.notify(f"profile failed: {exc}", severity="error")
            return
        self.config.tmux_profile = name
        self.config.save()
        self.notify(f"applied {name} profile")

    # ── change events ─────────────────────────────────────────────────────

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self._dispatch(event.switch.id, event.value)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.pressed is not None:
            self._dispatch(event.radio_set.id, event.pressed.name)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._dispatch(event.input.id, event.value)

    def _dispatch(self, wid: str | None, value) -> None:
        setter = self._apply.get(wid or "")
        if setter is None:
            return
        try:
            setter(value)
        except (ValueError, TypeError) as exc:
            self.notify(str(exc) or "invalid value", severity="warning")
