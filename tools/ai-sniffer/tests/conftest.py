"""Shared fixtures. The eval scripts aren't a package, so they're loaded by path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).parents[1] / "eval"


@pytest.fixture
def eval_script():
    def load(name: str):
        spec = importlib.util.spec_from_file_location(
            f"ai_sniffer_eval_{name.replace('/', '_')}", EVAL / f"{name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        # Dataclasses look their module up in sys.modules while the class is built.
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    return load


@pytest.fixture
def workspace(tmp_path):
    """A tiny eval directory: two drafts and the label file that points into them."""
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "heldout-a.md").write_text(
        "---\ntitle: A\n---\n\nIt didn't degrade. It collapsed.\n\nNote that this matters.\n"
    )
    (drafts / "dev-b.html").write_text(
        "<p>Same idea, different engine.</p>\n<p>Sit with that.</p>\n"
    )
    return tmp_path
