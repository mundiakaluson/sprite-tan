# Godot project

Godot 4.2+. Nothing in here has been run yet (the project was written without Godot installed), so expect to fix a typo or two on first open.

## Get the data in
1. Open the manager tool (`python tool/app.py`) and press the big green **EXPORT TO GAME** button (or run `python tool/export_game.py`).
2. Open this folder (`godot/`) in Godot. It imports the new images on first open.
3. Press Play. The debug scene shows a recoloured runner, a player card, a skill card and a pack wrapper; SPACE opens a pack (result in the Output panel).

`assets/` (except `assets/pitches/`) and `data/` are generated and git-ignored. `assets/pitches/` (hand-made pitch art), `shaders/`, `scripts/`, `scenes/` and `project.godot` are tracked.

## What the export writes
| folder | content |
|---|---|
| `data/` | every CSV and json from the repo `data/`, `looks_index.csv`, `card_rules.json` (card layout numbers), `export_manifest.json` |
| `assets/sprites/` | `NAME_uv_sheet.png` per animation (frames across, 32 directions down, 40x40 cells), `animations.json` (frames, ms per frame, loop, events, root motion), skin atlases |
| `assets/hair/` | hair layer sheets (same layout as the sprite sheets) |
| `assets/looks/` | `PLxxx.png`: each player's 96x24 look atlas |
| `assets/cards/` | skill card faces `ID.png` and tooltips `ID_tip.png` |
| `assets/faces/` | one small head-and-shoulders image per player |
| `assets/card/` | shared player-card layers: `bg_RARITY`, `top_RARITY`, `foil_STYLE` strips (36 frames) |
| `assets/font/` | the 3x5 pixel font atlas + `chars.txt` |
| `assets/packs/` | pack wrappers `PACKID.png` and `back_common.png` ... `back_legend.png` |
| `assets/pitches/` | not generated: hand-made pitch art, tracked in git |
| `shaders/` | `uv_skin.gdshader` |

## Scripts (one folder per feature)
| folder | what |
|---|---|
| `scripts/core/` | `data.gd` (autoload `Data`): loads every CSV into `Data.tables` / `Data.by_id`, plus `Data.manifest`, `Data.anims`, `Data.rules`. `Data.tex("cards/SH01.png")` loads an exported image |
| `scripts/packs/` | `packlib.gd` (`PackLib`): port of `packs/packlib.py` (shop schedule, odds, pity, guarantee, pools, roll) |
| `scripts/cards/` | `player_card.gd` (`PlayerCard`), `player_tip.gd` (`PlayerTip`), `pixel_text.gd` (`PixelText`): cards built live from the CSV row with shared layers and the player's face. Stats are never baked into images |
| `scripts/players/` | `player.gd` (`Player`: sprite + row + state machine), `player_sprite.gd` (`PlayerSprite`: sheet player with the recolour shader), `state_machine.gd` (`PlayerStateMachine`), `player_state.gd` (`PlayerState`, the base for every state) |
| `scripts/players/states/` | one file per state: `state_idle.gd`, `state_run.gd`, `state_action.gd`. To add one: extend `PlayerState`, register it in `Player._build_states()` |
| `scripts/debug/` | `main.gd`: debug scene only (click = move, K = kick, SPACE = open a pack) |

Put new features in their own folder (for example `scripts/match/`, `scripts/ai/`, `scripts/ui/`), not in the scripts root.

Player states: a state gets `enter(msg)`, `update(dt)`, `physics_update(dt)`, `on_event(name, data)`, `on_clip_finished(clip)`, `exit()`. Change state with `sm.transition_to(&"run", {"target": pos})`; outside code gives orders with `player.move_to(pos)` and `player.play_action("kick")`. Clips that are not baked yet (like `base_idle`) are skipped, and idle falls back to a frozen `run` frame.

## Rules
- CSV columns are the contract. Add columns, do not rename them, and the game keeps working.
- Sprite pixels are UV lookups, not colours: always draw them with `uv_skin.gdshader` and the player's atlas.
- Pity counters and owned cards belong in the save file, not the CSVs.
