"""essayist: turn Markdown files into a blog.

Pandoc reads the Markdown. A template writes the page.
"""

from __future__ import annotations

from .core import Blog, pandoc, read, text_file_to_string, top_block, write
from .template import Jinja2Template, PandocTemplate, Template

__version__ = "0.2.2"

__all__ = [
    "Blog",
    "Template",
    "Jinja2Template",
    "PandocTemplate",
    "pandoc",
    "read",
    "text_file_to_string",
    "top_block",
    "write",
    "__version__",
]
