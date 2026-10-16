class_name EngagementDirector
extends RefCounted
## Turns some moments of the running sim into engagements (design doc 9a / 9b): the sim asks first (`duel(...)`), the director decides
## whether this one becomes an engagement (gap since the last, pace towards engage_target per side, how high up the pitch), and if so
## freezes it: the match clock stops, play drops into slow motion, both sides pick a card or the free default in secret, the picks are
## revealed together, then the resolver plays the outcome out through the normal sim (take-on, tackle, slide...). If it says no,
## the sim carries on by itself as before.
## Manual or Auto per side: Team.engage_auto (home from MatchSettings > Engagements > home_auto_engage; away is always Auto).
## Numbers: MatchSettings > Engagements. Counters `stat_*` for headless tests.

signal started(e: Engagement)
signal revealed(e: Engagement)
signal finished(e: Engagement)

var g: MatchGame
var ai: EngagementAi
var duel_resolver: DuelResolver
var double: DoubleTeam             ## Double Team's zap (cards with effect move=double)
var current: Engagement = null
var play_t := 0.0                  ## play seconds since the last engagement ended
var count := {}                    ## Team -> engagements as the ball side
var stat_started := {}             ## type -> n
var stat_outcomes := {}            ## "type outcome" -> n
var stat_cards := {}               ## "ball" / "challenge" -> cards played
var stat_defaults := {}            ## "ball" / "challenge" -> free defaults
var stat_declined := 0
var log: Array[String] = []

func _init(game: MatchGame) -> void:
	g = game
	ai = EngagementAi.new(game)
	duel_resolver = DuelResolver.new(game)
	double = DoubleTeam.new(game)
	play_t = 999.0

## true while an engagement is being chosen or revealed (the clock stops, play is in slow motion)
func frozen() -> bool:
	return current != null

## is this player in the engagement right now (the AI leaves him alone, nobody else tackles him)
func busy(f: Footballer) -> bool:
	return current != null and current.involves(f)

## the human can pick for this team now
func waiting_for(team: Team) -> bool:
	return current != null and current.step == Engagement.Step.CHOOSE and not team.engage_auto and not current.picked(team) and current.involves_team(team)

## seconds the human has left to pick
func time_left() -> float:
	if current == null: return 0.0
	return maxf(0.0, g.settings.engage_choose_time - current.t)

# ---------------------------------------------------------------- asking
## the sim is about to play a duel: `move` is what `initiator` was going to do ("takeon", "tackle", "slide").
## Returns true when it became an engagement (the caller must NOT play its move then; the resolver will).
func duel(carrier: Footballer, defender: Footballer, initiator: Footballer, move: String) -> bool:
	var s := g.settings
	if not s.engage_on or current != null or g.phase != MatchGame.Phase.PLAY: return false
	if carrier == null or defender == null or g.carrier != carrier or carrier.team == defender.team: return false
	if carrier.is_keeper() or defender.is_keeper(): return false
	if carrier.lock > 0.0 or defender.lock > 0.0 or defender.no_touch > 0.0 or not carrier.aim_done.is_null(): return false
	if g.dribble.busy(carrier) or g.dribble.busy(defender): return false
	if play_t < s.engage_min_gap or not _pace_ok(carrier.team):
		stat_declined += 1
		return false
	var depth := clampf((carrier.pos.x * carrier.team.dir + MatchGame.HALF_L) / (2.0 * MatchGame.HALF_L), 0.0, 1.0)
	if g.rng.randf() > lerpf(s.engage_chance_deep, s.engage_chance_high, depth):
		stat_declined += 1
		return false
	var e := Engagement.new()
	e.type = "duel"
	e.ball = carrier
	e.challenger = defender
	e.initiator = initiator
	e.move = move
	e.start_clock = g.clock
	_begin(e)
	return true

var _press_t := 0.0

## the main trigger (design doc 2): the defending side's presser gets into the carrier's engagement zone
func _press_check(dt: float) -> void:
	var s := g.settings
	_press_t -= dt
	if _press_t > 0.0: return
	_press_t = s.engage_press_every
	var c := g.carrier
	if c == null or c.is_keeper(): return
	var other := g.away if c.team == g.home else g.home
	var ctx: AiContext = g.brain.ctx.get(other)
	if ctx == null or ctx.presser == null: return
	var p := ctx.presser
	if p.pos.distance_to(c.pos) > s.engage_press_zone or p.ai.get("engage_try", -99.0) > g.clock - s.engage_press_retry: return
	p.ai["engage_try"] = g.clock
	duel(c, p, p, "tackle")

