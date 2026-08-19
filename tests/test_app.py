import pytest

from telepane import tmux
from telepane.app import TelepaneApp
from telepane.tmux import Pane, Session, Window
from telepane.widgets.send_box import SendBox
from telepane.widgets.tree import KIND_PANE, NodeRef


def _sessions():
    pane = Pane(
        id="%0",
        index=0,
        title="",
        command="bash",
        path="/tmp",
        active=True,
        pid=1,
        width=80,
        height=24,
    )
    win = Window(id="@0", index=0, name="w", pane_count=1, active=True, layout="", panes=[pane])
    return [
        Session(
            id="$0",
            name="s",
            window_count=1,
            attached=True,
            created=0,
            activity=0,
            path="/tmp",
            windows=[win],
        )
    ]


@pytest.fixture
def mocked(monkeypatch):
    sent = []
    monkeypatch.setattr(tmux, "snapshot", lambda: _sessions())
    monkeypatch.setattr(tmux, "list_sessions", lambda deep=True: _sessions())
    monkeypatch.setattr(
        tmux,
        "server_info",
        lambda sessions=None: {
            "running": "yes",
            "version": "3.7",
            "pid": "1",
            "socket": "/x",
            "term": "xterm",
            "sessions": "1",
            "windows": "1",
            "panes": "1",
            "clients": "1",
        },
    )
    monkeypatch.setattr(tmux, "capture_pane", lambda t, **k: "line1\nline2")
    monkeypatch.setattr(tmux, "send_text", lambda t, txt, enter=True: sent.append((t, txt, enter)))
    return sent


@pytest.mark.asyncio
async def test_app_mounts_and_lists(mocked):
    app = TelepaneApp()
    async with app.run_test():
        assert app.query_one("#tree").root.children  # session node built


@pytest.mark.asyncio
async def test_app_send_delivers_to_pane(mocked):
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app.query_one("#send-input").text = "hello world"
        app.action_send()
        await pilot.pause()
    assert mocked == [("%0", "hello world", True)]


@pytest.mark.asyncio
async def test_app_send_without_target_is_noop(mocked):
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = None
        app.query_one("#send-input").text = "x"
        app.action_send()
        await pilot.pause()
    assert mocked == []


@pytest.mark.asyncio
async def test_enter_in_input_sends(mocked):
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        inp = app.query_one("#send-input")
        inp.focus()
        await pilot.pause()
        inp.text = "typed then enter"
        await pilot.press("enter")
        await pilot.pause()
    assert mocked == [("%0", "typed then enter", True)]


@pytest.mark.asyncio
async def test_shift_enter_inserts_newline_when_enter_sends(mocked):
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        inp = app.query_one("#send-input")
        inp.focus()
        await pilot.pause()
        inp.text = "line1"
        await pilot.press("shift+enter")
        await pilot.pause()
        assert "\n" in inp.text  # newline inserted, not submitted
    assert mocked == []


@pytest.mark.asyncio
async def test_toggle_off_enter_newline_shift_enter_sends(mocked):
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app.query_one(SendBox).set_enter_sends(False)
        inp = app.query_one("#send-input")
        inp.focus()
        await pilot.pause()
        inp.text = "msg"
        await pilot.press("enter")  # now inserts a newline, does not send
        await pilot.pause()
        assert mocked == []
        assert "\n" in inp.text
        await pilot.press("shift+enter")  # now sends
        await pilot.pause()
    assert len(mocked) == 1
    assert mocked[0][0] == "%0"


@pytest.mark.asyncio
async def test_settings_screen_opens_and_switches(mocked):
    from telepane.widgets.settings_screen import SettingsScreen

    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.action_settings()
        await pilot.pause()
        assert isinstance(app.screen, SettingsScreen)
        app.screen._show_section("General")
        await pilot.pause()
        assert app.screen.query("#settings-fields *")


@pytest.mark.asyncio
async def test_settings_applies_telepane_toggle(mocked):
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.action_settings()
        await pilot.pause()
        app.screen._dispatch("f-confirm_kill", False)
        await pilot.pause()
    assert app.config.confirm_kill is False


@pytest.mark.asyncio
async def test_md_highlight_toggle(mocked):
    from telepane.widgets.send_box import MessageArea

    app = TelepaneApp()
    async with app.run_test() as pilot:
        area = app.query_one("#send-input", MessageArea)
        app.query_one(SendBox).set_md_highlight(True)
        await pilot.pause()
        assert area.language == "markdown"
        app.query_one(SendBox).set_md_highlight(False)
        await pilot.pause()
        assert area.language is None


