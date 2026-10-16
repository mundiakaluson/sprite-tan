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
| `animations/players/` | generated and tracked: `player_library.tres` (AnimationPlayer library), `player_flow.tres` (AnimationTree graph). One subfolder per animated feature |
| `shaders/` | `uv_skin.gdshader` |

## Controls
Keys and mouse buttons are **Input Map actions**, stored in `project.godot` under `[input]` and editable in Project > Project Settings > Input Map. Current actions: `move_order` (left click), `play_kick` (K), `open_pack` (Space). Scripts only ever name the action (`event.is_action_pressed("play_kick")`), never a key, so rebinding needs no code change. Add new actions there and use them from scripts.

## Folders
Scenes mirror scripts: `scenes/<feature>/` next to `scripts/<feature>/` (`scenes/players/player.tscn`, `scenes/cards/player_card.tscn`, `scenes/debug/main.tscn`). New scene = new or existing feature folder, never the scenes root. Run scene: `scenes/debug/main.tscn`.

## Scripts (one folder per feature)
| folder | what |
|---|---|
| `scripts/core/` | `data.gd` (static class `Data`, no autoload, so editor previews work): loads every CSV into `Data.tables` / `Data.by_id`, plus `Data.manifest`, `Data.anims`, `Data.rules`. `Data.tex("cards/SH01.png")` loads an exported image |
| `scripts/packs/` | `packlib.gd` (`PackLib`): port of `packs/packlib.py` (shop schedule, odds, pity, guarantee, pools, roll) |
| `scripts/cards/` | `player_card.gd` (`PlayerCard`), `player_tip.gd` (`PlayerTip`), `pixel_text.gd` (`PixelText`): cards built live from the CSV row with shared layers and the player's face. Stats are never baked into images |
| `scripts/players/` | `player.gd` (`Player`), `player_sprite.gd` (`PlayerSprite`: the recoloured picture, driven by the AnimationPlayer), `state_machine.gd` (`PlayerStateMachine`), `player_state.gd` (`PlayerState`, the base node for every state) |
| `scripts/players/states/` | states with logic: `state_run.gd`, `state_action.gd`, `state_timed.gd` |
| `scripts/engagement/` | `engagement_director.gd` (`EngagementDirector`, `g.engage`: picks which sim moments become engagements, freeze, picks, reveal), `engagement.gd` (one engagement), `duel_resolver.gd` (`DuelResolver`), `engagement_ai.gd` (`EngagementAi`, the AI manager's pick), `engage_card.gd` (`EngageCard`: reads `engage` / `effect` / `stats` of a card), `engagement_view.gd` (HUD bits) |
| `scripts/debug/` | `main.gd`: debug scene only (click = move, K = kick, SPACE = open a pack) |

Put new features in their own folder (for example `scripts/match/`, `scripts/ai/`, `scripts/ui/`), not in the scripts root.

### Animations (Animation panel, flow graph)
- `animations/players/player_library.tres` has one Animation per sprite sheet (175 now). Open `scenes/players/player.tscn`, select the **AnimationPlayer** node: every clip is in the dropdown in the bottom Animation panel, press play to see it (the `Sprite` shows the player). Each animation sets `Sprite:sheet` and `Sprite:frame_index`, and fires method calls at event frames (`strike`, `land`, ...).
- Select the **AnimationTree** node and open the bottom **AnimationTree** panel: the graph has a node per clip and **arrows** for the chains in `data/animation_flow.csv` (fall -> get up, stumbles -> recover step, ...). The tree follows arrows by itself.
- Both files are generated by the export every time (and committed). To change a flow, edit `data/animation_flow.csv` (tool: Other tables > animation_flow), then Export. Do not edit the graph in Godot, it is overwritten.
- Quick look without the player: select `Sprite`, pick `sheet` / `frame_index` / `direction` in the inspector. Cards: select the root node and set `player_id`. All of this needs an export first.

### Animation viewer (rotate while playing)
Open `scenes/debug/animation_viewer.tscn` and press **F6**. Pick a player and any clip from the list, then rotate while it plays: Left/Right or A/D (Input Map actions `rotate_left` / `rotate_right`), drag with the left mouse button, the Direction slider, or **Spin**. Also a clip filter, playback speed, Repeat and Pause. In the editor you can do the same by selecting `Sprite` and changing `direction` while the AnimationPlayer plays.

### Card animations
`scenes/cards/player_card.tscn` and `skill_card.tscn` each have an **AnimationPlayer**: `appear`, `hover_in`, `hover_out` (play automatically on mouse over), plus `foil_shimmer` on the player card (loops, animates `foil_frame` through the 36-frame strip) and `ready`, `unavailable`, `use`, `cooldown_end` on the skill card. They are hand-authored, so edit them in the editor. Code only calls `card.play("use")`. `SkillCard.new_card("SH01")` makes one; its hover tooltip is the exported tooltip image. Not yet ported: pack opening, Titan scenes, aura effects (still Python previews).

### Pack animations
`scenes/packs/pack_wrapper.tscn` (`PackWrapper`, scripts in `scripts/packs/`): the wrapper image from the export with an AnimationPlayer: `appear`, `hover_in/out`, `tremble`, `open` (placeholder punch). `PackWrapper.new_pack("weekly")`, `play_open()` then wait for `opened`. The dust disintegration and card reveal from `packs/opening.py` are still to be ported.

### Player states (edit them in the inspector)
`scenes/players/player.tscn` is the player: `Sprite` + `StateMachine`, and every state is a **child node of StateMachine**. The node's name is the state's name. The machine finds its children by itself; pick the start state in its `initial_state`.

Add a state without code: select `StateMachine` -> Add Child Node -> **PlayerState** (or `StateTimed`, `StateRun`, `StateAction`), rename it, then in the inspector set:
- `clip`: the animation to play (any name in the AnimationPlayer; arrows in the flow graph can continue it),
- `event_transitions`: `{"move_to": "Run", "stun": "Stunned"}` = event name -> state name,
- `go_to_when_clip_ends`: where to go when a non-looping clip ends.
Orders reach states as events: `player.move_to(pos)` sends `move_to`, `player.play_action("kick")` sends `play_action`, `player.send_event(&"stun")` sends anything you like.

Add a state with code: Create Script on the node, `extends PlayerState`, give it a `class_name` so it shows in Add Child Node, and override the `_on_enter`, `_on_exit`, `_on_update(delta)`, `_on_physics_update(delta)`, `_on_event(ev, data) -> bool` and `_on_clip_finished(clip) -> bool` you need. Use `player` and `sm` (`sm.transition_to(&"Run", {"target": pos})`). Use `@export` for anything you want to tune in the inspector. See `states/state_timed.gd` for a 10-line example.

Two Run nodes with different `speed_multiplier` give you Jog and Sprint with no new code.

## Rules
- CSV columns are the contract. Add columns, do not rename them, and the game keeps working.
- Sprite pixels are UV lookups, not colours: always draw them with `uv_skin.gdshader` and the player's atlas.
- Pity counters and owned cards belong in the save file, not the CSVs.

Rules for working in this project (folders, data contract, animation flow, states, input): see `CLAUDE.md` in this folder.
