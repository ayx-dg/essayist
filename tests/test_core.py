"""Reading, writing and Pandoc helpers."""

import os

from essayist.core import bundled_path, front_matter, pandoc, read, write


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


def test_front_matter_reads_the_top_block():
    data = front_matter("---\ntitle: One\ndate: 2024-01-01\n---\n\nbody\n")
    assert data["title"] == "One"


def test_front_matter_without_block_is_none():
    assert front_matter("just text\n") is None


def test_front_matter_makes_title_a_string():
    data = front_matter("---\ntitle: 42\n---\n")
    assert data["title"] == "42"


def test_bundled_path_finds_templates():
    path = bundled_path("templates")
    assert os.path.isdir(path)
    assert os.path.isfile(os.path.join(path, "post.html"))
