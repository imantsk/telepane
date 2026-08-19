"""Configuration boundary: the only module that reads the environment."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

_APP = "telepane"


def _config_dir() -> Path:
    """~/.config/telepane, honouring XDG_CONFIG_HOME. Env read confined here."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path(os.environ.get("HOME", "~")).expanduser() / ".config"
    return base / _APP


def config_path() -> Path:
    return _config_dir() / "config.json"


def home_dir() -> str:
    """Home path. Env read confined here."""
    return os.environ.get("HOME", "")


@dataclass
class Config:
    enter_sends: bool = True
    confirm_kill: bool = True
    md_highlight: bool = True
    humanize_commands: bool = True
    poll_interval: float = 2.0
    preview_lines: int = 40
    sidebar_width: int = 40
    send_height: int = 10
    theme: str = "textual-dark"
    browser: str = ""
    open_links: bool = True
    update_check: bool = True
    auto_update: bool = True
    screenshot_format: str = "svg"
    screenshot_save_file: bool = True
    screenshot_clipboard: bool = True
    screenshot_dir: str = ""
    tmux_profile: str = "Optimized"
    favorites: list[str] = field(default_factory=list)

    @classmethod
    def load(cls) -> Config:
        path = config_path()
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return cls()
        base = cls()
        out: dict = {}
        for name, default in base.__dict__.items():
            if name not in data:
                continue
            value = data[name]
            try:
                if isinstance(default, bool):
                    value = bool(value)
                elif isinstance(default, int):
                    value = int(value)
                elif isinstance(default, float):
                    value = float(value)
                elif isinstance(default, str):
                    value = str(value)
                elif isinstance(default, list):
                    value = list(value)
            except (ValueError, TypeError):
                continue
            out[name] = value
        return cls(**out)

    def save(self) -> None:
        path = config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2))
        os.replace(tmp, path)
