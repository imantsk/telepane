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
