# sprite-tan

A pixel-art football game where the 22 players play by themselves and you are the manager: you step in at
"engagements" (duels, shots, passes, aerials, one-on-ones) with a hand of ability cards, against an AI manager
playing by the same rules. Matches are about 5 minutes.

This repo holds the game data, the sprite pipeline, and (soon) a Python manager tool for editing the data and
exporting sprites. The Godot game itself has not been started.

## Layout

| Path | What |
| --- | --- |
| `data/` | CSVs the game loads at runtime: `cards`, `players`, `pack_odds`, `formations`, `formation_slots`, `formation_families`, `styles` |
| `sprites/` | Ray-cast pose engine and UV-lookup sprite renderer: `gen_player_v2.py`, `gen_actions.py`, `gen_uv.py`, `gen_hair.py`, `export_hair.py`. Built sheets are in `sprites/out_uv/` |
| `cards/` | Card face renderer (`cardlib2.py`) and emblem toolkit (`emblem.py`) |
| `scripts/` | One-off data generators (players, rarity, stats, formations). Run them from `data/` |
| `titan/` | Titan card cinematic demo scripts |
| `tool/` | The Python manager tool (to be built) |
| `docs/` | Design notes |

## Sprites

Characters are rendered from a 3D rig into small UV-lookup sprites: each pixel stores which texel of a 96x24 skin
atlas to show plus a tone, so skin, kit and hair colours are just different atlases. Cells are 40x40, 32 directions,
no outline. Hair is a separate layer sheet per style and animation (`sprites/out_uv/hair/`), drawn over the body.

```
cd sprites
python3 gen_uv.py          # body sheets, atlases, previews (about 2 minutes)
python3 export_hair.py     # 10 hair styles x 5 animations
```

Needs Python 3.10+, numpy, pillow (matplotlib for the formation preview).

## Data

Names in `players.csv` are respelled versions of real player names. They sit in one column and can be swapped
before any public or commercial release. `players_invented_names.csv` has a fully invented set.
