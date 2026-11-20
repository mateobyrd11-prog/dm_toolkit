from pathlib import Path

import pytest

import toolkit


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def prevent_external_calls(monkeypatch):
    """Tests must explicitly mock browser launches and HTTP requests."""
    def unexpected_call(*args, **kwargs):
        pytest.fail("Unexpected browser or network call")

    monkeypatch.setattr(toolkit, "open_link", unexpected_call)
    monkeypatch.setattr(toolkit.requests, "get", unexpected_call)


@pytest.fixture
def project_directory(monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    return PROJECT_ROOT
