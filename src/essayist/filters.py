"""Pandoc filters.

A filter changes the page while Pandoc reads it.

Name a filter in one of three ways:

1. a path, like ``filters/up.lua``
2. a file name inside your filter folder, like ``up`` (means ``up.lua``)
3. a filter that comes with essayist, like ``gallery``

essayist comes with its own filters in a folder inside the package. Write their
names with no ``.lua`` ending.
"""

from __future__ import annotations

import os
from pathlib import Path

from .core import filters_folder


def flag_for(path: str) -> str:
    """The Pandoc flag that loads one filter file.

    ``.lua`` files use ``--lua-filter``. Every other file uses ``--filter``
    and is run as a program.
    """
    return f"--lua-filter={path}" if path.endswith(".lua") else f"--filter={path}"


def included() -> list[str]:
    """File names of the filters that come with essayist."""
    return sorted(p.name for p in Path(filters_folder()).glob("*.lua"))


def included_path(name: str) -> str:
    """Path of a filter that comes with essayist.

    ``gallery`` and ``gallery.lua`` both work.
    """
    if not name.endswith(".lua"):
        name += ".lua"
    return os.path.join(filters_folder(), name)


def find(name: str, folder: str | None = None) -> str | None:
    """Find one filter file. Returns ``None`` when nothing matches.

    Order: path, then file inside ``folder``, then a filter that comes with
    essayist.
    """
    if os.path.isfile(name):
        return name
    if folder:
        for candidate in (
            os.path.join(folder, name),
            os.path.join(folder, name + ".lua"),
        ):
            if os.path.isfile(candidate):
                return candidate
    path = included_path(name)
    return path if os.path.isfile(path) else None


def in_folder(folder: str | None) -> list[str]:
    """Every ``*.lua`` file inside ``folder``, sorted by name."""
    if not folder or not os.path.isdir(folder):
        return []
    return [str(p) for p in sorted(Path(folder).glob("*.lua"))]


def flags(names=(), folder: str | None = None) -> list[str]:
    """Pandoc flags for ``names`` plus every file found in ``folder``.

    No flag is repeated. Names that match nothing are skipped.
    """
    out: list[str] = []
    for path in [find(n, folder) for n in names] + in_folder(folder):
        if not path:
            continue
        one = flag_for(path)
        if one not in out:
            out.append(one)
    return out
