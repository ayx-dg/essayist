"""Blog: one source in, one output place."""

import os

from essayist import Blog, Jinja2Template

MARK_LUA = """function Str(el)
  if el.text == "MARKME" then
    return pandoc.Str("MARKED")
  end
end
"""


def _posts(root, **kw):
    return Blog(
        source=str(root / "markdown" / "posts"),
        output=str(root / "public" / "posts"),
        **kw,
    )


# --- where things go -----------------------------------------------------


def test_out_dir_for_a_folder(site):
    assert _posts(site).out_dir == str(site / "public" / "posts")


def test_out_dir_for_a_file(site):
    blog = Blog(str(site / "markdown" / "index.md"), str(site / "public" / "index.html"))
    assert blog.out_dir == str(site / "public")


def test_link_prefix_comes_from_the_output_folder(site):
    assert _posts(site).link_prefix == "/posts"


# --- reading -------------------------------------------------------------


def test_scan_reads_every_source_file(site):
    posts = _posts(site).scan()
    assert [p["title"] for p in posts] == [
        "Welcome to SimpleBlog",
        "Second Sample Post",
        "Draft Post",
        "Unlisted Sample Post",
    ]


def test_scan_sorts_by_date(site):
    posts = _posts(site).scan()
    assert [p["date"] for p in posts] == [
        "2024-01-15",
        "2024-02-20",
        "2024-03-01",
        "2024-04-01",
    ]


def test_scan_numbers_posts(site):
    posts = _posts(site).scan()
    assert [p["number"] for p in posts] == [1, 2, 3, 4]
    assert posts[0]["link"] == "/posts/1.html"


def test_scan_a_single_file(site):
    blog = Blog(str(site / "markdown" / "index.md"), str(site / "public" / "index.html"))
    assert len(blog.scan()) == 1


def test_publish_defaults_to_public(site):
    posts = _posts(site).scan()
    assert posts[0]["publish"] == "public"


# --- writing -------------------------------------------------------------


def test_build_writes_posts_but_not_drafts(site):
    _posts(site).build()
    out = os.listdir(site / "public" / "posts")
    assert "1.html" in out
    assert "2.html" in out
    assert "4.html" in out  # unlisted is still rendered
    assert "3.html" not in out  # draft is not


def test_build_a_single_file(site):
    Blog(
        str(site / "markdown" / "index.md"), str(site / "public" / "index.html")
    ).build()
    html = (site / "public" / "index.html").read_text()
    assert "Home Page" in html


def test_build_copies_files_that_are_not_markdown(site, tmp_path):
    (site / "markdown" / "posts" / "pic.txt").write_text("x")
    blog = Blog(
        str(site / "markdown" / "posts"), str(tmp_path / "out"), name="N"
    )
    blog.build()
    assert (tmp_path / "out" / "pic.txt").is_file()
    assert not (tmp_path / "out" / "welcome.md").exists()


def test_build_copies_the_css_file(site, tmp_path):
    css = tmp_path / "my.css"
    css.write_text("body{}")
    Blog(str(site / "markdown" / "posts"), str(tmp_path / "out"), css=str(css)).build()
    assert (tmp_path / "out" / "style-note.css").is_file()


def test_blog_name_goes_into_the_page_title(site, tmp_path):
    Blog(str(site / "markdown" / "posts"), str(tmp_path / "out"), name="My Blog").build()
    assert "Welcome to SimpleBlog | My Blog" in (tmp_path / "out" / "1.html").read_text()


def test_prev_and_next_links(site, tmp_path):
    Blog(str(site / "markdown" / "posts"), str(tmp_path / "posts")).build()
    second = (tmp_path / "posts" / "2.html").read_text()
    assert 'href="/posts/1.html"' in second  # previous post
    # post 2 is the last public one, so there is no "next" link
    assert "post-nav-next" not in second
    first = (tmp_path / "posts" / "1.html").read_text()
    assert 'href="/posts/2.html"' in first  # next post
    assert "post-nav-prev" not in first  # and no "previous" link


def test_draft_output_is_removed(site, tmp_path):
    out = tmp_path / "out"
    blog = Blog(str(site / "markdown" / "posts"), str(out))
    blog.build()
    (out / "3.html").write_text("stale")
    blog.build()
    assert not (out / "3.html").exists()


# --- index and feed ------------------------------------------------------


