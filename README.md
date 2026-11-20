# DM Toolkit

A Python toolkit for generating random encounters and coin loot for D&D 5e
(pre-2024), rolling dice, and generating ability scores.

## Setup

Create and activate a Conda environment:

```sh
conda create -n dm_toolkit python=3.13 pip
conda activate dm_toolkit
python -m pip install beautifulsoup4 numpy requests
```

If `dm_toolkit` already exists, activate it with `conda activate dm_toolkit`.
Run the examples below from the project root so the toolkit can find its
encounter and loot files.

## Generate an encounter

Start an interactive Python session:

```sh
python -i toolkit.py
```

At the Python `>>>` prompt, generate a hard arctic encounter for level 7:

```python
generator('xanny', 'arctic', 7, 'h')
```

Or run it directly from the shell:

```sh
python -c "from toolkit import generator; print(generator('xanny', 'arctic', 7, 'h'))"
```

The function accepts `generator(source, terrain, level, diff='')`:

- `source`: the encounter collection, currently `xanny` for Xanathar's Guide.
- `terrain`: one of the environments listed below.
- `level`: character level, normally 1–20. Levels above 20 use the highest
  tier and hard difficulty.
- `diff`: omit for the full percentile table, or use `'e'`, `'m'`, or `'h'`
  to favor lower, middle, or higher table results. These options select
  portions of a table; they do not guarantee a balanced encounter.

For encounters with marked creatures, the toolkit opens their stat blocks
on [AideDD](https://www.aidedd.org/), fetches challenge ratings and XP, and
returns `(encounter, loot)`. These lookups require an internet connection.
For encounters without marked creatures, it returns the encounter text.
This project is not affiliated with AideDD.

## Encounter data

The `xanny` collection contains **44 files and 1,608 entries** across 11 terrains:

`arctic`, `coastal`, `desert`, `forest`, `grassland`, `hill`, `mountain`,
`swamp`, `underdark`, `underwater`, and `urban`.

| File | Character levels used by the generator |
| --- | --- |
| `rank_1.txt` | 1–4 |
| `rank_2.txt` | 5–10 |
| `rank_3.txt` | 11–16 |
| `rank_4.txt` | 17–20 |

The tables were transcribed from the photos in `Random encounters/`,
including supplemental photos that filled every previously cropped entry.
No missing-source placeholders remain. Swamp and underwater each share one
levels 11–20 source table between ranks 3 and 4.

See [the encounter data notes](encounters/xanny/README.md) for the format,
source details, and the grassland level-band exception.

To add another collection, follow this layout:

```text
encounters/<source>/<terrain>/rank_<1-4>.txt
```

Each line starts with an inclusive percentile range. Use `100` for the
book's `00`, repeat the bounds for a single result, and prefix stat-block
names with a backtick:

```text
01-05 2 `saber-toothed-tiger
06-07 1d4 `half-ogre
```

Each table must cover rolls 1–100 without gaps or overlaps.

## Other helpers

Use these at the interactive Python prompt after loading `toolkit.py`:

```python
roll(2, 6)       # Returns (total, list_of_individual_rolls)
stats()         # Six ability scores, each generated as 2d6+6
loot(7)         # Coin loot for challenge rating 7
```

Loot tables live in `loot/table_1.txt` through `loot/table_4.txt`, using the
same tier boundaries as encounters. Challenge ratings below 1 use tier 1;
ratings above 20 use tier 4 with an upper-percentile roll.

The encounter-to-loot calculation sums each creature count multiplied by its
stat-block XP. It applies the group multiplier using creatures whose CR is
at least half the original party level, then converts the adjusted XP to the
highest CR threshold it reaches. The current conversion has a minimum of
CR 1 and a maximum of CR 30. That converted CR selects the loot tier;
the party's encounter-table rank does not select the loot tier.

For example, four trolls at party level 1 contribute 7,200 XP. The group
multiplier is 2, giving 14,400 adjusted XP, which converts to CR 15 and
uses `loot/table_3.txt`. Coin amounts still depend on the loot roll.

## Tests

Install the development dependency if needed, then run pytest in the
`dm_toolkit` Conda environment:

```sh
conda run -n dm_toolkit python -m pip install -r requirements-dev.txt
conda run -n dm_toolkit python -m pytest
```

Tests cover table completeness, dice evaluation, percentile boundaries,
creature links, stat-block parsing, XP calculations, loot, and generator
behavior. Browser launches and HTTP requests are mocked.

## Current limitations

Creature counts are associated with marked stat blocks. Labels such as
``8 hunters (`tribal-warrior)`` count as eight creatures;
numbers in distances, prices, and rations do not contribute to XP. Articles
such as "a" and "an" imply one individual, and mounts inherit rider counts.
The parenthesized knight/doppelganger substitution replaces one knight
rather than adding an extra creature.

Alternatives, day/night conditions, chance-dependent creatures, and
unquantified groups raise `CreatureCountError` before stat-block lookups.
Resolve the choice or supply an explicit quantity before calculating XP.
The parser recognizes the table's common prose patterns; custom descriptions
should use explicit quantities next to creature markers. Stat-block lookups
also depend on AideDD's availability and HTML format.

Creature links resolve AideDD's alternate slugs for deep gnomes,
will-o'-wisps, and incubi. Kuo-toa monitors link to the kuo-toa whip page,
which includes their variant stats, with the monitor's own CR and XP used
for calculations.

AideDD has no matching pre-2024 pages for mind flayer arcanists or quaggoth
thonots. Those encounters raise `StatBlockLookupError` with a message to
consult the 2014 Monster Manual. The toolkit does not substitute 2024 or
base-creature stats. Failed requests and missing CR/XP also raise this error.

## Planned features

- Ally mode
- Damage tracking
- Hoard loot
- Encounter objects
