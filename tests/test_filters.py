"""Tests for the pandoc filter interface (bundled, explicit and discovered)."""

import os

import pytest

from essayist import Blog, build_site
from essayist.config import Config
from essayist.core import pandoc_filter_flag

MARK_LUA = """function Str(el)
  if el.text == "MARKME" then
    return pandoc.Str("MARKED")
  end
end
"""


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _post(root, name="one.md", body="MARKME here"):
    return _write(
        root,
        f"markdown/posts/{name}",
        f"---\ntitle: One\ndate: 2024-01-01\npublish: public\n---\n\n{body}\n",
    )


# --- flag construction ----------------------------------------------------


def test_pandoc_filter_flag_dispatches_on_extension():
    assert pandoc_filter_flag("a/b.lua") == "--lua-filter=a/b.lua"
    assert pandoc_filter_flag("a/b.py") == "--filter=a/b.py"
    assert pandoc_filter_flag("a/b") == "--filter=a/b"


def test_bundled_filters_lists_gallery():
    assert "gallery.lua" in Blog.bundled_filters()


def test_bundled_filter_normalises_suffix():
    path = Blog.bundled_filter("gallery")
    assert os.path.isfile(path)
    assert path.endswith("gallery.lua")


# --- resolution -----------------------------------------------------------


def test_resolve_filter_finds_file_in_filter_dir(tmp_path):
    _write(tmp_path, "filters/mine.lua", MARK_LUA)
    cfg = Config(filter_dir=str(tmp_path / "filters"))
    assert cfg.resolve_filter("mine", None) == str(tmp_path / "filters" / "mine.lua")
    assert cfg.resolve_filter("mine.lua", None) == str(tmp_path / "filters" / "mine.lua")


def test_resolve_filter_accepts_absolute_path(tmp_path):
    path = _write(tmp_path, "elsewhere/custom.lua", MARK_LUA)
    cfg = Config(filter_dir=str(tmp_path / "filters"))
    assert cfg.resolve_filter(str(path), None) == str(path)


def test_resolve_filter_falls_back_to_bundled(tmp_path):
    cfg = Config(filter_dir=str(tmp_path / "filters"))
    resolved = cfg.resolve_filter("gallery", Blog)
    assert resolved is not None
    assert resolved.endswith("gallery.lua")
    assert os.path.isfile(resolved)


def test_resolve_filter_returns_none_when_missing(tmp_path):
    cfg = Config(filter_dir=str(tmp_path / "filters"))
    assert cfg.resolve_filter("nope", Blog) is None


# --- discovery ------------------------------------------------------------


def test_discovered_filters_sorted_and_lua_only(tmp_path):
    _write(tmp_path, "filters/b.lua", MARK_LUA)
    _write(tmp_path, "filters/a.lua", MARK_LUA)
    _write(tmp_path, "filters/notes.txt", "not a filter")
    cfg = Config(filter_dir=str(tmp_path / "filters"))
    found = cfg.discovered_filters()
    assert [os.path.basename(p) for p in found] == ["a.lua", "b.lua"]


def test_discovered_filters_empty_when_dir_missing(tmp_path):
    assert Config(filter_dir=str(tmp_path / "nope")).discovered_filters() == []


# --- flags ----------------------------------------------------------------


def test_filter_flags_from_discovery(tmp_path):
    d = tmp_path / "filters"
    _write(tmp_path, "filters/a.lua", MARK_LUA)
    cfg = Config(filter_dir=str(d))
    assert cfg.filter_flags(None) == [f"--lua-filter={d / 'a.lua'}"]


def test_gallery_shortcut_is_still_supported(tmp_path):
    cfg = Config(gallery=True, filter_dir=str(tmp_path / "none"))
    flags = cfg.filter_flags(Blog)
    assert len(flags) == 1
    assert flags[0].startswith("--lua-filter=")
    assert flags[0].endswith("gallery.lua")
    assert os.path.isfile(flags[0].split("=", 1)[1])


def test_filters_are_deduplicated(tmp_path):
    d = tmp_path / "filters"
    _write(tmp_path, "filters/a.lua", MARK_LUA)
    cfg = Config(filters=["a", "a.lua"], filter_dir=str(d))
    assert len(cfg.filter_flags(None)) == 1


def test_filter_already_in_panargs_is_not_repeated(tmp_path):
    d = tmp_path / "filters"
    _write(tmp_path, "filters/a.lua", MARK_LUA)
    cfg = Config(panargs=[f"--lua-filter={d / 'a.lua'}"], filter_dir=str(d))
    assert cfg.effective_panargs(None) == [f"--lua-filter={d / 'a.lua'}"]


