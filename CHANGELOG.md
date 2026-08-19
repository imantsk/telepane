# Changelog

This file documents all the important changes to this project. The format
follows [Keep a Changelog](https://keepachangelog.com/). The project follows
semantic versioning.

## [Unreleased]

## [0.9.10] - 2026-08-19

- Check for updates every hour, and when the app regains focus. The first
  check after a release now lands within the hour, not within six.

## [0.9.9] - 2026-08-19

- Shift+Click a split key to pick what runs in the new pane: an installed
  agent CLI, or a custom command. A yolo toggle (default on) adds the
  agent's approval-bypass flag, inferred from its own --help output.
- New panes start in the source pane's directory. The picker has a working
  directory input with Tab completion.
- Update entry in the command palette: dim when current, active when a new
  version exists.
- Rename acts on the selected window, or the window of the selected pane.
- Center the split picker and cap its height.

## [0.9.8] - 2026-08-19

- Show the version in the settings footer.

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
