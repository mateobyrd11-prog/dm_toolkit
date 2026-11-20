"""Check every supplied table using the same parsing helpers as the application."""
from pathlib import Path
import random
import re

import pytest

import toolkit


ROOT = Path(__file__).resolve().parents[1]
TERRAINS = (
    "arctic", "coastal", "desert", "forest", "grassland", "hill",
    "mountain", "swamp", "underdark", "underwater", "urban",
)
ENCOUNTER_PATHS = [
    Path("encounters/xanny") / terrain / f"rank_{rank}.txt"
    for terrain in TERRAINS for rank in range(1, 5)
]
LOOT_PATHS = [Path("loot") / f"table_{rank}.txt" for rank in range(1, 5)]


@pytest.mark.parametrize("relative_path", ENCOUNTER_PATHS + LOOT_PATHS, ids=str)
def test_table_has_ordered_complete_percentile_coverage(relative_path):
    rows = (ROOT / relative_path).read_text().splitlines()
    previous_end = 0
    for row in rows:
        match = re.fullmatch(r"(\d{2,3})-(\d{2,3}) (.+)", row)
        assert match, f"Malformed row: {row!r}"
        start, end = map(int, match.group(1, 2))
        assert start == previous_end + 1, f"Gap or overlap: {row!r}"
        assert start <= end <= 100
        previous_end = end
    assert previous_end == 100

    for percentile in range(1, 101):
        matches = [row for row in rows if toolkit.in_range(percentile, row)]
        assert len(matches) == 1, f"Roll {percentile}: {matches!r}"
        assert toolkit.strip_range(matches[0]) == matches[0].split(" ", 1)[1]


@pytest.mark.parametrize("relative_path", ENCOUNTER_PATHS, ids=str)
def test_all_encounter_rows_evaluate_and_preserve_creature_links(relative_path, monkeypatch):
    rng = random.Random(0)
    monkeypatch.setattr(toolkit, "die", rng.randint)
    for row in (ROOT / relative_path).read_text().splitlines():
        description = toolkit.strip_range(row)
        encounter = toolkit.eval_encounter(description)
        assert encounter.strip(), row
        assert not re.search(r"\d+d\d+|\d+\+\d+", encounter), row
        slugs = re.findall(r"`([a-z]+(?:-[a-z]+)*)", description)
        assert len(slugs) == description.count("`"), row
        assert toolkit.find_creature(encounter) == [
            f"{toolkit.encounter_site}?vo={slug}" for slug in slugs
        ]


@pytest.mark.parametrize("terrain", ["swamp", "underwater"])
def test_combined_level_tables_are_available_in_both_ranks(terrain):
    directory = ROOT / "encounters/xanny" / terrain
    assert (directory / "rank_3.txt").read_text() == (directory / "rank_4.txt").read_text()
