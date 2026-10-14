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
