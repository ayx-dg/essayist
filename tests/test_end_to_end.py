"""End-to-end tests: drive the CLI over the sample site and inspect the output.

Everything the build is expected to guarantee (which files exist, which posts
are visible where, what ends up inside the generated HTML) is asserted here by
running the real ``essayist build`` command, so CI only needs ``pytest``.
"""

from essayist import cli


def _toml_path(path) -> str:
    """Render a path as a TOML basic string (backslashes must be escaped)."""
    return str(path).replace("\\", "/")


def _build(site, tmp_path) -> "tuple":
    """Run ``essayist build`` against the sample site; return (public, root)."""
    cfg_file = tmp_path / "essayist.toml"
    cfg_file.write_text(
        "\n".join(
            [
                f'markdown_dir = "{_toml_path(site / "markdown" / "posts")}"',
                f'post_dir = "{_toml_path(tmp_path / "public" / "posts")}"',
                'blogname = "E2E Blog"',
                'site_url = "https://example.com"',
                'panargs = ["--mathml", "--toc"]',
                f'home_md = "{_toml_path(site / "markdown" / "index.md")}"',
                f'home_output = "{_toml_path(tmp_path / "public" / "index.html")}"',
                f'data_path = "{_toml_path(tmp_path / "data.json")}"',
            ]
        )
    )
    assert cli.main(["build", "--config", str(cfg_file)]) == 0
    return tmp_path / "public", tmp_path


def test_cli_build_produces_expected_files(site, tmp_path):
    public, _ = _build(site, tmp_path)
    assert (public / "posts" / "1.html").is_file()
    assert (public / "posts" / "2.html").is_file()
    assert (public / "posts" / "index.html").is_file()
    assert (public / "posts" / "rss.xml").is_file()
    assert (public / "index.html").is_file()


def test_cli_build_renders_unlisted_but_not_drafts(site, tmp_path):
    public, _ = _build(site, tmp_path)
    # "draft" is never rendered; "unlisted" is rendered but kept off the index
    assert not (public / "posts" / "3.html").exists()
    assert (public / "posts" / "4.html").is_file()


def test_cli_build_unlisted_is_feed_only(site, tmp_path):
    public, _ = _build(site, tmp_path)
    index_html = (public / "posts" / "index.html").read_text()
    rss_xml = (public / "posts" / "rss.xml").read_text()
    assert "Unlisted Sample Post" not in index_html
    assert "Unlisted Sample Post" in rss_xml


def test_cli_build_rss_titled_after_blogname(site, tmp_path):
    public, _ = _build(site, tmp_path)
    rss_xml = (public / "posts" / "rss.xml").read_text()
    assert "<title>E2E Blog</title>" in rss_xml


def test_cli_build_pages_contain_no_build_paths(site, tmp_path):
    public, root = _build(site, tmp_path)
    for page in [
        public / "posts" / "index.html",
        public / "posts" / "1.html",
        public / "index.html",
    ]:
        text = page.read_text()
        assert str(root) not in text
        assert str(site) not in text


def test_cli_build_pages_reference_no_missing_assets(site, tmp_path):
    public, _ = _build(site, tmp_path)
    for page in [public / "posts" / "index.html", public / "index.html"]:
        assert "script.js" not in page.read_text()
