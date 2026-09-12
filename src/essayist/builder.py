"""High level build orchestration."""

from __future__ import annotations

import os
import shutil

from .config import Config
from .core import Blog, text_file_to_string


def build_site(config: Config) -> Blog:
    """Run a full site build described by ``config`` and return the Blog."""
    meta = {}
    if config.blogname:
        meta["blogname"] = config.blogname
    if config.google_group_id:
        meta["google_group_id"] = config.google_group_id

    blog = Blog(
        markdown_dir=config.markdown_dir,
        post_dir=config.post_dir,
        template_dir=config.template_dir,
        meta=meta,
        data_path=config.data_path,
        site_url=config.site_url,
    )
    # set effective panargs (with bundled gallery filter if requested)
    blog.default_panargs = config.effective_panargs(blog)

    blog.update_data()
    blog.build_posts()

    if config.style_css:
        dst_dir = os.path.dirname(os.path.join(config.post_dir, "style-note.css"))
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(config.style_css, os.path.join(config.post_dir, "style-note.css"))

    if config.build_index:
        blog.build_index(index_path=config.post_dir, index_title=config.index_title)

    if config.build_rss:
        rss_path = config.rss_path or os.path.join(config.post_dir, "rss.xml")
        blog.build_rss(rss_path=rss_path)

    if config.home_md:
        home_html = blog.render_page(
            content=text_file_to_string(config.home_md),
            template_name=config.home_template,
            meta={},
            panargs=["--mathml"],
        )
        home_dir = os.path.dirname(config.home_output)
        os.makedirs(home_dir, exist_ok=True)
        with open(config.home_output, "w", encoding="utf-8") as f:
            f.write(home_html)

    return blog
