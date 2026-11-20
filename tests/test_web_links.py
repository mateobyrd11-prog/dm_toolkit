"""Regression checks for verified AideDD aliases, variants, and missing pages."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import requests

import toolkit


@pytest.mark.parametrize("slug, target", [
    ("deep-gnome", "deep-gnome-svirfneblin"),
    ("will-o-wisp", "will-o--wisp"),
    ("incubus", "succubus"),
    ("kuo-toa-monitor", "kuo-toa-whip#kuo-toa-monitor"),
    ("young-white-dragon", "young-white-dragon"),
])
def test_creature_link_aliases_keep_encounter_names(slug, target):
    assert toolkit.find_creature(f"1 (`{slug})") == [
        f"https://www.aidedd.org/dnd/monstres.php?vo={target}"
    ]


@pytest.mark.parametrize("getter, expected", [(toolkit.get_cr, 3), (toolkit.get_xp, 700)])
def test_monitor_uses_variant_challenge_instead_of_whip(getter, expected, monkeypatch):
    # The primary block and the monitor's prose both contain CR and XP.
    html = """
        <h1>Kuo-toa Whip</h1>
        <div><strong>Challenge</strong> 1 (200 XP)</div>
        <h2>VARIANTE: KUO-TOA MONITOR</h2>
        <p>A kuo-toa monitor has a challenge rating of 3 (700 XP).
        It has the same statistics as a kuo-toa whip except for its variant traits.</p>
    """
    get = Mock(return_value=SimpleNamespace(status_code=200, text=html))
    monkeypatch.setattr(toolkit.requests, "get", get)
    assert getter(toolkit.creature_url("kuo-toa-monitor")) == expected
    get.assert_called_once_with(
        "https://www.aidedd.org/dnd/monstres.php?vo=kuo-toa-whip", timeout=20
    )


@pytest.mark.parametrize("getter", [toolkit.get_cr, toolkit.get_xp])
def test_missing_monitor_section_does_not_use_base_stats(getter, monkeypatch):
    response = SimpleNamespace(status_code=200, text="<p>Challenge 1 (200 XP)</p>")
    monkeypatch.setattr(toolkit.requests, "get", Mock(return_value=response))
    with pytest.raises(toolkit.StatBlockLookupError, match="No CR/XP"):
        getter(toolkit.creature_url("kuo-toa-monitor"))


@pytest.mark.parametrize("getter", [toolkit.get_cr, toolkit.get_xp])
@pytest.mark.parametrize("slug", ["mind-flayer-arcanist", "quaggoth-thonot"])
def test_unavailable_2014_variants_fail_without_fetching_2024_stats(getter, slug):
    # conftest fails the test if this attempts an HTTP request.
    with pytest.raises(toolkit.StatBlockLookupError, match="no pre-2024 stat block"):
        getter(toolkit.creature_url(slug))


@pytest.mark.parametrize("getter", [toolkit.get_cr, toolkit.get_xp])
@pytest.mark.parametrize("status, html, message", [
    (200, "<html><title>AideDD</title><body></body></html>", "No CR/XP"),
    (404, "Not found", "HTTP 404"),
    (503, "Service unavailable", "HTTP 503"),
])
def test_missing_stat_blocks_raise_clear_errors(getter, status, html, message, monkeypatch):
    monkeypatch.setattr(toolkit.requests, "get", Mock(
        return_value=SimpleNamespace(status_code=status, text=html)
    ))
    with pytest.raises(toolkit.StatBlockLookupError, match=message):
        getter("https://example.test/missing")


@pytest.mark.parametrize("getter", [toolkit.get_cr, toolkit.get_xp])
def test_request_timeout_has_context(getter, monkeypatch):
    monkeypatch.setattr(toolkit.requests, "get", Mock(side_effect=requests.Timeout("Timed out")))
    with pytest.raises(toolkit.StatBlockLookupError, match="Could not fetch stat block"):
        getter("https://example.test/monster")


def test_xp_accepts_grouping_separators_and_split_html(monkeypatch):
    response = SimpleNamespace(status_code=200, text=(
        "<div><strong>Challenge</strong> <span>20</span> (25,000 XP)</div>"
    ))
    monkeypatch.setattr(toolkit.requests, "get", Mock(return_value=response))
    assert toolkit.get_cr("https://example.test/monster") == 20
    assert toolkit.get_xp("https://example.test/monster") == 25000


def test_generator_does_not_open_a_known_missing_stat_block(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "encounters/test/underdark"
    directory.mkdir(parents=True)
    (directory / "rank_1.txt").write_text("01-100 1 `mind-flayer-arcanist\n")
    with pytest.raises(toolkit.StatBlockLookupError, match="no pre-2024 stat block"):
        toolkit.generator("test", "underdark", 1)
