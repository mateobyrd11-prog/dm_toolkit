"""Creature quantities must not come from unrelated narrative numbers."""
from unittest.mock import Mock

import pytest

import toolkit


@pytest.mark.parametrize("encounter, expected", [
    ("2 `ogre with 1 `troll", [2, 1]),
    ("100-100 2 `ogre", [2]),
    ("50 feet away, 2 `ogre guard a door", [2]),
    ("At mile 12, 3 hunters (`tribal-warrior) wait", [3]),
    ("8 hunters (`tribal-warrior)", [8]),
    ("A herd of 40 caribou (`deer) moving through the snow", [40]),
    ("A group of seven people (`commoner) wearing masks", [7]),
    ("A half-orc `druid tending to an injured `polar-bear", [1, 1]),
    ("A young woodcutter (`scout) racing to rescue a friend", [1]),
    ("A force of 100 dwarves (`veteran) charging 100 gp or 200 gp", [100]),
    ("4 `zombie aboard a ship. Searching yields 12 days of rations.", [4]),
    ("6 `ghast crawling over 3 wrecked ships", [6]),
    ("1 `archmage on a `riding-horse, blasting 4 `guard with spells", [1, 1, 4]),
    ("5 `veteran on `riding-horse", [5, 5]),
    ("1 `bandit-captain with 10 `bandit, all on `riding-horse", [1, 10, 11]),
    ("6 `knight on `warhorse (one knight is a `doppelganger)", [5, 6, 1]),
    ("A sparkling stream, 20 feet wide", []),
])
def test_creature_counts_associate_quantities_with_markers(encounter, expected):
    assert toolkit.creature_counts(encounter) == expected


@pytest.mark.parametrize("encounter", [
    "1 `ogre or 3 `goblin",
    "1 `couatl (day) or 1 `banshee (night)",
    "2 `banshee (night only)",
    "Two farmers (50% chance for one farmer to be a retired `assassin)",
    "At 50 feet, a herd of `deer grazes",
    "12 nomads (`tribal-warrior) on `riding-horse following a herd of antelope (`deer)",
    "50 feet away from `ogre",
    "An unknown number of `goblin",
])
def test_ambiguous_counts_fail_instead_of_using_narrative_numbers(encounter):
    with pytest.raises(toolkit.CreatureCountError):
        toolkit.creature_counts(encounter)


def test_generator_ignores_narrative_number_before_creature_counts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "encounters/test/arctic"
    directory.mkdir(parents=True)
    encounter = "50 feet away, 2 `ogre guard a cache of 100 gp"
    (directory / "rank_1.txt").write_text(f"01-100 {encounter}\n")
    monkeypatch.setattr(toolkit, "get_xp", Mock(return_value=450))
    monkeypatch.setattr(toolkit, "get_cr", Mock(return_value=2))
    monkeypatch.setattr(toolkit, "open_link", Mock())
    loot = Mock(return_value="12 GP")
    monkeypatch.setattr(toolkit, "loot", loot)
    assert toolkit.generator("test", "arctic", 1) == (encounter, "12 GP")
    # 2 * 450 XP, multiplied by 1.5 for two significant monsters => 1350, CR 4.
    loot.assert_called_once_with(4)


def test_unresolved_encounter_fails_before_fetching_stats_or_opening_browser(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "encounters/test/arctic"
    directory.mkdir(parents=True)
    (directory / "rank_1.txt").write_text("01-100 1 `ogre or 3 `goblin\n")
    # The autouse fixture rejects any accidental HTTP/browser calls.
    with pytest.raises(toolkit.CreatureCountError, match="Choose one alternative"):
        toolkit.generator("test", "arctic", 1)
