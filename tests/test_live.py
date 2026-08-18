import os
import time
import uuid

import pytest

from telepane import tmux
from telepane.app import TelepaneApp
from telepane.widgets.tree import KIND_PANE, NodeRef

live = pytest.mark.skipif(
    not os.environ.get("TELEPANE_LIVE_TESTS"),
    reason="live tmux test; set TELEPANE_LIVE_TESTS=1 to run",
)


@live
def test_send_text_roundtrip_against_real_tmux():
    name = f"telepane-selftest-{uuid.uuid4().hex[:8]}"
    tmux.new_session(name)
    session = next(s for s in tmux.list_sessions() if s.name == name)
    try:
        pane = session.windows[0].panes[0]
        marker = f"TELEPANE_OK_{uuid.uuid4().hex[:6]}"
        tmux.send_text(pane.id, f"printf {marker}", enter=True)
        time.sleep(0.4)
        assert marker in tmux.capture_pane(pane.id)
    finally:
        tmux.kill_session(session.id)


@live
async def test_app_sends_to_real_pane_end_to_end():
    """Full stack: the running App's send path delivers to a real tmux pane."""
    name = f"telepane-e2e-{uuid.uuid4().hex[:8]}"
    tmux.new_session(name)
    session = next(s for s in tmux.list_sessions() if s.name == name)
    try:
        pane = session.windows[0].panes[0]
        marker = f"TELEPANE_E2E_{uuid.uuid4().hex[:6]}"
        app = TelepaneApp()
        async with app.run_test() as pilot:
            app.selected = NodeRef(KIND_PANE, pane.id, pane.id, name)
            app.query_one("#send-input").text = f"printf {marker}"
            app.action_send()
            await pilot.pause()
        time.sleep(0.4)
        assert marker in tmux.capture_pane(pane.id)
    finally:
        tmux.kill_session(session.id)
