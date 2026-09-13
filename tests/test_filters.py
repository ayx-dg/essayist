"""Pandoc filters: paths, the filters that come with essayist, folders."""

import os

from essayist import filters


def test_flag_for_lua_files():
    assert filters.flag_for("a/b.lua") == "--lua-filter=a/b.lua"


def test_flag_for_other_files():
    assert filters.flag_for("a/b.py") == "--filter=a/b.py"


def test_included_lists_gallery():
    assert "gallery.lua" in filters.included()


def test_included_path_works_with_and_without_suffix():
    assert filters.included_path("gallery") == filters.included_path("gallery.lua")
    assert os.path.isfile(filters.included_path("gallery"))


def test_find_by_path(tmp_path):
    path = tmp_path / "up.lua"
    path.write_text("")
    assert filters.find(str(path)) == str(path)


def test_find_by_name_in_folder(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "up.lua").write_text("")
    assert filters.find("up", str(tmp_path / "fd")) == str(tmp_path / "fd" / "up.lua")


def test_find_a_filter_that_comes_with_essayist(tmp_path):
    found = filters.find("gallery", str(tmp_path / "empty"))
    assert found is not None
    assert found.endswith("gallery.lua")


def test_find_returns_none_for_unknown(tmp_path):
    assert filters.find("nope", str(tmp_path / "empty")) is None


def test_in_folder_sorts_by_name_and_skips_other_files(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "b.lua").write_text("")
    (tmp_path / "fd" / "a.lua").write_text("")
    (tmp_path / "fd" / "note.txt").write_text("")
    found = filters.in_folder(str(tmp_path / "fd"))
    assert [os.path.basename(p) for p in found] == ["a.lua", "b.lua"]


def test_in_folder_empty_when_folder_missing(tmp_path):
    assert filters.in_folder(str(tmp_path / "nope")) == []


def test_flags_covers_names_and_folder(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "a.lua").write_text("")
    made = filters.flags(["gallery"], str(tmp_path / "fd"))
    assert len(made) == 2
    assert any(f.endswith("gallery.lua") for f in made)
    assert any(f.endswith("a.lua") for f in made)


def test_flags_has_no_repeats(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "a.lua").write_text("")
    made = filters.flags(["a", "a.lua"], str(tmp_path / "fd"))
    assert made == [f"--lua-filter={tmp_path / 'fd' / 'a.lua'}"]


def test_flags_skips_unknown_names():
    assert filters.flags(["nope"]) == []
