import pytest

from telepane import tmux


class Dummy:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def test_list_sessions_parses(monkeypatch):
    row = "\t".join(["$0", "main", "2", "1", "1700000000", "1700000100", "/home/u"])

    def fake_run(args, **kw):
        if args[1] == "list-sessions":
            return Dummy(row + "\n")
        return Dummy("")

    monkeypatch.setattr(tmux.subprocess, "run", fake_run)
    sessions = tmux.list_sessions(deep=True)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.id == "$0"
    assert s.name == "main"
    assert s.window_count == 2
    assert s.attached is True
    assert s.path == "/home/u"
    assert s.windows == []


def test_list_panes_parses(monkeypatch):
    row = "\t".join(["%5", "0", "vim", "python", "/tmp", "1", "4242", "120", "40"])

    def fake_run(args, **kw):
        return Dummy(row + "\n") if args[1] == "list-panes" else Dummy("")

    monkeypatch.setattr(tmux.subprocess, "run", fake_run)
    panes = tmux.list_panes("@1")
    assert len(panes) == 1
    p = panes[0]
    assert p.id == "%5"
    assert p.command == "python"
    assert p.active is True
    assert p.pid == 4242
    assert (p.width, p.height) == (120, 40)
    assert p.target == "%5"


def test_send_text_builds_literal_argv(monkeypatch):
    calls = []

    def fake_run(args, **kw):
        calls.append(args)
        return Dummy("")

    monkeypatch.setattr(tmux.subprocess, "run", fake_run)
    tmux.send_text("%3", "hello -n world", enter=True)
    assert calls == [
        [
            "tmux",
            "send-keys",
            "-t",
            "%3",
            "-l",
            "--",
            "hello -n world",
            ";",
            "send-keys",
            "-t",
            "%3",
            "Enter",
        ]
    ]


def test_send_text_escapes_trailing_semicolon(monkeypatch):
    calls = []
    monkeypatch.setattr(tmux.subprocess, "run", lambda args, **kw: calls.append(args) or Dummy(""))
    tmux.send_text("%3", "phpinfo();", enter=False)
    assert calls[0][-1] == "phpinfo()\\;"
    calls.clear()
    tmux.send_text("%3", "a;b;c", enter=False)
    assert calls[0][-1] == "a;b;c"


def test_send_text_no_enter_single_call(monkeypatch):
    calls = []
    monkeypatch.setattr(tmux.subprocess, "run", lambda args, **kw: calls.append(args) or Dummy(""))
    tmux.send_text("%3", "x", enter=False)
    assert len(calls) == 1


def test_send_text_empty_only_enter(monkeypatch):
    calls = []
    monkeypatch.setattr(tmux.subprocess, "run", lambda args, **kw: calls.append(args) or Dummy(""))
    tmux.send_text("%3", "", enter=True)
    assert calls == [["tmux", "send-keys", "-t", "%3", "Enter"]]


def test_run_raises_on_failure(monkeypatch):
    monkeypatch.setattr(tmux.subprocess, "run", lambda args, **kw: Dummy("", 1, "boom"))
    with pytest.raises(tmux.TmuxError):
        tmux._run(["kill-session", "-t", "$9"])


def test_run_swallows_failure_when_unchecked(monkeypatch):
    monkeypatch.setattr(tmux.subprocess, "run", lambda args, **kw: Dummy("", 1, "boom"))
    assert tmux._run(["list-sessions"], check=False) == ""