def test_index_lists_only_public_posts(site, tmp_path):
    blog = _posts(site)
    blog.build()
    blog.build_index()
    html = (site / "public" / "posts" / "index.html").read_text()
    assert "Second Sample Post" in html
    assert "Draft Post" not in html
    assert "Unlisted Sample Post" not in html


def test_index_title(site):
    _posts(site).build()
    path = _posts(site).build_index(title="All Posts")
    assert "All Posts" in open(path).read()


def test_feed_skips_drafts_and_keeps_unlisted(site, tmp_path):
    blog = Blog(
        str(site / "markdown" / "posts"),
        str(tmp_path / "posts"),
        name="My Blog",
        url="https://example.com",
    )
    blog.build()
    blog.build_rss()
    xml = (tmp_path / "posts" / "rss.xml").read_text()
    assert "Welcome to SimpleBlog" in xml
    assert "Unlisted Sample Post" in xml
    assert "Draft Post" not in xml
    assert "<title>My Blog</title>" in xml
    assert "https://example.com/posts/1.html" in xml


def test_pages_have_no_build_paths(site, tmp_path):
    blog = Blog(str(site / "markdown" / "posts"), str(tmp_path / "out"))
    blog.build()
    blog.build_index()
    for page in ["1.html", "2.html", "index.html"]:
        text = (tmp_path / "out" / page).read_text()
        assert str(tmp_path) not in text
        assert str(site) not in text


# --- filters -------------------------------------------------------------


def test_filter_folder_files_are_applied(tmp_path):
    (tmp_path / "md").mkdir()
    (tmp_path / "md" / "a.md").write_text(
        "---\ntitle: A\ndate: 2024-01-01\n---\n\nMARKME here\n"
    )
    (tmp_path / "fd").mkdir()
    (tmp_path / "fd" / "mark.lua").write_text(MARK_LUA)
    blog = Blog(str(tmp_path / "md"), str(tmp_path / "out"), filter_dir=str(tmp_path / "fd"))
    blog.build()
    html = (tmp_path / "out" / "1.html").read_text()
    assert "MARKED" in html
    assert "MARKME" not in html


def test_included_filter_is_applied(tmp_path):
    (tmp_path / "md").mkdir()
    (tmp_path / "md" / "a.md").write_text(
        "---\ntitle: A\ndate: 2024-01-01\n---\n\ntext\n"
    )
    blog = Blog(str(tmp_path / "md"), str(tmp_path / "out"), filters=["gallery"])
    blog.build()
    assert (tmp_path / "out" / "1.html").is_file()


def test_no_filters_leaves_text_alone(tmp_path):
    (tmp_path / "md").mkdir()
    (tmp_path / "md" / "a.md").write_text(
        "---\ntitle: A\ndate: 2024-01-01\n---\n\nMARKME here\n"
    )
    Blog(str(tmp_path / "md"), str(tmp_path / "out")).build()
    assert "MARKME" in (tmp_path / "out" / "1.html").read_text()


# --- mail comments -------------------------------------------------------


def test_mail_comment_link(tmp_path):
    (tmp_path / "md").mkdir()
    (tmp_path / "md" / "a.md").write_text(
        "---\ntitle: A\ndate: 2024-01-01\n"
        "maillist_title: Say hi\n"
        "google_group_link: https://groups.google.com/g/g\n"
        "---\n\ntext\n"
    )
    Blog(str(tmp_path / "md"), str(tmp_path / "out"), google_group="g").build()
    html = (tmp_path / "out" / "1.html").read_text()
    assert "mailto:g@googlegroups.com" in html
    assert "mailto://" not in html
    assert "Say%20hi" in html


# --- own template --------------------------------------------------------


def test_own_template_is_used(tmp_path):
    (tmp_path / "md").mkdir()
    (tmp_path / "md" / "a.md").write_text("---\ntitle: A\ndate: 2024-01-01\n---\n\nx\n")
    (tmp_path / "tpl").mkdir()
    (tmp_path / "tpl" / "post.html").write_text("CUSTOM {{ heading }}")
    blog = Blog(
        str(tmp_path / "md"),
        str(tmp_path / "out"),
        template=Jinja2Template("post.html", dir=str(tmp_path / "tpl")),
    )
    blog.build()
    assert "CUSTOM A" in (tmp_path / "out" / "1.html").read_text()