# --- end to end -----------------------------------------------------------


def test_filter_dir_filter_is_applied_to_posts(tmp_path):
    _post(tmp_path)
    _write(tmp_path, "filters/mark.lua", MARK_LUA)
    cfg = Config(
        markdown_dir=str(tmp_path / "markdown" / "posts"),
        post_dir=str(tmp_path / "public" / "posts"),
        filter_dir=str(tmp_path / "filters"),
        data_path=str(tmp_path / "data.json"),
    )
    build_site(cfg)
    html = (tmp_path / "public" / "posts" / "1.html").read_text()
    assert "MARKED" in html
    assert "MARKME" not in html


def test_explicit_filter_entry_is_applied(tmp_path):
    _post(tmp_path)
    _write(tmp_path, "elsewhere/mark.lua", MARK_LUA)
    cfg = Config(
        markdown_dir=str(tmp_path / "markdown" / "posts"),
        post_dir=str(tmp_path / "public" / "posts"),
        filters=[str(tmp_path / "elsewhere" / "mark.lua")],
        filter_dir=str(tmp_path / "unused"),
        data_path=str(tmp_path / "data.json"),
    )
    build_site(cfg)
    assert "MARKED" in (tmp_path / "public" / "posts" / "1.html").read_text()


def test_no_filters_leaves_markdown_untouched(tmp_path):
    _post(tmp_path)
    cfg = Config(
        markdown_dir=str(tmp_path / "markdown" / "posts"),
        post_dir=str(tmp_path / "public" / "posts"),
        filter_dir=str(tmp_path / "none"),
        data_path=str(tmp_path / "data.json"),
    )
    build_site(cfg)
    html = (tmp_path / "public" / "posts" / "1.html").read_text()
    assert "MARKME" in html
    assert "MARKED" not in html


# --- CLI ------------------------------------------------------------------


def test_cli_gallery_flag_still_enables_gallery(site, tmp_path):
    from essayist import cli

    cfg_file = tmp_path / "essayist.toml"
    cfg_file.write_text(
        f'markdown_dir = "{site / "markdown" / "posts"}"\n'
        f'post_dir = "{tmp_path / "public" / "posts"}"\n'
        f'data_path = "{tmp_path / "data.json"}"\n'
        f'filter_dir = "{tmp_path / "none"}"\n'
    )
    assert cli.main(["build", "--config", str(cfg_file), "--gallery"]) == 0
    assert (tmp_path / "public" / "posts" / "1.html").exists()


def test_cli_filter_flag_adds_a_filter(tmp_path):
    from essayist import cli

    lua_file = tmp_path / "mark.lua"
    lua_file.write_text(MARK_LUA)
    _post(tmp_path / "site", body="MARKME here")
    cfg_file = tmp_path / "essayist.toml"
    cfg_file.write_text(
        f'markdown_dir = "{tmp_path / "site" / "markdown" / "posts"}"\n'
        f'post_dir = "{tmp_path / "site" / "public" / "posts"}"\n'
        f'data_path = "{tmp_path / "data.json"}"\n'
        f'filter_dir = "{tmp_path / "none"}"\n'
    )
    assert cli.main(["build", "--config", str(cfg_file), "--filter", str(lua_file)]) == 0
    html = (tmp_path / "site" / "public" / "posts" / "1.html").read_text()
    assert "MARKED" in html


def test_cli_filter_dir_overrides_config(tmp_path):
    from essayist import cli

    _write(tmp_path, "myfilters/mark.lua", MARK_LUA)
    _post(tmp_path / "site", body="MARKME here")
    cfg_file = tmp_path / "essayist.toml"
    cfg_file.write_text(
        f'markdown_dir = "{tmp_path / "site" / "markdown" / "posts"}"\n'
        f'post_dir = "{tmp_path / "site" / "public" / "posts"}"\n'
        f'data_path = "{tmp_path / "data.json"}"\n'
        f'filter_dir = "{tmp_path / "none"}"\n'
    )
    assert (
        cli.main(
            ["build", "--config", str(cfg_file), "--filter-dir", str(tmp_path / "myfilters")]
        )
        == 0
    )
    html = (tmp_path / "site" / "public" / "posts" / "1.html").read_text()
    assert "MARKED" in html


@pytest.mark.parametrize("flag", ["--filter", "--filter-dir", "--gallery"])
def test_cli_exposes_filter_flags(flag, capsys):
    from essayist import cli

    with pytest.raises(SystemExit):
        cli.main(["build", "--help"])
    assert flag in capsys.readouterr().out
