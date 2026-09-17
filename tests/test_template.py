"""The Template class and its two kinds."""

import pytest

from essayist import Jinja2Template, PandocTemplate, Template
from essayist.core import templates_folder


def test_base_template_has_no_render():
    with pytest.raises(NotImplementedError):
        Template().render(title="x")


def test_jinja2_template_uses_a_file_that_comes_with_essayist():
    html = Jinja2Template("post.html").render(
        title="T", heading="H", paragraphs="<p>body</p>"
    )
    assert "<title> T </title>" in html
    assert "H" in html
    assert "<p>body</p>" in html


def test_jinja2_template_uses_own_folder(tmp_path):
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "mine.html").write_text("MINE {{ heading }}")
    assert "MINE Hi" == Jinja2Template("mine.html", dir=str(tmp_path / "t")).render(
        heading="Hi"
    )


def test_jinja2_template_default_dir_is_inside_essayist():
    assert Jinja2Template("post.html").dir == templates_folder()


def test_pandoc_template_renders_body_and_variables(tmp_path):
    tpl = tmp_path / "t.html"
    tpl.write_text("<h1>$title$</h1>$body$")
    out = PandocTemplate(path=str(tpl)).render(body="Hi there", title="My Title")
    assert "<h1>My Title</h1>" in out
    assert "Hi there" in out


def test_pandoc_template_without_file_uses_pandoc_default():
    out = PandocTemplate().render(body="Hi there")
    assert "Hi there" in out


def test_pandoc_template_passes_extra_pandoc_flags(tmp_path):
    out = PandocTemplate(pandoc_args=["--mathml"]).render(body="$x$")
    assert "math" in out


def test_pandoc_template_skips_empty_variables(tmp_path):
    tpl = tmp_path / "t.html"
    tpl.write_text("$body$")
    out = PandocTemplate(path=str(tpl)).render(body="Hi", title=None)
    assert "Hi" in out


def test_both_kinds_answer_the_same_call():
    for template in (Jinja2Template("post.html"), PandocTemplate()):
        assert isinstance(template.render(title="x"), str)


# --- CWD-relative path resolution ----------------------------------------


def test_jinja2_template_resolves_relative_to_cwd(tmp_path, monkeypatch):
    """Relative path like './template' resolves against CWD."""
    (tmp_path / "mytpl").mkdir()
    (tmp_path / "mytpl" / "x.html").write_text("CWD {{ v }}")
    monkeypatch.chdir(tmp_path)
    t = Jinja2Template("mytpl/x.html")
    assert t.render(v="ok") == "CWD ok"
    assert t.dir == str(tmp_path / "mytpl")


def test_jinja2_template_resolves_dir_relative_to_cwd(tmp_path, monkeypatch):
    """Relative directory path resolves against CWD."""
    (tmp_path / "tpls").mkdir()
    (tmp_path / "tpls" / "post.html").write_text("DIR {{ v }}")
    monkeypatch.chdir(tmp_path)
    t = Jinja2Template("tpls")
    assert t.render(v="ok") == "DIR ok"
    assert t.name == "post.html"


def test_jinja2_template_absolute_path_works(tmp_path):
    """Absolute paths work without CWD dependency."""
    (tmp_path / "abs.html").write_text("ABS {{ v }}")
    t = Jinja2Template(str(tmp_path / "abs.html"))
    assert t.render(v="x") == "ABS x"
    assert t.dir == str(tmp_path)


def test_jinja2_template_bare_name_uses_dir(tmp_path):
    """Bare name + dir= looks in the given directory."""
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "a.html").write_text("DIR {{ v }}")
    t = Jinja2Template("a.html", dir=str(tmp_path / "d"))
    assert t.render(v="ok") == "DIR ok"


def test_jinja2_template_bare_name_uses_bundled():
    """Bare name without dir= falls back to bundled templates."""
    t = Jinja2Template("post.html")
    assert t.dir == templates_folder()
    html = t.render(title="T", heading="H", paragraphs="<p>b</p>")
    assert "T" in html
    assert "<p>b</p>" in html
