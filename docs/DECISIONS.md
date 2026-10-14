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
