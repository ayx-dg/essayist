"""Shared pytest fixtures."""

import os
import shutil

import pytest

SAMPLE = os.path.join(os.path.dirname(__file__), "sample")


@pytest.fixture
def site(tmp_path):
    """A copy of the sample site (markdown fixtures) inside tmp_path."""
    root = tmp_path / "site"
    shutil.copytree(os.path.join(SAMPLE, "markdown"), root / "markdown")
    return root
