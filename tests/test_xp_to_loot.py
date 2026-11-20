"""Verify stat-block XP -> encounter CR -> real loot-table results."""
from pathlib import Path
from shutil import copytree
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import toolkit


# XP by CR 1-30, from the 2014 rules / SRD 5.1 Experience Points table.
CR_XP = [
    200, 450, 700, 1100, 1800, 2300, 2900, 3900, 5000, 5900,
    7200, 8400, 10000, 11500, 13000, 15000, 18000, 20000, 22000, 25000,
    33000, 41000, 50000, 62000, 75000, 90000, 105000, 120000, 135000, 155000,
]


@pytest.mark.parametrize("cr, xp", list(enumerate(CR_XP, start=1)))
def test_single_monster_xp_converts_at_every_cr_threshold(cr, xp):
    assert toolkit.xp_to_cr(xp, 1) == cr
    if cr > 1:
        assert toolkit.xp_to_cr(xp - 1, 1) == cr - 1


@pytest.mark.parametrize("count, multiplier", [
    (1, 1), (2, 1.5), (3, 2), (6, 2), (7, 2.5), (10, 2.5),
    (11, 3), (14, 3), (15, 4), (16, 4), (30, 4),
])
def test_group_multiplier_boundaries_convert_to_expected_cr(count, multiplier):
    # 1000 raw XP makes each multiplier land in a different known CR band.
    expected = {1: 3, 1.5: 4, 2: 5, 2.5: 6, 3: 7, 4: 8}[multiplier]
    assert toolkit.xp_to_cr(1000, count) == expected


STAT_BLOCKS = {
    "ogre": (2, 450),
    "troll": (5, 1800),
    "storm-giant": (13, 10000),
    "adult-gold-dragon": (17, 18000),
    "ancient-gold-dragon": (24, 62000),
}


@pytest.mark.parametrize("cr", range(1, 31))
def test_converted_cr_selects_matching_loot_tier(cr, project_directory, monkeypatch):
    monkeypatch.setattr(toolkit, "die", lambda start, stop: stop)
    monkeypatch.setattr(toolkit, "randrange", lambda start, stop: stop - 1)
    if cr <= 4:
        expected = "6 PP"
    elif cr <= 10:
        expected = "120 GP and 18 PP"
    elif cr <= 16:
        expected = "1200 GP and 120 PP"
    else:
        expected = "6000 GP and 1200 PP"
    assert toolkit.loot(cr) == expected


@pytest.mark.parametrize("encounter, level, rank, converted_cr, expected_coins", [
    ("1 `ogre", 1, 1, 2, "6 PP"),
    ("4 `ogre", 1, 1, 7, "120 GP and 18 PP"),
    ("4 `troll", 1, 1, 15, "1200 GP and 120 PP"),
    ("1 `storm-giant", 17, 4, 13, "1200 GP and 120 PP"),
    ("1 `adult-gold-dragon", 17, 4, 17, "6000 GP and 1200 PP"),
    ("1 `ancient-gold-dragon", 20, 4, 24, "6000 GP and 1200 PP"),
    ("2 `ogre with 1 `troll", 1, 1, 9, "120 GP and 18 PP"),
    # At party level 7, CR 2 ogres do not meet the level/2 cutoff.
    # Raw 3600 XP remains CR 7 instead of being inflated to CR 12.
    ("8 `ogre", 7, 2, 7, "120 GP and 18 PP"),
])
def test_stat_block_xp_produces_loot_for_converted_cr(
    tmp_path, monkeypatch, encounter, level, rank, converted_cr, expected_coins
):
    root = Path(__file__).resolve().parents[1]
    copytree(root / "loot", tmp_path / "loot")
    directory = tmp_path / "encounters/test/arctic"
    directory.mkdir(parents=True)
    (directory / f"rank_{rank}.txt").write_text(f"01-100 {encounter}\n")
    monkeypatch.chdir(tmp_path)

    def response(url, timeout):
        assert timeout == 20
        slug = url.split("?vo=", 1)[1]
        cr, xp = STAT_BLOCKS[slug]
        return SimpleNamespace(status_code=200, text=(
            f"<h1>{slug}</h1><p><strong>Challenge</strong> {cr} ({xp:,} XP)</p>"
        ))

    monkeypatch.setattr(toolkit.requests, "get", response)
    monkeypatch.setattr(toolkit, "open_link", Mock())
    monkeypatch.setattr(toolkit, "die", lambda start, stop: stop)
    monkeypatch.setattr(toolkit, "randrange", lambda start, stop: stop - 1)
    # Keep actual loot generation, spying only on the CR passed to it.
    loot = Mock(wraps=toolkit.loot)
    monkeypatch.setattr(toolkit, "loot", loot)

    assert toolkit.generator("test", "arctic", level) == (encounter, expected_coins)
    loot.assert_called_once_with(converted_cr)