func _pace_ok(team: Team) -> bool:
	var s := g.settings
	var expected := float(s.engage_target) * g.clock / MatchGame.GAME_SECONDS
	return float(count.get(team, 0)) < expected + s.engage_pace_slack

func _begin(e: Engagement) -> void:
	current = e
	count[e.ball.team] = int(count.get(e.ball.team, 0)) + 1
	stat_started[e.type] = int(stat_started.get(e.type, 0)) + 1
	e.ball.ai.erase("engage_fall")
	e.ball.shield = 99.0                                                       # nobody else nicks it while we choose
	started.emit(e)

# ---------------------------------------------------------------- choosing
## the human picks hand card `i` (MatchCards.play routes here while waiting_for(home))
func pick_index(team: Team, i: int) -> bool:
	if not waiting_for(team): return false
	var hand: Array = g.cards.hand_of(team)
	if i < 0 or i >= hand.size(): return false
	var c: Dictionary = hand[i]
	if not g.cards.can_play(team, c, current):
		g.hud.toast("%s: not for this %s" % [c["name"], current.type] if g.cards.ready(team, c) else "%s: cooling down" % c["name"])
		return false
	current.picks[team] = c
	g.hud.card_used(i)
	return true

## the human chooses the free default now (no card)
func pick_default(team: Team) -> void:
	if waiting_for(team): current.picks[team] = {}

func update(dt: float) -> void:
	var e := current
	if e == null:
		if g.phase == MatchGame.Phase.PLAY:
			play_t += dt
			_press_check(dt)
		return
	var s := g.settings
	var real := dt / maxf(Engine.time_scale, 0.01)
	e.t += real
	if g.phase != MatchGame.Phase.PLAY or g.carrier != e.ball:
		_end(e, "cancelled")
		return
	match e.step:
		Engagement.Step.CHOOSE:
			for team in [e.ball.team, e.challenger.team]:
				if e.picked(team): continue
				if team.engage_auto:
					if e.t >= s.engage_ai_think: e.picks[team] = ai.pick(e, team)
				elif e.t >= s.engage_choose_time:
					e.picks[team] = {}                                          # no pick in time: the free default
			if e.picked(e.ball.team) and e.picked(e.challenger.team): _reveal(e)
		Engagement.Step.REVEAL:
			if e.t >= s.engage_reveal_time: _resolve(e)
		Engagement.Step.ZAP:
			if not double.active(): _finish_resolve(e)

func _reveal(e: Engagement) -> void:
	e.step = Engagement.Step.REVEAL
	e.t = 0.0
	for team in [e.ball.team, e.challenger.team]:
		var c := e.card_of(team)
		var side := e.side_of(team)
		if c.is_empty():
			stat_defaults[side] = int(stat_defaults.get(side, 0)) + 1
		else:
			stat_cards[side] = int(stat_cards.get(side, 0)) + 1
			g.cards.start_cooldown(team, c)
	revealed.emit(e)

## true while a card's effect plays out between the reveal and the resolve (time runs at double_slowmo, not the freeze)
func zapping() -> bool:
	return current != null and current.step == Engagement.Step.ZAP

func _resolve(e: Engagement) -> void:
	if e.type == "duel" and EngageCard.effect_str(e.card_of(e.challenger.team), "move") == "double" and double.start(e):
		e.step = Engagement.Step.ZAP                                       # the helper zaps in first; the duel resolves when he lands
		e.t = 0.0
		return
	_finish_resolve(e)

func _finish_resolve(e: Engagement) -> void:
	e.ball.shield = 0.0
	match e.type:
		"duel": duel_resolver.resolve(e)
	_end(e, e.outcome)

func _end(e: Engagement, outcome: String) -> void:
	if e.ball.shield > 50.0: e.ball.shield = 0.0
	if e.helper != null and double.active(): e.helper.lock = 0.0             # cancelled mid-zap: let him go
	double.clear()
	e.outcome = outcome
	e.step = Engagement.Step.DONE
	var k := "%s %s" % [e.type, outcome]
	stat_outcomes[k] = int(stat_outcomes.get(k, 0)) + 1
	log.append("%5.0f  %s  %s (%s) %s  vs  %s (%s) %s  -> %s %s%s" % [e.start_clock, e.type, e.ball.display_name(), e.ball.role, EngageCard.label(e.card_of(e.ball.team), "default"),
		e.challenger.display_name(), e.challenger.role, EngageCard.label(e.card_of(e.challenger.team), "default"), outcome, e.note, ("  + %s (%s)" % [e.helper.display_name(), "deep" if double.deep else "upfield"]) if e.helper != null else ""])
	current = null
	play_t = 0.0
	finished.emit(e)
