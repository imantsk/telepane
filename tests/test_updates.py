import io

from telepane import updates


def test_is_newer():
    assert updates.is_newer("0.9.7", "0.9.6")
    assert updates.is_newer("1.0.0", "0.9.9")
    assert not updates.is_newer("0.9.6", "0.9.6")
    assert not updates.is_newer("0.9.5", "0.9.6")
    assert updates.is_newer("0.10.0", "0.9.6")


def test_latest_version_parses_pypi(monkeypatch):
    payload = io.BytesIO(b'{"info": {"version": "1.2.3"}}')
    payload.__enter__ = lambda *a: payload
    payload.__exit__ = lambda *a: False
    monkeypatch.setattr(updates.urllib.request, "urlopen", lambda url, timeout: payload)
    assert updates.latest_version() == "1.2.3"


def test_latest_version_swallows_errors(monkeypatch):
    def boom(url, timeout):
        raise OSError("offline")

    monkeypatch.setattr(updates.urllib.request, "urlopen", boom)
    assert updates.latest_version() is None


def test_upgrade_argv(monkeypatch):
    calls = []

    class Ok:
        pass

    monkeypatch.setattr(updates.subprocess, "run", lambda args, **kw: calls.append(args) or Ok())
    assert updates.upgrade() is True
    assert calls[0][1:] == ["-m", "pip", "install", "--upgrade", "--quiet", "telepane"]
