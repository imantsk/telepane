# Changelog

This file documents all the important changes to this project. The format
follows [Keep a Changelog](https://keepachangelog.com/). The project follows
semantic versioning.

## [Unreleased]

## [0.9.7] - 2026-08-19

- Humanize pane command names in the sidebar: the tree shows the callable
  command (claude, copilot, opencode) instead of the kernel process name.
  Toggle in Settings, default on.
- Update notice next to the clock when PyPI has a newer version. Auto-update
  through pip when the toggle is on. Both toggles default on.

## [0.9.6] - 2026-08-19

- Shift+Click opens a previewed or raw markdown link in the browser. Only
  http and https links open.
- New settings: "Link browser" picker (system default or an installed
  browser) and a "Shift+Click opens links" toggle, default on.

## [0.9.5] - 2026-08-18

- Live markdown preview in the send box: completed fences render as rules
  with the language tag, bold/underline/italic/strike/inline-code/links
  render styled with markers concealed, headings hide their markers, and
  `---` renders as a rule. The cursor line and any broken syntax show raw
  text.
- Style fenced-code content and the fence language tag in the highlighter.
- Fix `send_text` so a message that ends with `;` keeps its last character.

## [0.9.4] - 2026-08-18

- Rewrite the readme and refresh the PyPI project page.

## [0.9.3] - 2026-08-18

- Fix an import crash on Python 3.9 in the modal screens.

## [0.9.2] - 2026-08-18

Initial release.

- Mouse-driven Textual TUI: session/window/pane tree, live server stats, a
  `capture-pane` preview, and a send box that delivers text to any chosen pane.
- Resizable sidebar and preview/send split; markdown highlighting in the input.
- Screenshot (SVG / PNG / MD) with clipboard copy.
- Settings view: Telepane options, theme, screenshot, tmux profiles, and a
  categorised tmux config editor applied live via `set-option`.
