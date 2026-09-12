"""Command line interface for the static site generator."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import fields

try:  # Python >= 3.11
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from .builder import build_site
from .config import Config


def _load_config(path: str | None) -> Config:
    """Load a :class:`Config` from a TOML file, if given."""
    if not path:
        return Config()
    with open(path, "rb") as f:
        data = tomllib.load(f)
    # Accept either a top-level table or a [tool.essayist] table.
    cfg = data.get("essayist", data)
    known = {f.name for f in fields(Config)}
    kwargs = {k: v for k, v in cfg.items() if k in known}
    base = os.path.dirname(os.path.abspath(path))
    config = Config(**kwargs)
    config.resolve(base)
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="essayist",
        description="A Pandoc + Jinja2 static site generator.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="Build the static site.")
    p_build.add_argument(
        "-c", "--config", default="essayist.toml", help="Path to TOML config file."
    )
    p_build.add_argument("--markdown-dir", help="Directory with Markdown posts.")
    p_build.add_argument("--post-dir", help="Output directory for posts.")
    p_build.add_argument("--template-dir", help="Directory with Jinja2 templates.")
    p_build.add_argument("--blogname", help="Blog name shown in page titles.")
    p_build.add_argument("--site-url", help="Base URL used in RSS feeds.")
    p_build.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Pandoc filter: a path, a file inside the filter directory, or the "
            "name of a bundled filter such as 'gallery'. Repeatable."
        ),
    )
    p_build.add_argument(
        "--filter-dir",
        help="Directory scanned for *.lua pandoc filters (default: filters).",
    )
    p_build.add_argument(
        "--gallery",
        action="store_true",
        help="Shorthand for --filter gallery.",
    )
    p_build.set_defaults(func=_cmd_build)

    sub.add_parser("version", help="Print the package version.").set_defaults(
        func=_cmd_version
    )
    return parser


def _cmd_build(args: argparse.Namespace) -> int:
    config = _load_config(args.config)
    # CLI flags override the config file.
    for key in (
        "markdown_dir",
        "post_dir",
        "template_dir",
        "filter_dir",
        "blogname",
        "site_url",
    ):
        value = getattr(args, key, None)
        if value:
            setattr(config, key, value)
    if args.filter:
        config.filters = list(config.filters) + list(args.filter)
    if args.gallery:
        config.gallery = True
    build_site(config)
    print("Build complete")
    return 0


def _cmd_version(args: argparse.Namespace) -> int:
    from . import __version__

    print(__version__)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
