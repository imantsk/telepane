import pytest


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    """Keep tests off the user's real ~/.config/telepane so they run on defaults."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
