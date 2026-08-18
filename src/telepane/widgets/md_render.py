"""Live-preview transforms for completed markdown syntax in the send box."""

from __future__ import annotations

import re

from rich.style import Style
from rich.text import Text

RULE_CHAR = "─"

_FENCE = re.compile(r"^```(\S*)\s*$")
_HEADING = re.compile(r"^(#{1,6}) (.+)$")
_HRULE = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
_INLINE = re.compile(
    r"\*\*(?P<bold>.+?)\*\*"
    r"|__(?P<und>.+?)__"
    r"|(?<!\*)\*(?P<ital>[^*\s](?:[^*]*[^*\s])?)\*(?!\*)"
    r"|(?<!_)_(?P<ital2>[^_\s](?:[^_]*[^_\s])?)_(?!_)"
    r"|~~(?P<strike>.+?)~~"
    r"|`(?P<code>[^`]+)`"
    r"|\[(?P<ltext>[^\]]+)\]\((?P<lurl>[^)\s]+)\)"
)

_STYLES = {
    "bold": Style(bold=True),
    "und": Style(underline=True),
    "ital": Style(italic=True),
    "ital2": Style(italic=True),
    "strike": Style(strike=True),
    "code": Style(bgcolor="#3a3a3a", color="#e8e8e8"),
    "ltext": Style(underline=True, color="#6db2ff"),
}
_HEADING_STYLE = Style(bold=True)
RULE_STYLE = Style(color="#6a6a6a")


def fence_map(lines: list[str]) -> dict[int, str | None]:
    """Map delimiter line index to its info tag for complete fences.

    The opening line maps to the tag string, the closing line to None. An
    unclosed fence adds nothing, so a deleted closing backtick reverts the
    whole block to plain rendering.
    """
    out: dict[int, str | None] = {}
    open_at: int | None = None
    tag = ""
    for i, line in enumerate(lines):
        match = _FENCE.match(line)
        if match is None:
            continue
        if open_at is None:
            open_at, tag = i, match.group(1)
        else:
            out[open_at] = tag
            out[i] = None
            open_at = None
    return out


def fence_interior(fences: dict[int, str | None]) -> set[int]:
    """Line indexes between complete fence delimiters."""
    interior: set[int] = set()
    delimiters = sorted(fences)
    for start, end in zip(delimiters[0::2], delimiters[1::2]):
        interior.update(range(start + 1, end))
    return interior


def rule_text(width: int, label: str = "") -> Text:
    """A horizontal rule, with the fence language tag inset when present."""
    if label:
        body = f"{RULE_CHAR * 2} {label} "
        body += RULE_CHAR * max(0, width - len(body))
    else:
        body = RULE_CHAR * width
    return Text(body[:width], style=RULE_STYLE, end="")


def transform_line(line: str) -> Text | None:
    """Render one completed-markdown line, or None when nothing applies."""
    heading = _HEADING.match(line)
    if heading:
        return Text(heading.group(2), style=_HEADING_STYLE, end="")
    if _HRULE.match(line):
        return Text("", end="")  # caller draws the rule at full width
    out = Text(end="")
    last = 0
    for match in _INLINE.finditer(line):
        out.append(line[last : match.start()])
        if match.group("ltext") is not None:
            out.append(match.group("ltext"), style=_STYLES["ltext"])
        else:
            name = str(match.lastgroup)
            out.append(match.group(name), style=_STYLES[name])
        last = match.end()
    if last == 0:
        return None
    out.append(line[last:])
    return out


def is_hrule(line: str) -> bool:
    return _HRULE.match(line) is not None


def line_links(line: str) -> list[tuple[int, int, int, int, str]]:
    """Links on a line as (src_start, src_end, vis_start, vis_end, url).

    Visual columns replay the `transform_line` walk, so they match what a
    previewed line shows. Heading markers shift visual columns too.
    """
    out: list[tuple[int, int, int, int, str]] = []
    heading = _HEADING.match(line)
    if heading:
        # A previewed heading conceals only its marker; links stay raw text.
        shift = len(heading.group(1)) + 1
        for match in _INLINE.finditer(line):
            if match.group("ltext") is not None:
                start, end = match.start(), match.end()
                out.append((start, end, start - shift, end - shift, match.group("lurl")))
        return out
    vis = 0
    last = 0
    for match in _INLINE.finditer(line):
        vis += match.start() - last
        if match.group("ltext") is not None:
            text, url = match.group("ltext"), match.group("lurl")
            out.append((match.start(), match.end(), vis, vis + len(text), url))
            vis += len(text)
        else:
            name = str(match.lastgroup)
            vis += len(match.group(name))
        last = match.end()
    return out
