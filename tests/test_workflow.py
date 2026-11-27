"""Tests for GitHub Actions workflows."""

from pathlib import Path


def test_hacs_validation_uses_an_immutable_ref():
    workflow = (Path(__file__).parents[1] / ".github/workflows/validate.yml").read_text()
    hacs_step = workflow.split("- name: HACS validation", maxsplit=1)[1]

    assert "REPOSITORY_REF: ${{ github.event.pull_request.head.sha || github.sha }}" in hacs_step
