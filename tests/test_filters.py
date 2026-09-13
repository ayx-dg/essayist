"""Pandoc filters: paths, bundle files, folder discovery."""

import os

from essayist import filters


def test_flag_uses_lua_filter_for_lua_files():
    assert filters.flag("a/b.lua") == "--lua-filter=a/b.lua"


def test_flag_uses_filter_for_other_files():
    assert filters.flag("a/b.py") == "--filter=a/b.py"


def test_bundle_files_lists_gallery():
    assert "gallery.lua" in filters.bundle_files()


def test_bundle_path_works_with_and_without_suffix():
    assert filters.bundle_path("gallery") == filters.bundle_path("gallery.lua")
    assert os.path.isfile(filters.bundle_path("gallery"))


def test_find_by_path(tmp_path):
    path = tmp_path / "up.lua"
    path.write_text("")
    assert filters.find(str(path)) == str(path)


def test_find_by_name_in_filter_dir(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "up.lua").write_text("")
    assert filters.find("up", str(tmp_path / "fd")) == str(tmp_path / "fd" / "up.lua")


def test_find_bundle_file(tmp_path):
    found = filters.find("gallery", str(tmp_path / "empty"))
    assert found is not None
    assert found.endswith("gallery.lua")


def test_find_returns_none_for_unknown(tmp_path):
    assert filters.find("nope", str(tmp_path / "empty")) is None


def test_discover_sorts_by_name_and_skips_other_files(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "b.lua").write_text("")
    (tmp_path / "fd" / "a.lua").write_text("")
    (tmp_path / "fd" / "note.txt").write_text("")
    found = filters.discover(str(tmp_path / "fd"))
    assert [os.path.basename(p) for p in found] == ["a.lua", "b.lua"]


def test_discover_empty_when_folder_missing(tmp_path):
    assert filters.discover(str(tmp_path / "nope")) == []


def test_all_flags_covers_names_and_folder(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "a.lua").write_text("")
    flags = filters.all_flags(["gallery"], str(tmp_path / "fd"))
    assert len(flags) == 2
    assert any(f.endswith("gallery.lua") for f in flags)
    assert any(f.endswith("a.lua") for f in flags)


def test_all_flags_has_no_repeats(tmp_path):
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "a.lua").write_text("")
    flags = filters.all_flags(["a", "a.lua"], str(tmp_path / "fd"))
    assert flags == [f"--lua-filter={tmp_path / 'fd' / 'a.lua'}"]


def test_all_flags_skips_unknown_names():
    assert filters.all_flags(["nope"]) == []
