from telepane.tmux import Pane
from telepane.widgets.info import compact_path, render_server, render_target
from telepane.widgets.resizer import clamp_size
from telepane.widgets.tree import KIND_PANE, NodeRef


def test_compact_path_home_and_parents():
    assert compact_path("/home/user/dev/project/app", "/home/user") == "~/d/p/app"


def test_compact_path_no_home():
    assert compact_path("/tmp", "") == "/tmp"


def test_render_target_long_title_gets_own_line():
    ref = NodeRef(KIND_PANE, "%3", "%3", "w.0")
    pane = Pane(
        id="%3",
        index=0,
        title="Z" * 200,
        command="bash",
        path="/tmp",
        active=True,
        pid=9,
        width=80,
        height=24,
    )
    out = render_target(ref, pane, width=40, home="")
    assert "\n" in out  # the very long title drops to its own line


def test_render_target_is_single_line():
    ref = NodeRef(KIND_PANE, "%3", "%3", "w.0")
    pane = Pane(
        id="%3",
        index=0,
        title="t",
        command="bash",
        path="/tmp",
        active=True,
        pid=9,
        width=80,
        height=24,
    )
    out = render_target(ref, pane, width=200)
    assert "\n" not in out
    assert "%3" in out and "bash" in out and "/tmp" in out


def test_render_target_none():
    assert "Select" in render_target(None, None)


def test_render_server_is_single_line_when_running():
    info = {
        "running": "yes",
        "version": "3.7",
        "pid": "1",
        "socket": "/s",
        "sessions": "2",
        "windows": "3",
        "panes": "6",
        "clients": "1",
    }
    out = render_server(info)
    assert "\n" not in out  # one line; the Static wraps it as the viewport narrows
    assert "3.7" in out and "sess" in out


def test_render_server_not_running():
    assert "not running" in render_server({"running": "no", "version": "3.7"})


def test_clamp_size_clamps_min():
    assert clamp_size(5, 200, 20) == 20


def test_clamp_size_clamps_max():
    assert clamp_size(195, 200, 20) == 180


def test_clamp_size_passthrough():
    assert clamp_size(80, 200, 20) == 80
