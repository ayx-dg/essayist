"""Configuration model for the static site generator."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from .core import pandoc_filter_flag


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
    filters: list[str] = field(default_factory=list)
    filter_dir: str = "filters"
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
                "filter_dir",
            ):
                if isinstance(value, str) and value and not os.path.isabs(value):
                    setattr(self, f.name, os.path.join(base, value))

    def effective_panargs(self, blog: Any) -> list[str]:
        """Return pandoc args with the configured filter flags appended."""
        return list(self.panargs) + self.filter_flags(blog)

    def filter_flags(self, blog: Any) -> list[str]:
        """Build the ``--lua-filter`` / ``--filter`` flags for this config.

        Filters come from three sources, in this order: the ``gallery``
        shortcut, the explicit :attr:`filters` list, and every ``*.lua`` file
        found in :attr:`filter_dir`. A flag already listed in :attr:`panargs`
        is never repeated.
        """
        flags: list[str] = []

        def add(path: str) -> None:
            flag = pandoc_filter_flag(path)
            if flag not in self.panargs and flag not in flags:
                flags.append(flag)

        if self.gallery and blog is not None:
            add(blog.bundled_filter("gallery"))
        for entry in self.filters:
            path = self.resolve_filter(entry, blog)
            if path:
                add(path)
        for path in self.discovered_filters():
            add(path)
        return flags

    def discovered_filters(self) -> list[str]:
        """Every ``*.lua`` file in :attr:`filter_dir`, sorted by name."""
        if not self.filter_dir or not os.path.isdir(self.filter_dir):
            return []
        return [str(p) for p in sorted(Path(self.filter_dir).glob("*.lua"))]

    def resolve_filter(self, entry: str, blog: Any = None) -> str | None:
        """Resolve one :attr:`filters` entry to a path, or ``None``.

        An entry may be a path, the name of a file inside :attr:`filter_dir`
        (with or without the ``.lua`` suffix), or the name of a filter bundled
        with the package, such as ``gallery``.
        """
        candidates: list[str] = []
        if os.path.isabs(entry):
            candidates.append(entry)
        else:
            if self.filter_dir:
                candidates.append(os.path.join(self.filter_dir, entry))
                if not entry.endswith(".lua"):
                    candidates.append(os.path.join(self.filter_dir, entry + ".lua"))
            candidates.append(entry)
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

        if blog is None or not hasattr(blog, "bundled_filters"):
            return None
        name = entry if entry.endswith(".lua") else entry + ".lua"
        if name in blog.bundled_filters():
            path = blog.bundled_filter(name)
            if os.path.isfile(path):
                return path
        return None
