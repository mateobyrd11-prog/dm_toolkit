# Xanathar's random encounters

Transcribed from the photographs of pages 92–112 in `Random encounters/`.
Each terrain has four files: `rank_1.txt` through `rank_4.txt`.

Terrains: `arctic`, `coastal`, `desert`, `forest`, `grassland`, `hill`,
`mountain`, `swamp`, `underdark`, `underwater`, and `urban`.

| Rank | Usual character levels |
| --- | --- |
| 1 | 1–4 |
| 2 | 5–10 |
| 3 | 11–16 |
| 4 | 17–20 |

The book labels the first two grassland tables **1–5** and **6–10**.
They are stored as ranks 1 and 2, respectively. The current generator uses
the usual level bands for every terrain, so it selects grassland rank 2
at character level 5.

The swamp and underwater tables each combine levels **11–20**. For each
of these terrains, ranks 3 and 4 contain identical copies of that table.

## File format

Each line contains an inclusive percentile range and one encounter:

```text
01-05 2 `saber-toothed-tiger
06-07 1d4 `half-ogre
```

- Single outcomes use repeated bounds, such as `81-81`.
- The book's `00` means 100 and is written as `100-100`.
- Dice expressions omit spaces around addition: `1d6+2`.
- A backtick introduces a singular, lowercase, hyphenated stat-block name,
  following the existing generator's link convention.
- Wrapped descriptions are joined into one line. Noncombat encounters,
  alternatives, conditions, and descriptive details are retained.
- Spellcaster and warrior vampires retain their variant descriptions with
  the base `vampire` stat-block marker.

The current generator's XP calculation assumes that every number in the
encounter is a creature count. Source entries with alternatives, mounts,
implied counts, or additional numbers in descriptions can require manual
interpretation; transcription does not change that calculation.

## Recovered source entries

The following supplemental photographs supplied the sections cropped in the
original photos. All missing entries and counts have been transcribed; no
source placeholders remain.

| File | Rolls | Page | Source photograph |
| --- | --- | --- | --- |
| `desert/rank_3.txt` | 31–35 | 96 | `81684825067__573C9241-206D-492C-8AE8-01374B51E34C.jpeg` |
| `underdark/rank_3.txt` | 81–82 | 108 | `81684828860__F9E8AC50-491B-4A84-B7D7-B679BC4007F8.jpeg` |
| `underdark/rank_4.txt` | 54–62 | 109 | `81684828860__F9E8AC50-491B-4A84-B7D7-B679BC4007F8.jpeg` |
