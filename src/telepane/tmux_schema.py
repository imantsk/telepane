"""tmux config schema and profiles. Scopes: session `-g`, server `-s`, window `-gw`."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Opt:
    name: str  # tmux option name
    label: str
    type: str  # bool | choice | number | text | color
    scope: str = "session"
    choices: tuple[str, ...] = ()
    default: str = ""


CATEGORIES: dict[str, list[Opt]] = {
    "General": [
        Opt("mouse", "Mouse support", "bool", "session", default="off"),
        Opt("base-index", "First window index", "number", "session", default="0"),
        Opt("renumber-windows", "Renumber windows on close", "bool", "session", default="off"),
        Opt("history-limit", "Scrollback lines", "number", "session", default="2000"),
        Opt("repeat-time", "Repeat time (ms)", "number", "session", default="500"),
        Opt("display-time", "Message time (ms)", "number", "session", default="750"),
        Opt(
            "set-clipboard",
            "System clipboard",
            "choice",
            "session",
            choices=("on", "off", "external"),
            default="external",
        ),
        Opt(
            "status-keys",
            "Command-prompt keys",
            "choice",
            "session",
            choices=("emacs", "vi"),
            default="emacs",
        ),
        Opt(
            "default-terminal",
            "Default terminal",
            "choice",
            "session",
            choices=("tmux-256color", "screen-256color", "xterm-256color"),
            default="screen-256color",
        ),
    ],
    "Server": [
        Opt("escape-time", "Escape time (ms)", "number", "server", default="500"),
        Opt("focus-events", "Focus events", "bool", "server", default="off"),
        Opt("exit-empty", "Exit when no sessions", "bool", "server", default="on"),
        Opt(
            "extended-keys",
            "Extended keys",
            "choice",
            "server",
            choices=("off", "on", "always"),
            default="off",
        ),
    ],
    "Window": [
        Opt("pane-base-index", "First pane index", "number", "window", default="0"),
        Opt(
            "mode-keys",
            "Copy-mode keys",
            "choice",
            "window",
            choices=("emacs", "vi"),
            default="emacs",
        ),
        Opt("aggressive-resize", "Aggressive resize", "bool", "window", default="off"),
        Opt("automatic-rename", "Automatic window rename", "bool", "window", default="on"),
        Opt("monitor-activity", "Monitor activity", "bool", "window", default="off"),
        Opt(
            "clock-mode-style",
            "Clock style",
            "choice",
            "window",
            choices=("12", "24"),
            default="24",
        ),
        Opt("clock-mode-colour", "Clock colour", "color", "window", default="blue"),
    ],
    "Status bar": [
        Opt("status", "Show status bar", "choice", "session", choices=("on", "off"), default="on"),
        Opt(
            "status-position",
            "Position",
            "choice",
            "session",
            choices=("top", "bottom"),
            default="bottom",
        ),
        Opt(
            "status-justify",
            "Window list align",
            "choice",
            "session",
            choices=("left", "centre", "right"),
            default="left",
        ),
        Opt("status-interval", "Refresh interval (s)", "number", "session", default="15"),
        Opt("status-left-length", "Left length", "number", "session", default="10"),
        Opt("status-right-length", "Right length", "number", "session", default="40"),
        Opt("status-left", "Left text", "text", "session"),
        Opt("status-right", "Right text", "text", "session"),
    ],
    "Alerts": [
        Opt(
            "visual-activity",
            "Visual activity",
            "choice",
            "session",
            choices=("on", "off", "both"),
            default="off",
        ),
        Opt(
            "visual-bell",
            "Visual bell",
            "choice",
            "session",
            choices=("on", "off", "both"),
            default="off",
        ),
        Opt(
            "visual-silence",
            "Visual silence",
            "choice",
            "session",
            choices=("on", "off", "both"),
            default="off",
        ),
        Opt(
            "bell-action",
            "Bell action",
            "choice",
            "session",
            choices=("none", "any", "current", "other"),
            default="other",
        ),
    ],
}


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    options: list[tuple[str, str, str]] = field(default_factory=list)  # (name, value, scope)


PROFILES: list[Profile] = [
    Profile("Optimized", "Your current ~/.tmux.conf"),
    Profile(
        "Sensible",
        "tmux-plugins/tmux-sensible: safe baseline",
        [
            ("escape-time", "0", "server"),
            ("history-limit", "50000", "session"),
            ("display-time", "4000", "session"),
            ("status-interval", "5", "session"),
            ("status-keys", "emacs", "session"),
            ("focus-events", "on", "server"),
            ("aggressive-resize", "on", "window"),
        ],
    ),
    Profile(
        "Oh My Tmux",
        "gpakosz/.tmux: batteries included",
        [
            ("escape-time", "10", "server"),
            ("repeat-time", "600", "session"),
            ("focus-events", "on", "server"),
            ("history-limit", "5000", "session"),
            ("base-index", "1", "session"),
            ("pane-base-index", "1", "window"),
            ("renumber-windows", "on", "session"),
            ("automatic-rename", "on", "window"),
            ("status-interval", "10", "session"),
            ("monitor-activity", "on", "window"),
            ("visual-activity", "off", "session"),
        ],
    ),
    Profile(
        "Vi / Power",
        "dreamsofcode-io style: vi-centric",
        [
            ("mouse", "on", "session"),
            ("base-index", "1", "session"),
            ("pane-base-index", "1", "window"),
            ("renumber-windows", "on", "session"),
            ("mode-keys", "vi", "window"),
            ("status-keys", "vi", "session"),
            ("set-clipboard", "on", "session"),
            ("default-terminal", "tmux-256color", "session"),
            ("escape-time", "0", "server"),
            ("history-limit", "100000", "session"),
            ("focus-events", "on", "server"),
        ],
    ),
    Profile(
        "Minimal",
        "Mouse-friendly beginner setup",
        [
            ("mouse", "on", "session"),
            ("base-index", "1", "session"),
            ("pane-base-index", "1", "window"),
            ("status-position", "bottom", "session"),
            ("renumber-windows", "on", "session"),
        ],
    ),
    Profile("Custom", "Manually changed after applying a profile"),
]

CUSTOM = "Custom"


# tmux named colours → an approximate hex for the swatch preview.
COLORS: list[tuple[str, str]] = [
    ("default", ""),
    ("black", "#2e3436"),
    ("red", "#cc0000"),
    ("green", "#4e9a06"),
    ("yellow", "#c4a000"),
    ("blue", "#3465a4"),
    ("magenta", "#75507b"),
    ("cyan", "#06989a"),
    ("white", "#d3d7cf"),
    ("brightblack", "#555753"),
    ("brightred", "#ef2929"),
    ("brightgreen", "#8ae234"),
    ("brightyellow", "#fce94f"),
    ("brightblue", "#729fcf"),
    ("brightmagenta", "#ad7fa8"),
    ("brightcyan", "#34e2e2"),
    ("brightwhite", "#eeeeec"),
]
