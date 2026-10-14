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

## Run it

Windows (PowerShell):

```
git clone https://github.com/mundiakaluson/sprite-tan
cd sprite-tan
python -m venv .venv
.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt

cd sprites                        # run the scripts from this folder
python gen_uv.py                  # body sheets and skin atlases, about 2 minutes
python export_hair.py             # the 10 hair styles, about 2 minutes
python preview_hair_styles.py     # makes hair_test.png, a contact sheet of every style
```

macOS / Linux: the same, but use `python3`, and activate with `source .venv/bin/activate`.
Already cloned? Run `git pull` to get the latest files.

The built sheets are already committed in `sprites/out_uv/`, so you only need to run these after changing the code.
Python 3.10 or newer. The scripts that make `data/*.csv` are in `scripts/` and are run from `data/`.

## Data

Names in `players.csv` are respelled versions of real player names. They sit in one column and can be swapped
before any public or commercial release. `players_invented_names.csv` has a fully invented set.
