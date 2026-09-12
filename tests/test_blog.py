"""Tests for Blog metadata handling, rendering and builds.

These tests use the sample Markdown fixtures in ``tests/sample`` and write all
output into pytest's temporary directories.
"""

import json
import os
import shutil

import pytest

from essayist import Blog, build_site, text_file_to_string
from essayist.config import Config

SAMPLE = os.path.join(os.path.dirname(__file__), "sample")


def _make_blog(root, **kw):
    return Blog(
        markdown_dir=str(root / "markdown" / "posts"),
        post_dir=str(root / "public" / "posts"),
        data_path=str(root / "data.json"),
        site_url="https://example.com",
        **kw,
    )


# --- metadata -------------------------------------------------------------


def test_process_metadata_reads_front_matter(site):
    blog = _make_blog(site)
    content = text_file_to_string(str(site / "markdown" / "posts" / "welcome.md"))
    meta = blog._process_metadata(content)
    assert meta["title"] == "Welcome to SimpleBlog"
    assert meta["tags"] == ["intro", "demo"]
    assert meta["publish"] == "public"


def test_process_metadata_without_front_matter(site):
    blog = _make_blog(site)
    assert blog._process_metadata("just text\n") is None


def test_visibility_defaults_to_public(site):
    blog = _make_blog(site)
    assert blog._post_visibility(None) == "public"
    assert blog._post_visibility({"publish": "draft"}) == "draft"


def test_rss_time_parses_date(site):
    blog = _make_blog(site)
    assert blog._rss_time("2024-01-15").year == 2024
    assert blog._rss_time("2024-01-15").month == 1


# --- data index -----------------------------------------------------------


def test_update_data_indexes_posts_sorted_by_date(site):
    blog = _make_blog(site)
    blog.update_data()
    with open(site / "data.json") as f:
        data = json.load(f)
    assert len(data) == 4
    titles = [p["title"] for p in data]
    assert titles == [
        "Welcome to SimpleBlog",
        "Second Sample Post",
        "Draft Post",
        "Unlisted Sample Post",
    ]
    assert data[0]["html_path"] == "/posts/1.html"
    assert data[2]["publish"] == "draft"
    assert data[3]["publish"] == "unlisted"


def test_name_a_file_maps_round_trip(site):
    blog = _make_blog(site)
    blog.update_data()
    path = str(site / "markdown" / "posts" / "second.md")
    assert blog._name_a_file(path) == 2


def test_prev_next_excludes_drafts(site):
    blog = _make_blog(site)
    blog.update_data()
    first = str(site / "markdown" / "posts" / "welcome.md")
    second = str(site / "markdown" / "posts" / "second.md")
    prev, nxt = blog._prev_next(first)
    assert prev is None
    assert nxt["md_path"] == second


# --- rendering ------------------------------------------------------------


def test_render_page_uses_bundled_templates(site):
    blog = _make_blog(site, meta={"blogname": "Demo"})
    content = text_file_to_string(str(site / "markdown" / "posts" / "welcome.md"))
    html = blog.render_page(content, "post.html")
    assert "Welcome to SimpleBlog | Demo" in html
    assert "Welcome to SimpleBlog" in html
    assert "<p>" in html


def test_write_page_creates_file(site, tmp_path):
    out = tmp_path / "out"
    blog = _make_blog(site)
    blog.write_page("<p>hi</p>", title="1", post_dir=str(out))
    assert (out / "1.html").read_text() == "<p>hi</p>"


def test_copy_assets_skips_markdown(site, tmp_path):
    blog = _make_blog(site)
    dst = tmp_path / "assets"
    blog.copy_assets(str(site / "markdown" / "posts"), str(dst))
    files = os.listdir(dst)
    assert "welcome.md" not in files


# --- full build -----------------------------------------------------------


def test_build_posts_skips_drafts_and_creates_html(site):
    blog = _make_blog(site)
    blog.update_data()
    blog.build_posts()
    posts = sorted(os.listdir(site / "public" / "posts"))
    assert "1.html" in posts
    assert "2.html" in posts
    # draft post is index 3 and must not be rendered
    assert "3.html" not in posts
    # unlisted post is index 4: rendered, even though it is hidden from index
    assert "4.html" in posts