@pytest.mark.asyncio
async def test_sidebar_resize_drag_changes_width(mocked):
    from telepane.widgets.resizer import Resizer

    class Move:
        screen_x = 30

        def stop(self):
            pass

    app = TelepaneApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()  # let the initial size-clamp settle
        resizer = app.query_one("#resizer", Resizer)
        resizer._dragging = True
        resizer.on_mouse_move(Move())
        await pilot.pause()
        assert app.query_one("#left").styles.width.value == 30


@pytest.mark.asyncio
async def test_sidebar_resize_persists_to_config(mocked, monkeypatch, tmp_path):
    from telepane.widgets.resizer import Resizer

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    app = TelepaneApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#resizer", Resizer).post_message(Resizer.Committed("sidebar", 33))
        await pilot.pause()
        assert app.config.sidebar_width == 33
    from telepane.config import Config

    assert Config.load().sidebar_width == 33


@pytest.mark.asyncio
async def test_send_resize_bounds(mocked):
    from telepane.widgets.resizer import Resizer

    class Move:
        def __init__(self, y):
            self.screen_y = y

        def stop(self):
            pass

    app = TelepaneApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()  # let the initial size-clamp settle
        rz = app.query_one("#resizer-y", Resizer)
        sb = app.query_one("#sendbox")
        rz._dragging = True
        rz.on_mouse_move(Move(2))  # drag to the top: max (preview hidden)
        await pilot.pause()
        max_h = sb.styles.height.value
        rz.on_mouse_move(Move(38))  # drag to the bottom: min (one line)
        await pilot.pause()
        min_h = sb.styles.height.value
    assert min_h == 6  # min_size, never fully hidden
    assert max_h >= 20  # grows large enough to hide the viewer


@pytest.mark.asyncio
async def test_maximized_send_box_tracks_terminal_height(mocked):
    from telepane.app import _SEND_MAX
    from telepane.config import Config

    heights = {}
    for term_h in (20, 50):
        app = TelepaneApp(config=Config(send_height=_SEND_MAX))
        async with app.run_test(size=(120, term_h)) as pilot:
            await pilot.pause()
            heights[term_h] = app.query_one("#sendbox").styles.height.value
    assert heights[50] > heights[20]  # stays maximized, grows with the terminal


@pytest.mark.asyncio
async def test_send_height_resize_persists_to_config(mocked, monkeypatch, tmp_path):
    from telepane.widgets.resizer import Resizer

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    app = TelepaneApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#resizer-y", Resizer).post_message(Resizer.Committed("send", 12))
        await pilot.pause()
        assert app.config.send_height == 12


@pytest.mark.asyncio
async def test_shift_click_link_opens_browser(mocked, monkeypatch):
    from telepane import browser as browser_mod
    from telepane.widgets.send_box import MessageArea

    opened = []
    monkeypatch.setattr(browser_mod, "open_url", lambda url, b="": opened.append((url, b)))
    app = TelepaneApp()
    async with app.run_test(size=(100, 40)) as pilot:
        area = app.query_one("#send-input", MessageArea)
        area.text = "see [docs](https://example.com)\n"
        area.cursor_location = (1, 0)
        await pilot.pause()
        await pilot.click(MessageArea, offset=(6, 0), shift=True)
        await pilot.pause()
        for _ in range(20):
            if opened:
                break
            await pilot.pause(0.05)
    assert opened == [("https://example.com", "")]


@pytest.mark.asyncio
async def test_plain_click_does_not_open(mocked, monkeypatch):
    from telepane import browser as browser_mod
    from telepane.widgets.send_box import MessageArea

    opened = []
    monkeypatch.setattr(browser_mod, "open_url", lambda url, b="": opened.append(url))
    app = TelepaneApp()
    async with app.run_test(size=(100, 40)) as pilot:
        area = app.query_one("#send-input", MessageArea)
        area.text = "see [docs](https://example.com)\n"
        area.cursor_location = (1, 0)
        await pilot.pause()
        await pilot.click(MessageArea, offset=(6, 0))
        await pilot.pause()
    assert opened == []


