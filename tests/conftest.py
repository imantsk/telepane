import pytest


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    """Keep tests off the user's real ~/.config/telepane so they run on defaults."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))


@pytest.fixture(autouse=True)
def no_network_update_check(request, monkeypatch):
    if request.module.__name__ == "test_updates":
        yield
        return
    from telepane import updates

    monkeypatch.setattr(updates, "latest_version", lambda: None)
    monkeypatch.setattr(updates, "upgrade", lambda: False)
    yield
