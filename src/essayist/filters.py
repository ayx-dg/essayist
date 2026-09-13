"""Pandoc filters.

A filter changes the page while Pandoc reads it.

Point at a filter in one of three ways:

1. a path, like ``filters/up.lua``
2. a file name inside a filter folder, like ``up`` (means ``up.lua`` there)
3. a bundle file name, like ``gallery``

A **bundle file** is a filter that ships inside essayist. You write its name
with no ``.lua`` ending.
"""

from __future__ import annotations

import os
from pathlib import Path

from .core import bundled_path


def flag(path: str) -> str:
    """The Pandoc flag that loads one filter file.

    ``.lua`` files use ``--lua-filter``. Every other file uses ``--filter``
    and is run as a program.
    """
    return f"--lua-filter={path}" if path.endswith(".lua") else f"--filter={path}"


def bundle_files() -> list[str]:
    """Names of the bundle files, like ``['gallery.lua']``."""
    return sorted(p.name for p in Path(bundled_path("filters")).glob("*.lua"))


def bundle_path(name: str) -> str:
    """Path of one bundle file. ``gallery`` and ``gallery.lua`` both work."""
    if not name.endswith(".lua"):
        name += ".lua"
    return bundled_path("filters", name)


def find(name: str, filter_dir: str | None = None) -> str | None:
    """Find one filter file. Returns ``None`` when nothing matches.

    Order: path, then file inside ``filter_dir``, then bundle file.
    """
    if os.path.isfile(name):
        return name
    if filter_dir:
        for candidate in (
            os.path.join(filter_dir, name),
            os.path.join(filter_dir, name + ".lua"),
        ):
            if os.path.isfile(candidate):
                return candidate
    path = bundle_path(name)
    return path if os.path.isfile(path) else None


def discover(filter_dir: str | None) -> list[str]:
    """Every ``*.lua`` file inside ``filter_dir``, sorted by name."""
    if not filter_dir or not os.path.isdir(filter_dir):
        return []
    return [str(p) for p in sorted(Path(filter_dir).glob("*.lua"))]


def all_flags(names=(), filter_dir: str | None = None) -> list[str]:
    """Pandoc flags for ``names`` plus every file found in ``filter_dir``.

    No flag is repeated. Names that match nothing are skipped.
    """
    out: list[str] = []
    paths = [find(n, filter_dir) for n in names] + discover(filter_dir)
    for path in paths:
        if not path:
            continue
        one = flag(path)
        if one not in out:
            out.append(one)
    return out
