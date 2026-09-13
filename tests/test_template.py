"""The Template class and its two kinds."""

import pytest

from essayist import Jinja2Template, PandocTemplate, Template
from essayist.core import bundled_path


def test_base_template_has_no_render():
    with pytest.raises(NotImplementedError):
        Template().render(title="x")


def test_jinja2_template_uses_a_bundled_file():
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


def test_jinja2_template_default_dir_is_the_bundled_one():
    assert Jinja2Template("post.html").dir == bundled_path("templates")


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
    out = PandocTemplate(panargs=["--mathml"]).render(body="$x$")
    assert "math" in out


def test_pandoc_template_skips_empty_variables(tmp_path):
    tpl = tmp_path / "t.html"
    tpl.write_text("$body$")
    out = PandocTemplate(path=str(tpl)).render(body="Hi", title=None)
    assert "Hi" in out


def test_both_kinds_answer_the_same_call():
    for template in (Jinja2Template("post.html"), PandocTemplate()):
        assert isinstance(template.render(title="x"), str)
