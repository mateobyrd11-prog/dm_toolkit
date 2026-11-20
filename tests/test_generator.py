from unittest.mock import Mock, call

import pytest

import toolkit

from test_encounter_data import TERRAINS


@pytest.fixture
def source_tables(tmp_path, monkeypatch):
    """Give integration tests small, independent encounter and loot tables."""
    monkeypatch.chdir(tmp_path)
    directory = tmp_path / "encounters/test/arctic"
    directory.mkdir(parents=True)
    for rank in range(1, 5):
        (directory / f"rank_{rank}.txt").write_text(f"01-100 Narrative from tier {rank}\n")
    return directory


@pytest.mark.parametrize("level, rank", [
    (1, 1), (4, 1), (5, 2), (10, 2), (11, 3), (16, 3), (17, 4), (20, 4),
])
def test_generator_selects_rank_at_level_boundaries(source_tables, monkeypatch, level, rank):
    monkeypatch.setattr(toolkit, "die", lambda start, stop: 100)
    assert toolkit.generator("test", "arctic", level) == f"Narrative from tier {rank}"


@pytest.mark.parametrize("difficulty, bounds", [
    ("e", (1, 50)), ("m", (25, 75)), ("h", (50, 100)),
])
def test_generator_applies_difficulty_roll(source_tables, monkeypatch, difficulty, bounds):
    roll = Mock(return_value=bounds[0])
    monkeypatch.setattr(toolkit, "randrange", roll)
    assert toolkit.generator("test", "arctic", 7, difficulty) == "Narrative from tier 2"
    roll.assert_called_once_with(*bounds)


def test_generator_caps_high_levels_and_uses_hard_difficulty(source_tables, monkeypatch):
    roll = Mock(return_value=75)
    monkeypatch.setattr(toolkit, "randrange", roll)
    assert toolkit.generator("test", "arctic", 30) == "Narrative from tier 4"
    roll.assert_called_once_with(50, 100)


def test_generator_combines_creature_xp_and_returns_loot(source_tables, monkeypatch):
    (source_tables / "rank_2.txt").write_text("01-100 2 `goblin with 1 `ogre\n")
    goblin = f"{toolkit.encounter_site}?vo=goblin"
    ogre = f"{toolkit.encounter_site}?vo=ogre"
    browser = Mock()
    xp = Mock(side_effect=lambda url: {goblin: 50, ogre: 450}[url])
    cr = Mock(side_effect=lambda url: {goblin: 0.25, ogre: 2}[url])
    loot = Mock(return_value="20 GP")
    monkeypatch.setattr(toolkit, "open_link", browser)
    monkeypatch.setattr(toolkit, "get_xp", xp)
    monkeypatch.setattr(toolkit, "get_cr", cr)
    monkeypatch.setattr(toolkit, "loot", loot)

    assert toolkit.generator("test", "arctic", 7) == ("2 `goblin with 1 `ogre", "20 GP")
    assert browser.call_args_list == [call(goblin), call(ogre)]
    assert xp.call_args_list == [call(goblin), call(ogre)]
    assert cr.call_args_list == [call(goblin), call(ogre)]
    # 2 * 50 + 450 = 550 XP. Only the ogre counts toward the multiplier.
    loot.assert_called_once_with(2)


@pytest.mark.parametrize("terrain", TERRAINS)
@pytest.mark.parametrize("level", [1, 5, 11, 17])
def test_generator_reads_each_real_terrain_and_tier(project_directory, monkeypatch, terrain, level):
    monkeypatch.setattr(toolkit, "die", lambda start, stop: 1)
    # Exercise file selection and evaluation without the separate XP/stat-block path.
    monkeypatch.setattr(toolkit, "find_creature", lambda encounter: [])
    assert toolkit.generator("xanny", terrain, level).strip()


@pytest.mark.parametrize("level, expected", [
    (0, "6 PP"), (1, "6 PP"), (4, "6 PP"),
    (5, "120 GP and 18 PP"), (10, "120 GP and 18 PP"),
    (11, "1200 GP and 120 PP"), (16, "1200 GP and 120 PP"),
    (17, "6000 GP and 1200 PP"), (20, "6000 GP and 1200 PP"),
])
def test_loot_selects_tiers_and_evaluates_coin_amounts(project_directory, monkeypatch, level, expected):
    monkeypatch.setattr(toolkit, "die", lambda start, stop: stop)
    assert toolkit.loot(level) == expected


def test_loot_caps_high_levels_and_uses_upper_percentiles(project_directory, monkeypatch):
    monkeypatch.setattr(toolkit, "die", lambda start, stop: stop)
    roll = Mock(return_value=99)
    monkeypatch.setattr(toolkit, "randrange", roll)
    assert toolkit.loot(30) == "6000 GP and 1200 PP"
    roll.assert_called_once_with(50, 100)
