from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

import toolkit


@pytest.mark.parametrize("percentile, expected", [(1, False), (99, False), (100, True)])
def test_roll_100_is_not_parsed_as_zero_to_100(percentile, expected):
    assert toolkit.in_range(percentile, "100-100 1 `frost-giant") is expected


def test_strip_range_preserves_creature_count_and_description_numbers():
    assert toolkit.strip_range("100-100 1 `frost-giant") == "1 `frost-giant"
    assert toolkit.strip_range("01-05 A path 20-30 feet wide") == "A path 20-30 feet wide"


@pytest.mark.parametrize("value, expected", [(20, False), (21, True), (25, True), (26, False)])
def test_percentile_range_is_inclusive(value, expected):
    assert toolkit.in_range(value, "21-25 Snowy tracks") is expected


def test_roll_returns_total_and_individual_dice(monkeypatch):
    dice = Mock(side_effect=[1, 6, 3])
    monkeypatch.setattr(toolkit, "die", dice)
    assert toolkit.roll(3, 6) == (10, [1, 6, 3])
    assert dice.call_args_list == [call(1, 6)] * 3


def test_stats_produces_six_ability_scores(monkeypatch):
    dice = Mock(side_effect=[1, 2, 3, 4, 5, 6] * 2)
    monkeypatch.setattr(toolkit, "die", dice)
    assert toolkit.stats() == [9, 13, 17, 9, 13, 17]


def test_eval_encounter_rolls_different_dice_and_adds_modifiers(monkeypatch):
    monkeypatch.setattr(toolkit, "die", Mock(side_effect=[2, 5, 3]))
    result = toolkit.eval_encounter("2d6+3 `goblin with 1d4 `wolf")
    assert result.strip() == "10 `goblin with 3 `wolf"


def test_eval_encounter_keeps_narrative_without_dice():
    text = "Single-file tracks in the snow that stop abruptly"
    assert toolkit.eval_encounter(text) == text


def test_coin_arithmetic():
    assert toolkit.do_add("2+3 GP and 7 SP").strip() == "5 GP and 7 SP"
    assert toolkit.do_mult("5x100 GP and 2x10 PP").strip() == "500 GP and 20 PP"
    assert toolkit.do_div("1/4") == 0.25


@pytest.mark.parametrize("text, slugs", [
    ("1 `young-white-dragon with 2 `polar-bear", ["young-white-dragon", "polar-bear"]),
    ("1 `druid, 2 hunters (`tribal-warrior)", ["druid", "tribal-warrior"]),
    ("A dragon-shaped cloud", []),
])
def test_find_creature_uses_only_marked_stat_blocks(text, slugs):
    assert toolkit.find_creature(text) == [
        f"{toolkit.encounter_site}?vo={slug}" for slug in slugs
    ]


@pytest.mark.parametrize("challenge, xp", [("1/4", 50), ("1/2", 100), ("2", 450)])
def test_stat_block_challenge_and_xp_parsing(challenge, xp, monkeypatch):
    response = SimpleNamespace(status_code=200, text=f"<p>Challenge {challenge} ({xp} XP)</p>")
    get = Mock(return_value=response)
    monkeypatch.setattr(toolkit.requests, "get", get)
    expected_cr = {"1/4": 0.25, "1/2": 0.5, "2": 2}[challenge]
    assert toolkit.get_cr("https://example.test/monster") == expected_cr
    assert toolkit.get_xp("https://example.test/monster") == xp
    assert get.call_args_list == [call("https://example.test/monster")] * 2


def test_count_creatures_includes_challenges_at_half_the_party_level():
    assert toolkit.count_creatures([0.5, 1, 2, 3], 4) == [0, 0, 1, 1]


@pytest.mark.parametrize("xp, creatures, expected", [
    (0, 1, 1), (199, 1, 1), (200, 1, 1), (449, 1, 1), (450, 1, 2),
    (1000, 1, 3), (1000, 2, 4), (1000, 3, 5), (1000, 7, 6),
    (1000, 11, 7), (1000, 15, 8), (1000, 30, 8),
])
def test_xp_conversion_thresholds_and_group_multipliers(xp, creatures, expected):
    assert toolkit.xp_to_cr(xp, creatures) == expected
