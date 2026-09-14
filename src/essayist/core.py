"""Read Markdown files and write HTML pages."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

import yaml

BODY_TEMPLATE = '$if(toc)$\n<nav id="TOC">\n    $toc$\n</nav>\n$endif$\n$body$\n'


def read(path: str) -> str:
    """Read one text file."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path: str, text: str) -> None:
    """Write one text file. Makes the folder when it is missing."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def inside_essayist(*parts: str) -> str:
    """Path of a file that lives inside the installed essayist."""
    from importlib.resources import as_file, files

    with as_file(files("essayist").joinpath(*parts)) as p:
        return str(p)


def templates_folder() -> str:
    """The folder with the Jinja2 files that come with essayist."""
    return inside_essayist("templates")


def filters_folder() -> str:
    """The folder with the filter files that come with essayist."""
    return inside_essayist("filters")


def pandoc(content: str, flags: list[str] | None = None) -> str:
    """Run Pandoc on ``content`` and return HTML."""
    flags = list(flags or [])
    temp_path = None
    if not any(f.startswith("--template=") for f in flags):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".html", delete=False, encoding="utf-8"
        ) as tf:
            tf.write(BODY_TEMPLATE)
            temp_path = tf.name
        flags.append(f"--template={temp_path}")
    try:
        proc = subprocess.Popen(
            ["pandoc", *flags],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, err = proc.communicate(input=content)
    finally:
        if temp_path:
            os.remove(temp_path)
    if err.strip():
        print(f"pandoc: {err.strip()}", file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"pandoc failed ({proc.returncode}): {err.strip()}")
    return out


def text_file_to_string(filename: str) -> str:
    """Read a text file and return its contents."""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def top_block(text: str) -> dict | None:
    """Read the ``---`` block at the top of a Markdown file."""
    if not text.startswith("---"):
        return None
    lines: list[str] = []
    inside = False
    for line in text.split("\n"):
        if line.startswith("---") and not inside:
            inside = True
            continue
        if line.startswith("---") and inside:
            break
        if inside:
            lines.append(line)
    data = yaml.load("\n".join(lines), Loader=yaml.FullLoader)
    if data and "title" in data:
        data["title"] = str(data["title"])
    return data


class Blog:
    """One Blog object reads one source and writes one output place.

    Give it a folder and it writes one page per Markdown file. Give it a single
    file and it writes one page.

    The normal setup is two Blog objects:

    - one for the posts: ``Blog("markdown/posts", "public/posts")``
    - one for the home page: ``Blog("markdown/index.md", "public/index.html")``
    """

    def __init__(
        self,
        source: str,
        output: str,
        template=None,
        filters=(),
        pandoc_args=(),
        name: str = "",
        url: str = "",
        google_group: str = "",
        css: str | None = None,
        filter_dir: str | None = None,
    ):
        self.source = source
        self.output = output
        self.template = template
        self.filters = list(filters)
        self.pandoc_args = list(pandoc_args)
        self.name = name
        self.url = (url or "https://example.com").rstrip("/")
        self.google_group = google_group
        self.css = css
        self.filter_dir = filter_dir
        self.posts: list[dict] = []
        if template is not None and hasattr(template, 'dir') and os.path.isdir(template.dir):
            self.template_dir = template.dir
        else:
            self.template_dir = None

    # --- where things go -------------------------------------------------

    @property
    def out_dir(self) -> str:
        """The folder that output goes into."""
        if self.output.endswith(".html"):
            return os.path.dirname(self.output) or "."
        return self.output

    @property
    def link_prefix(self) -> str:
        """The web path of :attr:`out_dir`, like ``/posts``."""
        return "/" + os.path.basename(os.path.normpath(self.out_dir))

    def _out_path(self, post: dict) -> str:
        if self.output.endswith(".html"):
            return self.output
        return os.path.join(self.output, f"{post['number']}.html")

    # --- reading ---------------------------------------------------------

    @property
    def source_dir(self) -> str:
        """The folder that holds the Markdown files."""
        if os.path.isdir(self.source):
            return self.source
        return os.path.dirname(self.source) or "."

    def scan(self) -> list[dict]:
        """Read every source file. Fills and returns :attr:`posts`."""
        if os.path.isdir(self.source):
            names = [n for n in os.listdir(self.source) if n.endswith(".md")]
        else:
            names = [os.path.basename(self.source)]
        paths = [os.path.join(self.source_dir, n) for n in names]
        paths.sort(key=lambda p: str((top_block(read(p)) or {}).get("date", "")))
        self.posts = [self._info(p, i) for i, p in enumerate(paths, 1)]
        return self.posts

    def _info(self, path: str, number: int) -> dict:
        meta = top_block(read(path)) or {}
        return {
            "number": number,
            "path": path,
            "link": f"{self.link_prefix}/{number}.html",
            "html_path": f"{self.link_prefix}/{number}.html",
            "title": str(meta.get("title", "")),
            "date": str(meta.get("date", "")),
            "ctime": str(meta.get("date", "")),
            "tags": meta.get("tags"),
            "publish": str(meta.get("publish", "public")),
            "meta": meta,
        }

    def _public(self) -> list[dict]:
        return [p for p in self.posts if p["publish"] == "public"]

    def _page_template(self):
        if self.template is not None:
            return self.template
        from .template import Jinja2Template

        return Jinja2Template("post.html")

    def _panargs(self) -> list[str]:
        from .filters import flags as filter_flags

        return list(self.pandoc_args) + filter_flags(self.filters, self.filter_dir)

    # --- writing ---------------------------------------------------------

    def render(self, text: str, post: dict | None = None) -> str:
        """Turn one Markdown file into one finished page."""
        meta = top_block(text) or {}
        title = str(meta.get("title", ""))
        prev_post, next_post = (None, None)
        if post is not None:
            prev_post, next_post = self._neighbours(post)
        return self._page_template().render(
            title=f"{title} | {self.name}" if self.name else title,
            heading=title,
            tags=meta.get("tags"),
            paragraphs=pandoc(text, self._panargs()),
            prev_post=prev_post,
            next_post=next_post,
            google_group_id=self.google_group,
            maillist_title=meta.get("maillist_title"),
            google_group_link=meta.get("google_group_link"),
        )

    def _neighbours(self, post: dict):
        posts = self._public()
        for i, item in enumerate(posts):
            if item["path"] == post["path"]:
                return (
                    posts[i - 1] if i > 0 else None,
                    posts[i + 1] if i < len(posts) - 1 else None,
                )
        return None, None

    def _neighbours_with_html_path(self, post: dict):
        prev, next_ = self._neighbours(post)
        return (
            {**prev, "html_path": prev["html_path"]} if prev else None,
            {**next_, "html_path": next_["html_path"]} if next_ else None,
        )

    def copy_assets(self) -> None:
        """Copy files that are not Markdown from source folder to output."""
        if not os.path.isdir(self.source_dir):
            return
        dst = self.out_dir
        for folder, _dirs, names in os.walk(self.source_dir):
            for name in names:
                if name.endswith(".md"):
                    continue
                src = os.path.join(folder, name)
                target = os.path.join(dst, os.path.relpath(src, self.source_dir))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(src, target)

    def build(self) -> "Blog":
        """Render every source file."""
        self.scan()
        if os.path.isdir(self.source):
            self.copy_assets()
        for post in self.posts:
            if post["publish"] == "draft":
                for name in (f"{post['number']}.html",):
                    try:
                        os.remove(os.path.join(self.out_dir, name))
                    except FileNotFoundError:
                        pass
                continue
            write(self._out_path(post), self.render(read(post["path"]), post))
        if self.css:
            shutil.copy2(self.css, os.path.join(self.out_dir, "style-note.css"))
        return self

    def _make_template(self, name: str) -> Jinja2Template:
        """Create a Jinja2Template, falling back to essayist defaults if not found."""
        from .template import Jinja2Template

        if self.template_dir and os.path.isfile(os.path.join(self.template_dir, name)):
            return Jinja2Template(name, dir=self.template_dir)
        return Jinja2Template(name)

    def build_index(self, path: str | None = None, title: str = "Index", template=None) -> str:
        """Write a page that lists every public post. Returns its path."""
        from .template import Jinja2Template

        if template is None:
            template = self._make_template("index.html")
        out = path or os.path.join(self.out_dir, "index.html")
        posts = [
            {"title": p["title"], "date": p["date"], "ctime": p["ctime"], "html_path": p["html_path"]}
            for p in self._public()
        ]
        write(out, template.render(posts=posts[::-1], title=title, blogname=self.name))
        return out

    def build_rss(self, path: str | None = None) -> str:
        """Write an RSS feed of every post that is not a draft."""
        out = path or os.path.join(self.out_dir, "rss.xml")
        items = ""
        for post in sorted(self.posts, key=lambda p: p["date"], reverse=True):
            if post["publish"] == "draft":
                continue
            link = self.url + post["html_path"]
            body = pandoc(read(post["path"]), ["--mathml", "-V", "title:"])
            date = post["date"].split(" ")[0]
            items += (
                "\n<item>"
                f"<title>{post['title']}</title>"
                f"<link>{link}</link>"
                f"<description>{post['title']}</description>"
                f"<content:encoded><![CDATA[{body}]]></content:encoded>"
                f"<pubDate>{datetime.strptime(date, '%Y-%m-%d')}</pubDate>"
                f"<guid>{link}</guid>"
                "</item>"
            )
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"'
            ' xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
            "<channel>"
            f"<title>{self.name or self.url}</title>"
            f'<atom:link href="{self.url}{self.link_prefix}/rss.xml"'
            ' rel="self" type="application/rss+xml" />'
            f"{items}\n</channel>\n</rss>"
        )
        write(out, xml)
        return out

    def render_page(self, content: str, template_name, pandoc_args: list[str] | None = None, meta: dict | None = None) -> str:
        """Render a single page with a given template."""
        from .template import Jinja2Template

        panargs = list(self.pandoc_args) + (list(pandoc_args) if pandoc_args else [])
        post_meta = top_block(content) or {}
        title = str(post_meta.get("title", ""))
        tags = post_meta.get("tags")
        body_html = pandoc(content, panargs)

        if isinstance(template_name, Jinja2Template):
            template = template_name
        else:
            template = self._make_template(template_name)

        prev_post, next_post = (None, None)

        data = {
            "title": f"{title} | {self.name}" if self.name else title,
            "heading": title,
            "tags": tags,
            "paragraphs": body_html,
            "google_group_id": self.google_group,
            "maillist_title": post_meta.get("maillist_title"),
            "google_group_link": post_meta.get("google_group_link"),
            "prev_post": prev_post,
            "next_post": next_post,
            **(meta or {}),
        }
        return template.render(**data)

    def write_page(self, output: str, title: str, post_dir: str = None) -> None:
        """Write a rendered page to the output directory."""
        dst = post_dir or self.out_dir
        os.makedirs(dst, exist_ok=True)
        write(os.path.join(dst, f"{title}.html"), output)
