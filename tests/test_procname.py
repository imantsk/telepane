from telepane import procname


def test_display_name_plain():
    assert procname.display_name("claude --dangerously-skip-permissions") == "claude"
    assert procname.display_name("zsh") == "zsh"


def test_display_name_strips_exe():
    assert procname.display_name("/opt/x/opencode.exe") == "opencode"


def test_display_name_interpreter_uses_script():
    assert procname.display_name("node /x/@github/copilot/bin/copilot") == "copilot"
    assert (
        procname.display_name("/x/Python.app/Contents/MacOS/Python /Users/im/.local/bin/telepane")
        == "telepane"
    )


def test_display_name_interpreter_skips_flags():
    assert procname.display_name("python3 -u /srv/agent.py") == "agent.py"


def test_display_name_version_argv0_kept_verbatim():
    assert procname.display_name("2.1.235") == "2.1.235"


_PS = """\
ttys000  S+   28951   200 copilot
ttys000  S+   28952 28951 node /x/@github/copilot/bin/copilot
ttys000  S+   28953 28952 /x/copilot-darwin-arm64/copilot
ttys003  Ss+  84809  1690 claude --dangerously-skip-permissions
ttys003  S+   84938 84809 /opt/homebrew/bin/uv run web-vision-mcp
ttys006  S+     311 47754 caffeinate -i -t 300
ttys006  Ss+  47754  1690 claude --resume abc
ttys005  Ss     100     1 -zsh
??       Ss   30612     1 /bin/zsh -c something
"""


def test_foreground_names_group_root_wins(monkeypatch):
    class Out:
        stdout = _PS

    monkeypatch.setattr(procname.subprocess, "run", lambda *a, **k: Out())
    names = procname.foreground_names()
    assert names["/dev/ttys000"] == "copilot"
    assert names["/dev/ttys003"] == "claude"
    assert names["/dev/ttys006"] == "claude"  # recycled low pid must not win
    assert "/dev/ttys005" not in names  # no foreground marker
    assert not any("??" in k for k in names)


def test_foreground_names_ps_failure(monkeypatch):
    def boom(*a, **k):
        raise OSError("no ps")

    monkeypatch.setattr(procname.subprocess, "run", boom)
    assert procname.foreground_names() == {}


def test_bypass_flag_inferred_from_help(monkeypatch):
    from telepane import agents

    helps = {
        "codex": "--dangerously-bypass-approvals-and-sandbox  skip approvals",
        "claude": "--dangerously-skip-permissions  Bypass all permission checks",
        "gemini": "-y, --yolo  Automatically accept all actions",
        "plain": "--help only here",
    }

    class Out:
        def __init__(self, text):
            self.stdout = text
            self.stderr = ""

    monkeypatch.setattr(agents.subprocess, "run", lambda args, **kw: Out(helps.get(args[0], "")))
    agents._flag_cache.clear()
    assert agents.bypass_flag("codex") == "--dangerously-bypass-approvals-and-sandbox"
    assert agents.bypass_flag("claude") == "--dangerously-skip-permissions"
    assert agents.bypass_flag("gemini") == "--yolo"
    assert agents.bypass_flag("plain") is None
    agents._flag_cache.clear()


def test_bypass_flag_swallows_failure(monkeypatch):
    from telepane import agents

    def boom(*a, **k):
        raise OSError("gone")

    monkeypatch.setattr(agents.subprocess, "run", boom)
    agents._flag_cache.clear()
    assert agents.bypass_flag("ghost") is None
    agents._flag_cache.clear()