@pytest.mark.asyncio
async def test_shift_click_disabled_by_setting(mocked, monkeypatch):
    from telepane import browser as browser_mod
    from telepane.config import Config
    from telepane.widgets.send_box import MessageArea

    opened = []
    monkeypatch.setattr(browser_mod, "open_url", lambda url, b="": opened.append(url))
    config = Config()
    config.open_links = False
    app = TelepaneApp(config=config)
    async with app.run_test(size=(100, 40)) as pilot:
        area = app.query_one("#send-input", MessageArea)
        area.text = "see [docs](https://example.com)\n"
        area.cursor_location = (1, 0)
        await pilot.pause()
        await pilot.click(MessageArea, offset=(6, 0), shift=True)
        await pilot.pause()
    assert opened == []


@pytest.mark.asyncio
async def test_update_notice_appears(mocked, monkeypatch):
    from telepane import updates

    monkeypatch.setattr(updates, "latest_version", lambda: "99.0.0")
    monkeypatch.setattr(updates, "upgrade", lambda: False)
    from telepane.config import Config

    config = Config()
    config.auto_update = False
    app = TelepaneApp(config=config)
    async with app.run_test() as pilot:
        for _ in range(40):
            if app.query("#update-notice"):
                break
            await pilot.pause(0.05)
        notice = app.query_one("#update-notice")
        assert "99.0.0" in str(notice.render())


@pytest.mark.asyncio
async def test_no_notice_when_check_disabled(mocked, monkeypatch):
    from telepane import updates

    monkeypatch.setattr(updates, "latest_version", lambda: "99.0.0")
    from telepane.config import Config

    config = Config()
    config.update_check = False
    app = TelepaneApp(config=config)
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        assert not app.query("#update-notice")


@pytest.mark.asyncio
async def test_settings_shows_version(mocked):
    from telepane import __version__

    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.action_settings()
        await pilot.pause()
        label = app.screen.query_one("#settings-version")
        assert __version__ in str(label.render())


@pytest.mark.asyncio
async def test_shift_split_opens_picker_and_runs_agent(mocked, monkeypatch):
    from telepane import agents
    from telepane import tmux as tmux_mod
    from telepane.widgets.modals import SplitPrompt

    splits = []
    monkeypatch.setattr(tmux_mod, "split_window", lambda t, **kw: splits.append((t, kw)))
    monkeypatch.setattr(agents, "installed", lambda: ["codex", "claude"])
    monkeypatch.setattr(agents, "bypass_flag", lambda n: "--yolo-flag")
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app._picker_arm = "split_h"
        app.action_split_h()
        await pilot.pause()
        assert isinstance(app.screen, SplitPrompt)
        lv = app.screen.query_one("#split-agents")
        lv.index = 1  # codex
        lv.action_select_cursor()
        for _ in range(40):
            if splits:
                break
            await pilot.pause(0.05)
    assert splits == [
        ("%0", {"horizontal": True, "command": "codex --yolo-flag", "start_dir": "/tmp"})
    ]


@pytest.mark.asyncio
async def test_shift_split_custom_command(mocked, monkeypatch):
    from telepane import agents
    from telepane import tmux as tmux_mod
    from telepane.widgets.modals import SplitPrompt

    splits = []
    monkeypatch.setattr(tmux_mod, "split_window", lambda t, **kw: splits.append((t, kw)))
    monkeypatch.setattr(agents, "installed", lambda: [])
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app._picker_arm = "split_v"
        app.action_split_v()
        await pilot.pause()
        assert isinstance(app.screen, SplitPrompt)
        box = app.screen.query_one("#split-command")
        box.focus()
        box.value = "htop"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
    assert splits == [("%0", {"horizontal": False, "command": "htop", "start_dir": "/tmp"})]


@pytest.mark.asyncio
async def test_plain_split_never_opens_picker(mocked, monkeypatch):
    from telepane import tmux as tmux_mod
    from telepane.widgets.modals import SplitPrompt

    splits = []
    monkeypatch.setattr(tmux_mod, "split_window", lambda t, **kw: splits.append((t, kw)))
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app.action_split_h()
        await pilot.pause()
        assert not isinstance(app.screen, SplitPrompt)
    assert splits == [("%0", {"horizontal": True, "command": None, "start_dir": "/tmp"})]