def test_build_index_lists_only_public_posts(site):
    blog = _make_blog(site)
    blog.update_data()
    blog.build_index(index_path=str(site / "public" / "posts"))
    html = (site / "public" / "posts" / "index.html").read_text()
    assert "Second Sample Post" in html
    assert "Draft Post" not in html
    # "unlisted" is feed-only, it must stay off the index page
    assert "Unlisted Sample Post" not in html


def test_build_rss_excludes_drafts_but_includes_unlisted(site):
    blog = _make_blog(site)
    blog.update_data()
    rss = site / "public" / "posts" / "rss.xml"
    blog.build_rss(rss_path=str(rss))
    content = rss.read_text()
    assert "Welcome to SimpleBlog" in content
    assert "Draft Post" not in content
    assert "Unlisted Sample Post" in content


def test_build_index_does_not_leak_absolute_paths(site):
    blog = _make_blog(site)
    blog.update_data()
    index_path = str(site / "public" / "posts")
    blog.build_index(index_path=index_path)
    html = (site / "public" / "posts" / "index.html").read_text()
    assert index_path not in html
    assert str(site) not in html


def test_build_rss_channel_title_uses_blogname(site):
    blog = _make_blog(site, meta={"blogname": "Demo Blog"})
    blog.update_data()
    rss = site / "public" / "posts" / "rss.xml"
    blog.build_rss(rss_path=str(rss))
    content = rss.read_text()
    assert "<title>Demo Blog</title>" in content


def test_build_rss_channel_title_falls_back_to_site_url(site):
    blog = _make_blog(site)
    blog.update_data()
    rss = site / "public" / "posts" / "rss.xml"
    blog.build_rss(rss_path=str(rss))
    content = rss.read_text()
    assert "<title>https://example.com</title>" in content


def test_render_page_mailto_link_is_well_formed(site):
    blog = _make_blog(site, meta={"google_group_id": "my-group"})
    content = (
        "---\n"
        "title: Mail Post\n"
        "date: 2024-05-01\n"
        "publish: public\n"
        "maillist_title: Say hi by email\n"
        "google_group_link: https://groups.google.com/g/my-group\n"
        "---\n"
        "\n"
        "# Mail Post\n"
    )
    html = blog.render_page(content, "post.html")
    assert "mailto:my-group@googlegroups.com" in html
    assert "mailto://" not in html
    # spaces in the subject must be percent-encoded
    assert "subject=Re:Say%20hi%20by%20email" in html
    assert "https://groups.google.com/g/my-group" in html


def test_index_page_has_no_dangling_script_tag(site):
    blog = _make_blog(site)
    blog.update_data()
    blog.build_index(index_path=str(site / "public" / "posts"))
    html = (site / "public" / "posts" / "index.html").read_text()
    assert "script.js" not in html


def test_build_site_end_to_end(site):
    cfg = Config(
        markdown_dir=str(site / "markdown" / "posts"),
        post_dir=str(site / "public" / "posts"),
        blogname="Demo Blog",
        site_url="https://example.com",
        home_md=str(site / "markdown" / "index.md"),
        home_output=str(site / "public" / "index.html"),
        data_path=str(site / "data.json"),
        panargs=["--mathml"],
    )
    build_site(cfg)
    assert (site / "public" / "posts" / "1.html").exists()
    assert (site / "public" / "posts" / "2.html").exists()
    assert (site / "public" / "posts" / "index.html").exists()
    assert (site / "public" / "posts" / "rss.xml").exists()
    assert (site / "public" / "index.html").exists()
    home = (site / "public" / "index.html").read_text()
    assert "Home Page" in home


def test_bundled_gallery_filter_resolves_to_file():
    from essayist import Blog

    path = Blog.bundled_filter("gallery.lua")
    assert os.path.isfile(path)


def test_bundled_templates_dir_exists():
    from essayist import Blog

    assert os.path.isdir(Blog._bundled_templates())
    assert os.path.isfile(os.path.join(Blog._bundled_templates(), "post.html"))
