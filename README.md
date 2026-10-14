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

## Manager tool

```
python tool/app.py
```
Tabs:
- **Players**: the 300 players as an Excel-style grid (double-click a cell to edit), with a live animated sprite preview, look pickers
  (skin, hair style and colour, beard, glasses, chain, headband, wristband, tattoo), stat boxes, auto rating, and export of
  every player's look atlas to `export/looks/`.
- **Cards**: the 200 cards with the live card face (the `cards/cardlib2.py` design: no description on the card, hover tooltip instead), ready / cooldown / unavailable states, a hand-of-8 preview, and export of faces and tooltips to `export/cards/`. All 200 cards have an illustrated emblem (SH01-SH30 in cards/cardlib2.py, the rest in cards/recipes.py); new cards get a category placeholder until a recipe is added.
- **Formations**: formation settings, slots, and a pitch where you drag the dots; BUILD/ATTACK/DEFEND shows each style's offsets.
- **Animations**: make new moves without drawing. Start blank or from run/kick/finesse/guard/slide, pose the figure with sliders
  (hips, chest, head, feet, knees, arms, ball), key frames on the timeline, preview with onion skin, then export to the game
  sprite sheets (optionally with hair layers). Saved as `data/animations/<name>.json`.
- **Other tables**: packs, looks palette, styles, families. **Checks**: validates every CSV. **Build**: buttons for the self-test, the body-sheet rebuild (`gen_uv.py`) and the hair-layer rebuild (`export_hair.py`), with a live log and a Stop button. **Sprite import**: recolour any PNG sheet.

Everything is plain CSV in `data/`, so Excel works side by side: edits made in Excel appear in the tool automatically (unless you have
unsaved edits there), and the tool writes a `.bak` copy before each save. Close the file in Excel before saving from the tool.
Headless checks: `python tool/selftest.py`. Custom animations also export from the command line: `python sprites/custom_anims.py NAME --hair`.
