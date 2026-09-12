"""Static site generator core.

Provides the :class:`Blog` class for rendering Markdown posts into HTML via
Pandoc and Jinja2, plus helpers for metadata extraction, asset copying, index
and RSS generation.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

# ---------------------------------------------------------------------------
# Utilities (pure functions, no class dependency)
# ---------------------------------------------------------------------------


def text_file_to_string(filename: str) -> str:
    """Read a text file and return its contents as a string."""
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def pandoc_filter_flag(path: str) -> str:
    """Return the pandoc CLI flag that loads ``path`` as a filter.

    ``.lua`` files are loaded in-process with ``--lua-filter``; anything else is
    assumed to be a JSON-filter executable and loaded with ``--filter``.
    """
    return f"--lua-filter={path}" if path.endswith(".lua") else f"--filter={path}"


def pandoc(content: str, flags: list[str] | None = None) -> str:
    """Render Markdown ``content`` to HTML using the pandoc CLI.

    A minimal standalone template is used so that only the document body (and
    an optional table of contents) is produced, leaving full page layout to the
    Jinja2 templates.
    """
    if flags is None:
        flags = []
    template = (
        "$if(toc)$\n<nav id=\"TOC\">\n    $toc$\n</nav>\n$endif$\n$body$\n"
    )
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", delete=False, encoding="utf-8"
    ) as tf:
        tf.write(template)
        template_path = tf.name
    try:
        proc = subprocess.Popen(
            ["pandoc", *flags, f"--template={template_path}"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = proc.communicate(input=content)
    finally:
        os.remove(template_path)
    if stderr.strip():
        print(f"pandoc stderr: {stderr.strip()}", file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError(
            f"pandoc failed with exit code {proc.returncode}: {stderr.strip()}"
        )
    return stdout


# ---------------------------------------------------------------------------
# Blog class
# ---------------------------------------------------------------------------


class Blog:
    """Render Markdown posts into a static site."""

    def __init__(
        self,
        *,
        markdown_dir: str,
        post_dir: str,
        template_dir: str | None = None,
        meta: dict | None = None,
        panargs: list[str] | None = None,
        data_path: str = "data.json",
        site_url: str = "",
    ):
        self.markdown_dir = markdown_dir
        self.post_dir = post_dir
        self.template_dir = template_dir
        self.meta = meta or {}
        self.default_panargs = panargs or []
        self.data_path = data_path
        self.site_url = site_url.rstrip("/")
        if template_dir:
            self.env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.env = Environment(loader=FileSystemLoader(self._bundled_templates()))

    # --- bundled resources -------------------------------------------------

    @staticmethod
    def _bundled_templates() -> str:
        from importlib.resources import as_file, files

        with as_file(files("essayist").joinpath("templates")) as p:
            return str(p)

    @staticmethod
    def _filters_dir() -> str:
        from importlib.resources import as_file, files

        with as_file(files("essayist").joinpath("filters")) as p:
            return str(p)

    @classmethod
    def bundled_filters(cls) -> list[str]:
        """Names of the pandoc filters bundled with the package."""
        return sorted(p.name for p in Path(cls._filters_dir()).glob("*.lua"))

    @classmethod
    def bundled_filter(cls, name: str) -> str:
        """Return the filesystem path of a bundled pandoc lua filter."""
        if not name.endswith(".lua"):
            name += ".lua"
        return os.path.join(cls._filters_dir(), name)

    # --- private helpers ---------------------------------------------------

    @staticmethod
    def _get_metadata(markdown_content: str) -> str:
        if not markdown_content.startswith("---"):
            raise ValueError("No metadata block")
        in_block = False
        lines = []
        for line in markdown_content.split("\n"):
            if line.startswith("---") and not in_block:
                in_block = True
                continue
            elif line.startswith("---") and in_block:
                break
            if in_block:
                lines.append(line)
        return "\n".join(lines)

    def _process_metadata(self, markdown_content: str) -> dict | None:
        try:
            raw = self._get_metadata(markdown_content)
            data: dict = yaml.load(raw, Loader=yaml.FullLoader)
            if data and "title" in data:
                data["title"] = str(data["title"])
            return data
        except ValueError:
            return None

    def _get_title(self, content: str) -> str:
        meta = self._process_metadata(content)
        return meta["title"] if meta else ""

    def _get_tags(self, content: str) -> list | None:
        meta = self._process_metadata(content)
        return meta.get("tags") if meta else None

    @staticmethod
    def _post_visibility(metadata: dict | None) -> str:
        if metadata and "publish" in metadata:
            return metadata["publish"]
        return "public"

    def _file_ctime(self, filename: str) -> str:
        content = text_file_to_string(filename)
        meta = self._process_metadata(content)
        return str(meta["date"]) if meta and "date" in meta else ""

    @staticmethod
    def _rss_time(time_str: str) -> datetime:
        input_str = " ".join(time_str.split(" ")[:2]).strip()
        return datetime.strptime(input_str, "%Y-%m-%d")

    # --- single page rendering --------------------------------------------

    def render_page(
        self,
        content: str,
        template_name: str,
        meta: dict | None = None,
        panargs: list[str] | None = None,
        filename: str | None = None,
    ) -> str:
        meta = meta or self.meta
        panargs = panargs or self.default_panargs
        post_meta = self._process_metadata(content)
        title = post_meta["title"] if post_meta else ""
        tags = post_meta.get("tags") if post_meta else None

        prev_post, next_post = (None, None)
        if filename:
            prev_post, next_post = self._prev_next(filename)

        body_html = pandoc(content, panargs)
        template = self.env.get_template(template_name)

        data = {
            "title": (
                f"{title} | {meta.get('blogname', '')}"
                if meta.get("blogname")
                else title
            ),
            "google_group_id": meta.get("google_group_id"),
            "heading": title,
            "tags": tags,
            "paragraphs": body_html,
            "maillist_title": post_meta.get("maillist_title") if post_meta else None,
            "google_group_link": (
                post_meta.get("google_group_link") if post_meta else None
            ),
            "prev_post": prev_post,
            "next_post": next_post,
        }
        return template.render(data)

    def write_page(self, output: str, title: str, post_dir: str | None = None) -> None:
        dst = post_dir or self.post_dir
        os.makedirs(dst, exist_ok=True)
        with open(f"{dst}/{title}.html", "w", encoding="utf-8") as f:
            f.write(output)

    # --- data management ---------------------------------------------------

    def update_data(self) -> None:
        data = []
        posts = sorted(
            [p for p in os.listdir(self.markdown_dir) if p.endswith(".md")],
            key=lambda md: self._file_ctime(f"{self.markdown_dir}/{md}"),
        )
        for count, md in enumerate(posts, 1):
            path = f"{self.markdown_dir}/{md}"
            content = text_file_to_string(path)
            meta = self._process_metadata(content)
            data.append(
                {
                    "title": self._get_title(content),
                    "tags": self._get_tags(content),
                    "html_path": f"/posts/{count}.html",
                    "md_path": path,
                    "ctime": self._file_ctime(path),
                    "publish": self._post_visibility(meta),
                }
            )
        with open(self.data_path, "w") as f:
            json.dump(data, f)

    def _name_a_file(self, filename: str) -> int | None:
        with open(self.data_path, "r") as f:
            data = json.load(f)
        for i, post in enumerate(data, 1):
            if post["md_path"] == filename:
                return i
        return None

    def _prev_next(self, filename: str):
        with open(self.data_path, "r") as f:
            data = json.load(f)
        posts = [p for p in data if p["publish"] == "public"]
        for i, post in enumerate(posts):
            if post["md_path"] == filename:
                prev = posts[i - 1] if i > 0 else None
                next = posts[i + 1] if i < len(posts) - 1 else None
                return prev, next
        return None, None

    # -- copy files that are not markdown --

    def copy_assets(self, src: str, dst: str) -> None:
        from pathlib import Path

        src_path = Path(src)
        dst_path = Path(dst)
        dst_path.mkdir(parents=True, exist_ok=True)

        for file in src_path.rglob("*"):
            if file.is_file() and not file.name.endswith(".md"):
                rel_path = file.relative_to(src_path)
                target = dst_path / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, target)

    # --- build posts -------------------------------------------------------

    def build_posts(self, updated=lambda x: True) -> None:
        self.copy_assets(self.markdown_dir, self.post_dir)

        for file in os.listdir(self.markdown_dir):
            if not file.endswith(".md"):
                continue
            path = f"{self.markdown_dir}/{file}"
            if not updated(path):
                continue

            content = text_file_to_string(path)
            meta = self._process_metadata(content)
            visibility = self._post_visibility(meta)

            if visibility == "draft":
                num = self._name_a_file(path)
                if num:
                    for p in [f"{self.post_dir}/{num}", f"{self.post_dir}/{num}.html"]:
                        try:
                            os.remove(p)
                        except FileNotFoundError:
                            pass
                continue

            output = self.render_page(content, "post.html", filename=path)
            self.write_page(output, title=str(self._name_a_file(path)))

    # --- build index page --------------------------------------------------

    def build_index(self, index_path: str | None = None, index_title: str = "Index") -> None:
        index_path = index_path or self.post_dir
        with open(self.data_path, "r") as f:
            data = list(filter(lambda x: x["publish"] == "public", json.load(f)))
        template = self.env.get_template("index.html")
        output = template.render(
            posts=list(data)[::-1], title=index_title, path=index_path
        )
        os.makedirs(index_path, exist_ok=True)
        with open(f"{index_path}/index.html", "w", encoding="utf-8") as f:
            f.write(output)

    # --- build RSS ---------------------------------------------------------

    def build_rss(self, rss_path: str) -> None:
        site_url = self.site_url or "https://example.com"
        with open(self.data_path, "r") as f:
            data = json.load(f)

        rss_template = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:admin="http://webns.net/mvcb/"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <channel>
    <title>{title}</title>
    <atom:link href="{site_url}/rss.xml" rel="self" type="application/rss+xml" />
    {items}
  </channel>
</rss>"""

        items = ""
        for post in sorted(data, key=lambda x: x.get("ctime", ""), reverse=True):
            # Only drafts are hidden: "unlisted" posts are served in the feed
            # but kept out of the index page.
            if post.get("publish") == "draft":
                continue
            with open(post["md_path"], "r") as pf:
                body = pandoc(pf.read(), ["--mathml", "-V", "title:"])
            link = f"{site_url}/{post['html_path'].lstrip('/')}"
            items += f"""
            <item>
                <title>{post['title']}</title>
                <link>{link}</link>
                <description>{post['title']}</description>
                <content:encoded><![CDATA[{body}]]></content:encoded>
                <pubDate>{self._rss_time(post['ctime'])}</pubDate>
                <guid>{link}</guid>
            </item>"""

        rss_output = rss_template.format(
            title=self.meta.get("blogname") or site_url,
            site_url=site_url,
            items=items,
        )
        os.makedirs(os.path.dirname(rss_path), exist_ok=True)
        with open(rss_path, "w") as f:
            f.write(rss_output)
