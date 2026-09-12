"""The shipped example configuration must stay valid and loadable."""

import os

from essayist import cli
from essayist.config import Config

EXAMPLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "essayist.example.toml")


def test_example_config_parses():
    assert os.path.exists(EXAMPLE)
    cfg = cli._load_config(EXAMPLE)
    assert isinstance(cfg, Config)
    assert cfg.blogname == "My Blog"
    assert cfg.gallery is False
    assert cfg.panargs == ["--mathml", "--toc"]


def test_example_config_paths_are_resolved():
    cfg = cli._load_config(EXAMPLE)
    base = os.path.dirname(EXAMPLE)
    assert cfg.markdown_dir == os.path.join(base, "markdown/posts")
    assert cfg.post_dir == os.path.join(base, "public/posts")
    assert cfg.home_output == os.path.join(base, "public/index.html")
