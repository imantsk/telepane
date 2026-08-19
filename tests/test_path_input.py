import os

from telepane.widgets.path_input import complete_dir


def test_complete_single_match(tmp_path):
    (tmp_path / "projects").mkdir()
    (tmp_path / "other").mkdir()
    value, candidates = complete_dir(str(tmp_path / "pro"), home="")
    assert value == str(tmp_path / "projects") + os.sep
    assert len(candidates) == 1


def test_complete_common_prefix(tmp_path):
    (tmp_path / "app-one").mkdir()
    (tmp_path / "app-two").mkdir()
    value, candidates = complete_dir(str(tmp_path / "a"), home="")
    assert value == str(tmp_path / "app-")
    assert len(candidates) == 2


def test_complete_lists_dir_contents(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "y").mkdir()
    value, candidates = complete_dir(str(tmp_path) + os.sep, home="")
    assert len(candidates) == 2


def test_complete_tilde_stays_tilde(tmp_path):
    (tmp_path / "docs").mkdir()
    value, _ = complete_dir("~/do", home=str(tmp_path))
    assert value == "~/docs" + os.sep


def test_complete_no_match(tmp_path):
    value, candidates = complete_dir(str(tmp_path / "zzz"), home="")
    assert candidates == []
    assert value == str(tmp_path / "zzz")


def test_complete_files_ignored(tmp_path):
    (tmp_path / "afile").write_text("x")
    (tmp_path / "adir").mkdir()
    value, candidates = complete_dir(str(tmp_path / "a"), home="")
    assert value == str(tmp_path / "adir") + os.sep
    assert len(candidates) == 1
