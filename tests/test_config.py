from telepane.config import Config


def test_defaults():
    c = Config()
    assert c.enter_sends is True
    assert c.confirm_kill is True
    assert c.poll_interval == 2.0


def test_save_load_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    Config(enter_sends=False, poll_interval=5.0, favorites=["a"]).save()
    loaded = Config.load()
    assert loaded.enter_sends is False
    assert loaded.poll_interval == 5.0
    assert loaded.favorites == ["a"]


def test_load_missing_returns_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "nope"))
    assert Config.load().enter_sends is True


def test_load_ignores_unknown_keys(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    (tmp_path / "telepane").mkdir()
    (tmp_path / "telepane" / "config.json").write_text('{"enter_sends": false, "bogus": 1}')
    loaded = Config.load()
    assert loaded.enter_sends is False
    assert not hasattr(loaded, "bogus")
