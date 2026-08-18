"""Screenshot capture: SVG, PNG (optional cairosvg), or MD; save and/or clipboard."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from . import clipboard
from .config import Config


def _dest_dir(config: Config, home: str) -> Path:
    return Path(config.screenshot_dir) if config.screenshot_dir else Path(home or ".")


def deliver(svg: str, preview: str, config: Config, *, home: str, stamp: str = "") -> str:
    fmt = config.screenshot_format
    stamp = stamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    path = _dest_dir(config, home) / f"telepane-{stamp}.{fmt}"

    data: bytes
    if fmt == "png":
        try:
            import cairosvg
        except ImportError:
            return "PNG needs the cairosvg package. Install it, or use svg or md."
        data = cairosvg.svg2png(bytestring=svg.encode())
    elif fmt == "md":
        data = f"```\n{preview}\n```\n".encode()
    else:
        data = svg.encode()

    need_file = config.screenshot_save_file or (config.screenshot_clipboard and fmt == "png")
    if need_file:
        try:
            path.write_bytes(data)
        except OSError as exc:
            return f"Cannot save the screenshot: {exc}"

    copied = False
    if config.screenshot_clipboard:
        copied = (
            clipboard.copy_file(str(path))
            if need_file
            else clipboard.copy_text(data.decode(errors="replace"))
        )

    parts = []
    if need_file:
        parts.append(f"Saved {path.name}")
    if copied:
        parts.append("Copied to clipboard")
    return " · ".join(parts) if parts else "Nothing to do. Enable Save file or Copy to clipboard."
