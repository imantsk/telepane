import pytest

from telepane import browser


def test_open_url_rejects_non_http():
    with pytest.raises(ValueError):
        browser.open_url("javascript:alert(1)")
    with pytest.raises(ValueError):
        browser.open_url("file:///etc/passwd")


def test_open_url_default_uses_webbrowser(monkeypatch):
    calls = []
    monkeypatch.setattr(browser.webbrowser, "open", lambda url: calls.append(url))
    browser.open_url("https://example.com")
    browser.open_url("https://example.com", browser.SYSTEM)
    assert calls == ["https://example.com"] * 2


def test_open_url_named_browser_argv(monkeypatch):
    calls = []
    monkeypatch.setattr(browser.subprocess, "run", lambda args, **kw: calls.append(args))
    browser.open_url("https://example.com", "Firefox")
    assert calls and "https://example.com" in calls[0]
    assert not any("sh" in str(a) for a in calls[0][:1])


def test_installed_starts_with_system_default():
    options = browser.installed()
    assert options[0] == browser.SYSTEM