@pytest.mark.asyncio
async def test_split_picker_is_centered_and_compact(mocked, monkeypatch):
    from telepane import agents

    monkeypatch.setattr(agents, "installed", lambda: ["claude", "codex", "gemini"])
    app = TelepaneApp()
    async with app.run_test(size=(100, 40)) as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app._picker_arm = "split_h"
        app.action_split_h()
        await pilot.pause()
        dialog = app.screen.query_one("#dialog")
        region = dialog.region
        assert region.y > 2  # vertically centered, not docked to the top
        assert abs((region.x + region.width // 2) - 50) <= 2  # horizontally centered
        assert region.height <= 19


@pytest.mark.asyncio
async def test_palette_update_entry_states(mocked):
    from telepane.app import _MenuCommands

    app = TelepaneApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        provider = _MenuCommands(app.screen)
        titles = [t if isinstance(t, str) else t.plain for t, _, _ in provider._items()]
        assert "Update" in titles  # dim plain-text form when no update exists
        app._update_latest = "9.9.9"
        titles = [t if isinstance(t, str) else t.plain for t, _, _ in provider._items()]
        assert "Update to 9.9.9" in titles
        app._update_ready = True
        titles = [t if isinstance(t, str) else t.plain for t, _, _ in provider._items()]
        assert "Update · 9.9.9 ready" in titles


@pytest.mark.asyncio
async def test_action_update_installs_when_available(mocked, monkeypatch):
    from telepane import updates

    monkeypatch.setattr(updates, "upgrade", lambda: True)
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app._update_latest = "9.9.9"
        app.action_update()
        for _ in range(40):
            if app._update_ready:
                break
            await pilot.pause(0.05)
        assert app._update_ready


@pytest.mark.asyncio
async def test_action_update_noop_when_current(mocked, monkeypatch):
    notes = []
    app = TelepaneApp()
    async with app.run_test() as pilot:
        monkeypatch.setattr(app, "notify", lambda msg, **kw: notes.append(msg))
        app.action_update()
        await pilot.pause()
    assert any("latest version" in n for n in notes)
    assert not app._update_ready


@pytest.mark.asyncio
async def test_rename_pane_targets_parent_window(mocked, monkeypatch):
    from telepane import tmux as tmux_mod
    from telepane.widgets.modals import TextPrompt

    renames = []
    monkeypatch.setattr(tmux_mod, "rename_window", lambda t, n: renames.append((t, n)))
    app = TelepaneApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app.action_rename()
        await pilot.pause()
        assert isinstance(app.screen, TextPrompt)
        box = app.screen.query_one("#prompt-input")
        box.focus()
        box.value = "renamed"
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
    assert renames == [("@0", "renamed")]


@pytest.mark.asyncio
async def test_split_agent_without_yolo(mocked, monkeypatch):
    from telepane import agents
    from telepane import tmux as tmux_mod
    from telepane.widgets.modals import SplitPrompt

    splits = []
    monkeypatch.setattr(tmux_mod, "split_window", lambda t, **kw: splits.append((t, kw)))
    monkeypatch.setattr(agents, "installed", lambda: ["codex"])
    monkeypatch.setattr(agents, "bypass_flag", lambda n: "--yolo-flag")
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app._picker_arm = "split_h"
        app.action_split_h()
        await pilot.pause()
        assert isinstance(app.screen, SplitPrompt)
        app.screen.query_one("#split-yolo").value = False
        await pilot.pause()
        lv = app.screen.query_one("#split-agents")
        lv.index = 1
        lv.action_select_cursor()
        for _ in range(40):
            if splits:
                break
            await pilot.pause(0.05)
    assert splits == [("%0", {"horizontal": True, "command": "codex", "start_dir": "/tmp"})]


@pytest.mark.asyncio
async def test_split_custom_path_overrides_pane_path(mocked, monkeypatch):
    from telepane import agents
    from telepane import tmux as tmux_mod
    from telepane.widgets.modals import SplitPrompt

    splits = []
    monkeypatch.setattr(tmux_mod, "split_window", lambda t, **kw: splits.append((t, kw)))
    monkeypatch.setattr(agents, "installed", lambda: [])
    app = TelepaneApp()
    async with app.run_test() as pilot:
        app.selected = NodeRef(KIND_PANE, "%0", "%0", "w.0")
        app._picker_arm = "split_h"
        app.action_split_h()
        await pilot.pause()
        assert isinstance(app.screen, SplitPrompt)
        assert app.screen.query_one("#split-path").value == "/tmp"
        app.screen.query_one("#split-path").value = "/work"
        lv = app.screen.query_one("#split-agents")
        lv.index = 0  # shell
        lv.action_select_cursor()
        for _ in range(40):
            if splits:
                break
            await pilot.pause(0.05)
    assert splits == [("%0", {"horizontal": True, "command": None, "start_dir": "/work"})]
