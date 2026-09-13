"""The command line wrapper."""

import os

from essayist import cli


def test_version(capsys):
    assert cli.main(["version"]) == 0
    assert capsys.readouterr().out.strip().startswith("0.")


def test_build_a_folder_writes_posts_index_and_feed(site, tmp_path):
    out = tmp_path / "public" / "posts"
    assert (
        cli.main(
            [
                "build",
                str(site / "markdown" / "posts"),
                str(out),
                "--name",
                "Flag Blog",
                "--url",
                "https://example.com",
            ]
        )
        == 0
    )
    assert (out / "1.html").is_file()
    assert (out / "index.html").is_file()
    assert (out / "rss.xml").is_file()
    assert "Flag Blog" in (out / "1.html").read_text()


def test_build_a_single_file_writes_one_page(site, tmp_path):
    out = tmp_path / "public" / "index.html"
    assert cli.main(["build", str(site / "markdown" / "index.md"), str(out)]) == 0
    assert out.is_file()
    assert "Home Page" in out.read_text()
    assert not (tmp_path / "public" / "rss.xml").exists()


def test_no_index_and_no_rss(site, tmp_path):
    out = tmp_path / "out"
    cli.main(
        ["build", str(site / "markdown" / "posts"), str(out), "--no-index", "--no-rss"]
    )
    assert (out / "1.html").is_file()
    assert not (out / "index.html").exists()
    assert not (out / "rss.xml").exists()


def test_filter_flag_is_applied(tmp_path):
    md = tmp_path / "md"
    md.mkdir()
    (md / "a.md").write_text("---\ntitle: A\ndate: 2024-01-01\n---\n\nMARKME\n")
    lua = tmp_path / "mark.lua"
    lua.write_text(
        'function Str(el)\n  if el.text == "MARKME" then\n'
        '    return pandoc.Str("MARKED")\n  end\nend\n'
    )
    cli.main(["build", str(md), str(tmp_path / "out"), "--filter", str(lua)])
    assert "MARKED" in (tmp_path / "out" / "1.html").read_text()


def test_filter_dir_flag_is_applied(tmp_path):
    md = tmp_path / "md"
    md.mkdir()
    (md / "a.md").write_text("---\ntitle: A\ndate: 2024-01-01\n---\n\nMARKME\n")
    fd = tmp_path / "fd"
    fd.mkdir()
    (fd / "mark.lua").write_text(
        'function Str(el)\n  if el.text == "MARKME" then\n'
        '    return pandoc.Str("MARKED")\n  end\nend\n'
    )
    cli.main(["build", str(md), str(tmp_path / "out"), "--filter-dir", str(fd)])
    assert "MARKED" in (tmp_path / "out" / "1.html").read_text()


def test_template_flags(tmp_path):
    md = tmp_path / "md"
    md.mkdir()
    (md / "a.md").write_text("---\ntitle: A\ndate: 2024-01-01\n---\n\nx\n")
    tpl = tmp_path / "tpl"
    tpl.mkdir()
    (tpl / "post.html").write_text("CUSTOM {{ heading }}")
    cli.main(
        ["build", str(md), str(tmp_path / "out"), "--template-dir", str(tpl)]
    )
    assert "CUSTOM A" in (tmp_path / "out" / "1.html").read_text()


def test_pandoc_arg_flag(tmp_path):
    md = tmp_path / "md"
    md.mkdir()
    (md / "a.md").write_text("---\ntitle: A\ndate: 2024-01-01\n---\n\n$x$\n")
    cli.main(["build", str(md), str(tmp_path / "out"), "--pandoc-arg=--mathml"])
    assert "math" in (tmp_path / "out" / "1.html").read_text()


def test_cli_help_lists_the_flags(capsys):
    import pytest

    with pytest.raises(SystemExit):
        cli.main(["build", "--help"])
    out = capsys.readouterr().out
    for flag in ("--filter", "--filter-dir", "--template", "--no-rss"):
        assert flag in out
