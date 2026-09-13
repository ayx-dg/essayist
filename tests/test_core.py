"""Reading, writing and Pandoc helpers."""

import os

from essayist.core import (
    filters_folder,
    inside_essayist,
    pandoc,
    read,
    templates_folder,
    top_block,
    write,
)


def test_read_and_write_round_trip(tmp_path):
    write(str(tmp_path / "a" / "b.txt"), "hello")
    assert read(str(tmp_path / "a" / "b.txt")) == "hello"


def test_pandoc_renders_markdown():
    assert "<p>" in pandoc("Hello world")


def test_pandoc_math():
    assert "math" in pandoc("$E = mc^2$", ["--mathml"])


def test_pandoc_toc():
    assert "toc" in pandoc("# Head\n\ntext", ["--toc"]).lower()


def test_pandoc_uses_a_given_template(tmp_path):
    tpl = tmp_path / "t.html"
    tpl.write_text("<main>$body$</main>")
    out = pandoc("Hi", [f"--template={tpl}"])
    assert "<main>" in out


def test_top_block_reads_the_top_block():
    data = top_block("---\ntitle: One\ndate: 2024-01-01\n---\n\nbody\n")
    assert data["title"] == "One"


def test_top_block_without_block_is_none():
    assert top_block("just text\n") is None


def test_top_block_makes_title_a_string():
    data = top_block("---\ntitle: 42\n---\n")
    assert data["title"] == "42"


def test_templates_folder_has_the_jinja2_files():
    path = templates_folder()
    assert os.path.isdir(path)
    assert os.path.isfile(os.path.join(path, "post.html"))


def test_filters_folder_has_the_filter_files():
    assert os.path.isdir(filters_folder())


def test_inside_essayist_finds_a_file():
    assert os.path.isfile(inside_essayist("style-note.css"))
