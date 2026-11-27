"""Tests for GitHub Actions workflows."""

from pathlib import Path


def test_hacs_validation_uses_an_immutable_ref():
    workflow = (Path(__file__).parents[1] / ".github/workflows/validate.yml").read_text()
    hacs_step = workflow.split("- name: HACS validation", maxsplit=1)[1]

    assert "REPOSITORY_REF: ${{ github.event.pull_request.head.sha || github.sha }}" in hacs_step


def test_release_please_can_use_a_personal_access_token():
    workflow = (
        Path(__file__).parents[1] / ".github/workflows/release-please.yml"
    ).read_text()
    release_step = workflow.split("- name: Run Release Please", maxsplit=1)[1]

    assert "token: ${{ secrets.RELEASE_PLEASE_TOKEN || secrets.GITHUB_TOKEN }}" in release_step
    assert "package-name:" not in release_step
