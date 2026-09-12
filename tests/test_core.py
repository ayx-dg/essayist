"""Tests for the pandoc helper (requires the pandoc CLI)."""

import pytest

from essayist import pandoc


def test_pandoc_basic():
    result = pandoc("---\ntitle: Test\n---\n\nHello world")
    assert isinstance(result, str)
    assert "Hello world" in result


def test_pandoc_math():
    result = pandoc("---\ntitle: Math\n---\n\n$E = mc^2$", ["--mathml"])
    assert "math" in result


def test_pandoc_toc():
    result = pandoc("---\ntitle: TOC\n---\n\n# Heading\n\nContent", ["--toc"])
    assert "toc" in result.lower()
