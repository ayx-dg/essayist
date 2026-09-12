"""essayist: a Pandoc + Jinja2 static site generator.

This package turns a directory of Markdown posts (with YAML front matter) into
a static HTML site, an index page and an RSS feed.
"""

from __future__ import annotations

from .builder import build_site
from .config import Config
from .core import Blog, pandoc, text_file_to_string

__version__ = "0.1.0"

__all__ = [
    "Blog",
    "Config",
    "build_site",
    "pandoc",
    "text_file_to_string",
    "__version__",
]
