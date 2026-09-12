"""Configuration model for the static site generator."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class Config:
    """Build configuration for a site.

    All paths are interpreted relative to the directory containing the config
    file (or the current working directory when built from kwargs).
    """

    markdown_dir: str = "markdown/posts"
    post_dir: str = "public/posts"
    template_dir: str | None = None
    blogname: str = ""
    google_group_id: str = ""
    panargs: list[str] = field(default_factory=list)
    gallery: bool = False
    build_index: bool = True
    index_title: str = "Index"
    build_rss: bool = True
    rss_path: str | None = None  # defaults to <post_dir>/rss.xml
    site_url: str = "https://example.com"
    home_md: str | None = None
    home_template: str = "home.html"
    home_output: str = "public/index.html"
    style_css: str | None = None
    data_path: str = "data.json"

    def resolve(self, base: str) -> None:
        """Make relative paths absolute with respect to ``base``."""
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name in (
                "markdown_dir",
                "post_dir",
                "template_dir",
                "rss_path",
                "home_md",
                "home_output",
                "style_css",
                "data_path",
            ):
                if isinstance(value, str) and value and not os.path.isabs(value):
                    setattr(self, f.name, os.path.join(base, value))

    def effective_panargs(self, blog: Any) -> list[str]:
        """Return pandoc args, injecting the bundled gallery filter if enabled."""
        args = list(self.panargs)
        if self.gallery and "--lua-filter" not in args:
            args.append(f"--lua-filter={blog.bundled_filter('gallery.lua')}")
        return args
