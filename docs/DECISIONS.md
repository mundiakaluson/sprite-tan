# Design decisions so far

Full text: the design document (see CLAUDE.md for the link).

- Match: about 5 minutes, clock pauses during engagements, about 20 engagements per side. Players play by themselves
  between engagements; the manager gives free orders and plays cards.
- Engagement types: duel, shot against keeper, pass contest, aerial, one-on-one. Six steps: trigger, freeze (slow motion),
  choose in secret (2-3 s), lock and reveal, resolve (stats + success roll + risk roll), aftermath.
- Cards: 200 in data/cards.csv with rarity, slots, success %, risk %, cooldown, timing (ANYTIME or ENGAGEMENT),
  kind (ACTION or BUFF), driving stats. No energy: cooldown only. Played cards stay in the hand and refill (MOBA style).
- Deck: built from a slot budget before the match. In the match you draw a hand of 8.
- Hidden choices in engagements; buffs, cooldowns and shot/pass aim lines are visible. Eagle's Eye shows the opponent's hand.
- Resolution: player stats (weighted by the card's `stats`) vs opponent; role fit penalty (orange about 8%, red about 20%).
- Players: 300 in data/players.csv, roles are free to place, no traits, looks from data (skin, hair style and colour,
  beard, glasses, chain, headband, wristband, tattoo).
- Formations: 10, one base class with family defaults and shared style offsets (data/formations*.csv, styles.csv).
- Economy: one currency (coins) from matches buys packs (500 basic, 1000-2000 rarer). Duplicates level up. No monetisation.
- HUD: score and clock on top, hand across the bottom, choice timer and orders bottom right.
- Stronger foot: every player has `foot` (R or L) in players.csv. Skill animations are authored and baked for the right foot only; a left-footed player uses
  the mirrored pose (moves.mirror_pose, previewed in the Cards tab) or, in the game, the right-foot sprite flipped horizontally with the direction index mirrored (32 - d).
- Shot animations: sprites/moves_shot.py generates data/animations/shXX_*.json (do not hand-edit those unless you also remove the id from the generator).
  Contact points are computed from the rig (moves.aim_ball / snap_ball), so the ball always meets the boot or head.
- Passing is the core verb, so pass cards have short cooldowns (1-5 turns of the 3-13 shot range; roughly 45% of the first pass values). Tune in data/cards.csv.
- Pass flow (interaction state): the manager picks a pass card, then taps the teammate to pass to (valid targets are highlighted, with an aim line showing speed and risk).
  The holder turns to face the target and plays the card's animation; the ball is released on the animation's `strike` event.
  If the manager does nothing the players pass by themselves: the holder scores teammates by openness, distance, forward progress and the holder's PAS,
  and keeps looking for a better opening until a defender closes in. A card played mid-hold overrides the AI choice.
- Ball variables on cards (cards.csv: ball_speed 0-10, ball_arc 0-10, ball_curve -5..5, blank when a card has no ball flight). The game flies the ball itself from
  these and the target, so the baked animation only supplies the body and the release frame. Player stats modify them:
  speed = ball_speed x (0.7 + 0.6 x stat/100), where stat is the average of the card's `stats` for that player (PAS for passes, SHO for shots; PHY adds to headers/long balls).
  Arc and curve scale the same way, and a weak stat also widens the aim error. So a driven pass from a high-PAS player is both faster and more accurate than from a low-PAS one.
  First-pass values were read off the animations; tune them in the Cards tab (ball speed / arc / curve).
- Dribble animations (sprites/moves_dribble.py): plain dribbles (Ball Roll, Drive Through, Quick Touch, Slalom, Burst of Pace, Wall Run, Dummy Run) show a grey translucent speed mist
  behind the direction of travel; the skill moves (step over, roulette, elastico, Cruyff turn, rainbow flick...) are custom body animations with no mist.
  The mist is 'quicksilver legs': grey translucent afterimages of the LEGS ONLY, taken from the previous 2-3 frames of the same animation and pushed back along the direction of travel,
  plus short speed streaks off each boot. It is a game-side effect, not part of the sprite sheet (the tool draws it with gen_uv.leg_trail; the game draws the previous frames' leg rows tinted grey under the
  sprite). animations.json carries a per-frame `mist` strength (0-1) and the heading. Turning moves rotate the body (`root_side_px` carries the sideways travel); the game keeps the new facing after the clip.
- The ball is independent: it is its own object in the game with its own position, height and velocity. Animations only supply the body. Each shot/pass animation stores a `contact` point
  (animations.json and the animation file: frame, part = boot_R / boot_L / head, and x, y, z relative to the player's root). The game plays the clip so that point lands on the ball
  (nudging the player to it) and launches the ball itself on the strike frame, using the card's ball variables and the player's stats. Ball paths inside the clips are previews only.
  Regenerating sprites/moves_*.py drops `contact`: run `python sprites/contacts.py` afterwards.
- Air passes: when the ball is already in the air (after a flick, a lob, a knock-down) a pass card uses an air version instead of its ground animation: the leg goes up to the ball.
  Three contact heights, chosen from the ball height at the moment the card is played: air_pass_low (knee, z~11), air_pass_mid (waist, z~20), air_pass_high (chest, z~30, standing foot hops).
  Above head height the player uses a header instead. These are generic animations, not tied to one card; the Cards tab can preview them (ball: in the air).

## SUPPORT cards (decided)
Support cards never replace what the player is doing. Default is an aura only: a glow around the selected player, or a brief pulse across the whole team for team effects (data/support_auras.csv: scope self/team/two/target/opponent, colour, shape, seconds).
A few cards add an upper-body overlay (columns overlay + side; sprites/overlays.py): head scan (Radar Vision), arm raise (Sixth Sense), fist up (Rally the Team), point (Wide Open, Captain's Orders, Decoy Run). It is blended onto the current animation, touching only that arm / the head, so the player keeps running, dribbling or shooting.
The earlier standalone gesture animations (sp01-sp30) were removed. The Cards tab preview has a "player is" selector (running / dribbling / shooting / jockeying / sprinting).

## KEEPER cards (decided)
GK01-GK25 are authored in sprites/moves_keeper.py (dives go to the keeper's right; the game mirrors for left). Saves are hand contacts: the animation has a strike frame and the game uses a hand reach zone; only the foot actions (sweeper clear, kick save, long kick, rebound clear) store a boot contact point. Carried balls (catches, throws) are held in the hands; incoming balls in the preview are placeholders, the game owns the ball. The Cards tab previews GK cards in the keeper kit.

## TITAN cards (decided)
Each Titan is its own cinematic scene, not a reused body with a coloured streak (that first attempt was rejected). Scenes are in titan/scenes.py on the engine in titan/engine.py (pitch, camera zoom, dim + letterbox + banner, hand of cards, the real Titan card sliding in, flash, result text, card going on cooldown) with effects in titan/fx.py (bolts, shockwaves, cracks, flames, vortex, reticle, glitch / chroma / gray post effects). 25 scenes, 4-6 seconds each, built from the baked player sprites (guard, run, slide and the skill / keeper animations plus tt05 Bicycle Kick and tt13 Earthquake Tackle bodies).
The Cards tab plays the scene in place of the move panel for TT cards (tool/titanwin.py renders it in a thread, then plays it). `python titan/scenes.py [TT01 ...]` writes GIFs to export/titan/ (git-ignored, about 77 MB for all) and contact sheets to /tmp.
The old titan/titan_zap.py and titan_demo.py are kept as the original reference.

- SUPPORT effects (tool/aurafx.py): one distinct, punchy effect per card (cast burst, then sustained effect, fade, rest) drawn on a 72x72 stage around the player; data/support_auras.csv `shape` = effect key. Still an aura over the player's current state; no on-screen text.
- Player variables on cards (cards.csv, blank when not used; first-pass values, tweak in the Cards tab). The animation supplies the body, these numbers tell the game how to drive it:
  move_mult (ground speed x PAC during the card, 1 = normal, 0 = planted), anim_rate (playback speed, shorter or longer commitment), travel (scale on root travel, e.g. slide length),
  reach (boot / hand zone size 0-10), steer (how much the player can change direction mid-card 0-10), lock (seconds committed before acting again).
  For SUPPORT buffs only move_mult is set (SP02 1.3, SP18 1.25, SP25 1.1, SP30 1.6) and applies while the buff lasts. Stats scale them the way they scale the ball variables.

## BASE ANIMATIONS (decided, not built yet)
- Set: idle, walk, jog, tired run, sprint (separate animations, no blended gait), jump (crouch / take-off / air / land), fall (forward / back / side), get-up (one for every fall), stumble (DIRECTIONAL, a few sizes), recover step, stun (for skills that stun), pain / limp state (after a heavy fall).
- Strength: the game compares the hit (and the pressed player's speed) with PHY. Outcomes: held (shoulder rock only) / stumble / knocked off the ball (still standing) / fall. A strong player mostly shows "held", a weak one "fall". Chest Out lifts the outcome one level.
- Build order proposed: idle, walk, jog, tired run -> stumble / knocked off / fall / get-up -> jump -> stun and pain / limp. Waiting for the user's go.
- BASE step 1 done (sprites/moves_base.py -> data/animations/base_*.json, baked): idle (breathing, weight shift, glance), walk, jog, tired run, sprint. All loop in place; the game moves the root and plays them at rate = speed / ground_speed_px_s (data/gaits.csv, clamped min_rate..max_rate) so feet don't slide. Next: stumble (directional) / knocked off / fall / get-up, then jump, then stun and pain / limp.
- Base animations have their own tab (tool/tab_base.py, rows in data/base_animations.csv, status = anim file exists), separate from the Cards tab and the skill animations.

## PACKS (decided, not built yet)
- Sources: bought with coins, or won as a weekly ranked reward (reward packs carry a `source` flag and are not purchasable).
- Limited timed packs: packs are fully data-driven (definition + pool + odds + schedule start / end), so a "pack studio" (the Packs tab now, a creator tool later) can make new ones without code. Expired packs disappear from the shop.
- Pity counter: a dry spell raises the next rare-or-better chance (per player, per pack type); counter and thresholds are columns, tweakable.
- Opening: one card at a time with a reveal animation (rarity flash, bigger for epic / legend); skippable (a skip button in game jumps to the summary, duplicates level up the owned card).
- Pieces: pack definition + pool tables, pack wrapper art generated from data, opening animation, Packs tab (create / duplicate pack, price, counts, odds with a live total, pools by category / rarity / id, guarantee, pity, schedule, wrapper + opening preview), pack-odds simulator.
- Build order proposed: data tables + Packs tab -> simulator -> wrapper art -> opening animation. Waiting for the user's go.

## SKILL CARD FACE v2 (decided)
Skill cards now use the player-card language (cards/cardlib2.py `card`; old face kept as `card_old`): dark field with a glow in the CATEGORY colour, thin frame in the RARITY colour,
big slot number top left with the category under it, rarity top right, plain name with side lines, three stats (HIT / RISK / CD) with no boxes and thin bars. Titan cards use the galaxy foil and a foil frame.
Emblems: no mini footballers (decided). Emblems are ball, direction arrows, stars and icons only; the old figure calls are switched off (emblem2.FIGURES) and recipes.fit() drops the ground line, centres and doubles what is left. Some may need a proper redraw later.

## PACKS (built)
Tables (all loaded at runtime, edited in the Packs tab or Excel):
- `data/packs.csv`: id, name, source (shop / ranked / event), price, player_items, card_items, tier, foil, silhouette, guarantee_min, pity_rarity, pity_start, pity_step, pity_hard, start, end, sort, active, note.
  Weekly ranked rewards use source=ranked, price 0. Limited packs set start/end (event); expired, upcoming and inactive packs are not in the shop (`packlib.shop()`).
- `data/pack_odds.csv`: pack id, common..legend percent per item.
- `data/pack_pools.csv`: pack, kind (player/card), category (role or card category), rarity, id, mode (include/exclude), weight. No rows for a kind = everything; a rarity the pool empties falls back to the whole table.
Pity: counter per pack type in the player's save (packs since the last pity_rarity+). After pity_start dry packs the odds lift by pity_step points per extra pack toward pity_rarity and better; pity_hard dry packs force one. Boost 0 and hard 0 = off.
Logic: `packs/packlib.py` (no Tk; roll, weights, state, simulate, check). Wrapper art: `packs/design2.foil_bag(row)`. Opening: `packs/opening.py` (Scene; `skip_to` jumps to the summary).
Opening look (decided): pack settles in, trembles, disintegrates to dust, ends with a punch, cards settle in a stack, reveal one at a time; no rays or rings. Card back is blank with one tier-colour border.
Tool: Packs tab (list, Definition, Odds/guarantee/pity with live total and a dry-spell slider, Pools with eligible counts, Look with tilt shimmer, Simulator for one pack or all packs, Opening preview with Skip).
Not done yet: pity counter in the save, the shop UI, wrapper extras ("substance" ideas). Logic is ported to `godot/scripts/packlib.gd`.

## ANIMATIONS (status)
All skill-card categories are baked: SHOT 30, PASS 25 (+3 air variants), DRIBBLE 29, DEFEND 35, SUPPORT 30, KEEPER 25, TITAN 25 cinematic scenes. Defend and Keeper had a natural-arms pass (9 clips: DF01, DF03, DF04, DF05, DF10, DF20, DF30, DF33, GK01). Rest of the Defend/Keeper clips, Hold Up Play and a few weak Titan scenes are still to polish. Base animations (idle, walk, jog...) are in progress.

## GODOT + EXPORT (built, untested in Godot)
- The Godot project lives in `godot/` (Godot 4.2+, nearest filtering, 960x540 viewport, integer scaling). Data and art are generated into `godot/data/` and `godot/assets/` by the tool's global **EXPORT TO GAME** button (`tool/export_game.py`); those folders are git-ignored, so after cloning press Export once.
- Export steps: CSV data, sprite sheets + skins + `animations.json` + shader, hair layers, one 96x24 look atlas per player, skill card faces + tooltips, modular player cards (shared bg/outline layers per rarity, 3 foil strips, one small face per player, the pixel font and `card_rules.json`; the game draws text, stats and tooltips live so nothing per-player is baked), pack wrappers + tier card backs, `export_manifest.json` (time, git commit, counts).
- Game side: static class `Data` (`scripts/core/data.gd`, no autoload so editor previews work) reads every CSV (columns are the contract: add, never rename); `PackLib` ports `packlib.py`; `PlayerSprite` plays a sheet through `uv_skin.gdshader` with the player's atlas.
- Saves hold what is not data: owned cards, pity counters, coins.
- Godot was not installed where this was written, so the GDScript has not been run.
- Player cards are modular on purpose: one face image per player, everything else shared or drawn from the CSV. Changing a stat needs no re-export. Skill cards are still one image each (unique emblem art) plus tooltips; making their text live is a possible follow-up.
- Player states are nodes: scenes/players/player.tscn has Sprite + StateMachine, each state a child node (PlayerState base with clip, event_transitions and go_to_when_clip_ends exports). New states can be added in the inspector with no code, or with a script that extends PlayerState (user and Claude both write Godot code).
- Player animation is Godot-native: one Animation per sprite sheet in an AnimationPlayer library (generated by the export into godot/animations/players/), plus an AnimationTree state machine whose arrows come from `data/animation_flow.csv`. The sprite node is passive (sheet, frame_index, direction set by the animation). Gameplay states (PlayerState nodes) ask for clips by name. Rules for the Godot project live in `godot/CLAUDE.md`.
- Everything animated is a Godot animation (AnimationPlayer in its scene). Cards: player_card / skill_card scenes with appear, hover, foil_shimmer, use, cooldown_end. Still to port from Python previews: pack opening, Titan scenes, aura effects.
- Folders for animated features: scripts/<feature>, scenes/<feature>, animations/<feature> (generated libraries). Pack wrapper scene (appear, hover, tremble, open placeholder) is in scenes/packs.

## Stadiums and pitches
- data/stadiums.csv (3 to start: ST01 Old Ground day, ST02 City Bowl night, ST03 Seaside Park dusk). Generator stadiums/stadiumlib.py, export step `stadiums` writes godot/assets/pitches/<id>/ (tracked).
- Pitch is a flat texture in a 3D scene, TV camera with perspective, own goal on the left; 105x68 m at 16 px/m, depth squashed 2:1. Pitch texture 1872x1280 (stands, crowd, boards, lights) is larger than the viewport; the match camera scrolls over it.
- Goals are side-on, two layers (back: behind players; front: near post and net over players; right goal = flipped left). Godot: scenes/stadium/stadium.tscn with stadium_id and pitch_to_screen().
- Player scene: select the root to get a Facing slider (0-31) for previewing directions.
- Revised: the stadium is a 3D Godot scene (TV camera with real perspective, like FIFA/EA). Generator now outputs pitch.png (flat top-down, 16 px/m), stand.png, boards.png, net.png; stands, goals, flags and floodlights are built from simple 3D parts in stadium.gd. Players stay 2D sprites projected onto the screen (Stadium.add_actor). Debug scene: scenes/debug/stadium_viewer.tscn (A/D camera, 1-3 stadium).

## Goals, stadium editor, camera (decided)
- data/goals.csv: modular goal styles (size, net depth top/ground, mesh cell, colours, net stiffness / damping / sag / drag, post sway, bounce). stadiums.csv picks one (goal column) and stores the TV camera (cam_height, cam_back, look_z, fov).
- Net = spring mesh (Verlet + links), front edge and ground pegged; ball pushes the points; posts and bar are damped springs. Same maths in stadiums/goallib.py (tool) and godot/scripts/stadium/goal_net.gd; Godot node: goal.gd (`ball_update(pos, vel)` returns the new ball velocity, signals hit_net / hit_frame). The Python Goal simulator tab is where the numbers get tuned.
- Python tool: Stadiums tab (table + colours + crowd / worn / floodlight / camera sliders + live software-rendered TV preview) and Goal simulator tab (shoot at the goal, tune the feel, three views). stadiums/preview.py is the software renderer (same camera maths as Godot).
- Camera: stadium is real 3D, so orbit / crane / push-in replay shots are possible. Plan: record positions every frame, replay through a camera path (data-driven shots). Not built yet (needs the match view).
- Net feel config (goals.csv): stiffness (taut), stretch 0-1 (0 hard and new, 1 soft; the ball sinks deeper), wear 0-100 (looser, sags lower in the middle, flaps longer, fainter). stadiums.csv `net_wear` overrides a style's wear per stadium (old grounds, worn nets; blank = the style's own). Formulas live in goallib.feel() and GoalNet.apply(); the Goal simulator tab has the sliders; exported to Godot with the CSVs (layout.json carries net_wear).

## Ball studio (decided)
- data/balls.csv: gravity (m/s2), air drag, Magnus swerve, knuckle wobble (metres) above a speed with little spin, dip (drag jump below a critical speed, Jabulani-style), bounce, grip, rolling drag, spin decay, mass, radius, texture (pattern + 3 colours + shine) and gameplay factors touch (first touch) and power (kick speed). Four to start: Match ball, Knuckler, Rain ball, Moon ball.
- Tool: Ball studio tab (edit, spinning preview, trajectory lab comparing every ball for the same shot). Physics shared by balls/balllib.py and godot/scripts/ball/ball_physics.gd. Textures: 16-frame roll sheet per ball, export step `balls`.
- Gameplay: kick speed = base x ball power; first touch quality x ball touch; swerve / knuckle / dip / bounce / grip act through the physics. The ball is a 3D point drawn as a pixel sprite; collisions use 3D physics, never pixels.
- Ball rotation (decided): the ball keeps a real 3D orientation turned by its spin every physics step; the pixel sprite is drawn by shaders/ball.gdshader from an equirectangular panel map (assets/balls/<id>_map.png). So rolling rolls, backspin tumbles, a trivela / finesse turns about a tilted axis, and a knuckle ball (almost no spin) barely turns while its path wobbles. Spin comes from kick styles (data/kick_styles.csv: speed, elevation, aim, side / back / roll spin, power, aim error); Ball.kick(from, aim, style_id, strength) builds the shot. Tool: Kick styles tab + Kick style dropdown and a slow-motion spin preview in the Ball studio.

## Match scene, first playable (decided)
- Main scene is scenes/match/match.tscn (scripts/match/): MatchGame runs the sim, Team / Footballer hold the squads, MatchHud draws score, clock, toasts and the hand of 8 real SkillCards. Players are 2D sprites in the 3D stadium; everything is simulated in metres (x along, z across) and only projected for display.
- Real-time for now (the 5 minute clock with engagement freezes comes later): 90 game minutes in `match_minutes` real minutes. You control the carrier, otherwise the player nearest the ball; WASD move, J pass / tackle, L lob, K shoot, Shift sprint, Q switch, 1-8 cards.
- Cards in this slice: SHOT and PASS cards kick with a kick style picked from the card's curve / arc (success % decides clean strike or miscue), DRIBBLE cards give a short tackle shield (fail = ball lost), DEFEND cards are tackles near the carrier. Cooldown seconds = cd x cooldown_scale. Other cats say "not in this build".
- Placeholder AI: formation slots + ball-side shift, one chaser per team, carrier dribbles / shoots inside ~24 m / passes under pressure, keeper tracks the ball and catches or parries by HAN / REF. Tune in MatchGame exports; move numbers into data/ once they settle.

## Match controls and ball states (decided)
- No keyboard walking: the human is a manager. Mouse: click a player of yours for his order menu (with the ball Pass / Through / Lob / Shoot; without Run / Press / Tackle), then click a team mate or a spot; or drag from a player to a spot to make a run (the AI runs it, then plays on). Controller: the stick moves the pointer, Cross = click, Triangle held = press and hold (drag), Circle = cancel. Same code path as the mouse.
- Ball states (nodes, editable in the inspector): Free, Held, Pass, Through, Lob, Shot. Kick numbers come from data/ball_actions.csv (style, speed rule, lead, stat). A through ball aims ahead of the receiver and sends him running.
- Next steps agreed: HUD look, then one AI file per role with switch cases per formation, then player / ball foot collisions.

## Match gestures and layout (decided)
- Double click a team mate = pass, right click = lob, drag from the ball carrier = shoot with time slowed to ~30% while you line it up, drag from anyone else = a run, click a player = a small menu (Through, Run, Press, Tackle). Controller: Cross click, Square lob, Triangle held drag, Circle cancel.
- The HUD never covers the pitch: the pitch view is the top 420 px, the HUD strip (score, clock, selected player, hint, hand of 8 cards, controls) sits under it.

## Match structure, build-up and AI (decided)
- MatchGame is thin; settings are one resource (MatchSettings, inspector); possession, motion, rules, orders, cards are separate modules. No pop-ups in the match: order buttons live in the HUD strip.
- Pace: players accelerate and turn like people (accel 7 m/s2, top speed from PAC), the carrier runs slower than a free player, the ball sits ahead of the feet. Build-up: the team has a phase (build-up, progress, final third / organise, press, transition); the carrier holds the ball a moment, then passes by score (forward gain, space, ideal length, blocked lanes, risk) and shoots only inside the shoot range with a clear lane; a pass receiver runs onto the ball. Shape = formation slot + styles.csv offsets for the phase + team line + slide to the ball, using the formation's numbers (line height, width, compactness, press, overlap, directness, counter, risk).
- AI is one file per role (scripts/ai/roles) with formation-aware switch cases; the user refines them.
- Everything ships to the inspector: AI roles are Resources (all numbers `@export`, grouped) collected in an AiProfile .tres per team (MatchSettings > AI); the other modules' constants (order timing, card effects, keeper/control) are MatchSettings groups. No tweakable literals in code.
- Formation AI: one Resource per formation in scripts/ai/formations (AiProfile > Formations). 4-4-2 (F01) from tactico.pro: two banks with set gaps that move with the ball, no press without a trigger (full back, back pass, carrier facing own goal), full back overlaps when the wide mid holds width and underlaps when he comes inside, one CM always behind the ball, one striker drops into the pocket and one stays on the last defender's shoulder.

## Pitch map and HUD room (decided)
- The pitch map is data (data/pitch_zones.csv areas, data/pitch_spots.csv points) read by a static PitchMap class, in the team's frame (x across from the team's left, y from own goal to opponent goal, percent) like the formation slots, so one file serves both teams. AiContext exposes it (spot / zone / in_zone / zones_at) to every role; it is deliberately not inherited, so rules, HUD and tools can use it too.
- HUD: cards at 75% and the tooltip at 1.5x (exports on the Hud node), with a TEAM area reserved next to the hand for team commands (set_team_commands, signal team_command). The commands themselves are still to be decided.

## Team stances and the current command (decided)
- Teams live under their formation: the formation file organises, presses and blocks. TEAM buttons (auto, press high, mid block, park bus, push up, counter) are stances that lean the formation's numbers; `auto` follows the formation and switches by minute and score. Details in godot/CLAUDE.md.
- Drag from the ball carrier: snap to the nearest mate = pass, dragged further = through ball (runner ringed), into the goal area = shot. A small HUD box shows the current command (pass / through / shoot / run / card / team) from one state store (MatchCommand) that every action writes to.

## HUD art (decided)
- The HUD is complete pixel art in the card language, 1:1 on the 960x540 screen (no fractional scaling: cards in the hand at their real 64x90). Panels and buttons are dark-field frames with cut corners tinted by an accent (team kit colour, command kind colour); text is the cards' 3x5 pixel font.
- Generated, not hand-painted: hud/hudlib.py + data/hud_style.csv, exported to assets/ui by the HUD art step; Godot side = PixelPanel / PixelLabel / PixelButton / PixelImage in scripts/ui. Next: HUD tab in the tool to preview, icons for the orders and stances, the GOAL / KICK OFF banners, the pitch-side score bug.


- Score bug: design A (top-left, home/away/clock boxes, RANKED/UNRANKED tag). Ranked = gold frames + corner studs + division and stakes line; unranked = steel. MatchSettings group Scoreboard. Full screen: stretch scale_mode fractional, F11 toggles.
- Game view is now 1280x720 (pitch SubViewport 1280x580, HUD strip 1280x140 below) so the camera can zoom on the players and the HUD still fits.
- Layout is adaptive: stretch canvas_items + aspect expand; pitch view fills the window above a 140 px HUD strip, HUD nodes are anchored (orders left, hand centre, team/command right). Strip art tiles.
