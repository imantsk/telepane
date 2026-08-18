"""Entry point for the `telepane` command."""

from __future__ import annotations

import argparse
import sys

from . import __version__, tmux
from .app import TelepaneApp


def _preflight() -> str | None:
    if not tmux.is_installed():
        return "tmux is not installed, or not on the PATH."
    if not tmux.server_running():
        return "No tmux server runs. Start a tmux server first. For example, run `tmux new`."
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="telepane",
        description="Mouse-driven tmux control dashboard. Send text to any pane.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"telepane {__version__}")
    parser.parse_args(argv)

    problem = _preflight()
    if problem:
        print(problem, file=sys.stderr)
        return 1

    TelepaneApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
