"""Command line wrapper around :class:`essayist.Blog`."""

from __future__ import annotations

import argparse
import os
import sys

from .core import Blog
from .template import Jinja2Template


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="essayist",
        description="Turn Markdown files into a blog.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build", help="Build pages.")
    p.add_argument("source", help="Markdown file or folder.")
    p.add_argument("output", help="HTML file or folder.")
    p.add_argument("--template", help="Jinja2 template file name.")
    p.add_argument("--template-dir", help="Folder with your Jinja2 templates.")
    p.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="NAME",
        help="Pandoc filter: path, file in --filter-dir, or bundle file. Repeatable.",
    )
    p.add_argument("--filter-dir", help="Folder scanned for *.lua filters.")
    p.add_argument("--name", default="", help="Blog name in page titles.")
    p.add_argument("--url", default="", help="Site address used in the feed.")
    p.add_argument("--group-id", default="", help="Google group for mail comments.")
    p.add_argument("--css", help="CSS file copied next to the pages.")
    p.add_argument(
        "--pandoc-arg",
        action="append",
        default=[],
        metavar="FLAG",
        help="Extra Pandoc flag, like --pandoc-arg=--mathml. Repeatable.",
    )
    p.add_argument("--no-index", action="store_true", help="Do not write the list page.")
    p.add_argument("--no-rss", action="store_true", help="Do not write the feed.")
    p.set_defaults(func=_cmd_build)

    sub.add_parser("version", help="Print the version.").set_defaults(
        func=_cmd_version
    )
    return parser


def _cmd_build(args: argparse.Namespace) -> int:
    template = None
    if args.template or args.template_dir:
        template = Jinja2Template(args.template or "post.html", dir=args.template_dir)
    blog = Blog(
        source=args.source,
        output=args.output,
        template=template,
        filters=args.filter,
        panargs=args.pandoc_arg,
        name=args.name,
        url=args.url,
        group_id=args.group_id,
        css=args.css,
        filter_dir=args.filter_dir,
    )
    blog.build()
    # A folder of posts also gets a list page and a feed.
    if os.path.isdir(args.source):
        if not args.no_index:
            blog.build_index()
        if not args.no_rss:
            blog.build_rss()
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
