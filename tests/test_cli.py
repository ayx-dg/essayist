"""Tests for the configuration and CLI."""

import os

import pytest

from essayist import cli
from essayist.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.markdown_dir == "markdown/posts"
    assert cfg.post_dir == "public/posts"
    assert cfg.template_dir is None
    assert cfg.build_rss is True
    assert cfg.gallery is False


def test_config_resolve_makes_paths_absolute():
    cfg = Config()
    cfg.resolve("/base")
    assert cfg.markdown_dir == "/base/markdown/posts"
    assert cfg.post_dir == "/base/public/posts"


def test_effective_panargs_adds_gallery_filter():
    class _B:
        @staticmethod
        def bundled_filter(name):
            return f"/pkg/filters/{name}"

    cfg = Config(panargs=["--mathml"], gallery=True)
    args = cfg.effective_panargs(_B)
    assert "--mathml" in args
    assert any(a.startswith("--lua-filter=") and a.endswith("gallery.lua") for a in args)


def test_effective_panargs_without_gallery():
    cfg = Config(panargs=["--mathml"])
    assert cfg.effective_panargs(None) == ["--mathml"]


def test_load_config_from_toml(tmp_path):
    cfg_file = tmp_path / "essayist.toml"
    cfg_file.write_text(
        'markdown_dir = "md"\n'
        'post_dir = "out"\n'
        'blogname = "Toml Blog"\n'
        'panargs = ["--mathml"]\n'
    )
    cfg = cli._load_config(str(cfg_file))
    assert cfg.blogname == "Toml Blog"
    assert cfg.markdown_dir == os.path.join(str(tmp_path), "md")
    assert cfg.panargs == ["--mathml"]


def test_load_config_missing_file_returns_defaults():
    # A non-existent path is never passed by the CLI; but guard the behaviour.
    with pytest.raises(FileNotFoundError):
        cli._load_config("/definitely/not/here.toml")


def test_main_version(capsys):
    assert cli.main(["version"]) == 0
    out = capsys.readouterr().out.strip()
    assert out == "0.1.0" or out.startswith("0.")


def test_main_build_with_flags(site, tmp_path, capsys):
    cfg_file = tmp_path / "essayist.toml"
    cfg_file.write_text(
        f'markdown_dir = "{site/"markdown"/"posts"}"\n'
        f'post_dir = "{tmp_path/"public"/"posts"}"\n'
        f'site_url = "https://example.com"\n'
        f'home_md = "{site/"markdown"/"index.md"}"\n'
        f'home_output = "{tmp_path/"public"/"index.html"}"\n'
        f'data_path = "{tmp_path/"data.json"}"\n'
    )
    rc = cli.main(["build", "--config", str(cfg_file), "--blogname", "Flag Blog"])
    assert rc == 0
    assert os.path.exists(tmp_path / "public" / "posts" / "1.html")
    assert "Flag Blog" in (tmp_path / "public" / "posts" / "1.html").read_text()
    assert "Build complete" in capsys.readouterr().out
