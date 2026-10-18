class_name DuelResolver
extends RefCounted
## Resolves a duel engagement (carrier vs defender) and plays the result out through the normal sim: the take-on (MatchDribble.take_on with a
## forced bite / read), the standing tackle (MatchPossession.start_tackle), the slide (MatchDribble.slide_tackle), a poke, a loose ball or a foul.
##
## Rolls (design doc section 5):  P = clamp(succ + engage_k x (A - D), engage_p_min, engage_p_max) for each side, where succ is the card's
## (or engage_default_succ for the free default) and A / D the two players' stats weighted by each card's `stats` (no card: DRI vs DEF).
## Both roll. One succeeds = he wins; both = the bigger margin wins; neither = the ball runs loose. The card is never a free pass:
## a strong defender beats a weak dribbler who plays a skill card more often than not.
## Risk: a failed card fires its bad consequence with risk % (the dribbler goes down, the defender is left on the floor);
## a won defending card is a foul instead with risk % x engage_risk_win_share.
## Card effect keys (cards.csv `effect`): move = feint / skill / flick / burst / shield (ball side), stand / slide / poke / charge / double / foul
## (challenge side); strand = how much longer a beaten defender is out of play; burst = burst speed factor.
## Double Team (move=double): a team mate has zapped in first (DoubleTeam); the challenge stat gets double_stat_bonus and, upfield, the helper makes the tackle from behind.

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

func resolve(e: Engagement) -> void:
	var s := g.settings
	var c := e.ball
	var d := e.challenger
	var ca := e.card_of(c.team)
	var cd := e.card_of(d.team)
	var a := EngageCard.stat(c, ca, "DRI")
	var dd := EngageCard.stat(d, cd, "DEF")
	if e.helper != null: dd += s.double_stat_bonus                                 # two on one (Double Team)
	var pa := clampf((s.engage_default_succ if ca.is_empty() else Data.num(ca["succ"], 60.0)) + s.engage_k * (a - dd), s.engage_p_min, s.engage_p_max)
	var pd := clampf((s.engage_default_succ if cd.is_empty() else Data.num(cd["succ"], 60.0)) + s.engage_k * (dd - a), s.engage_p_min, s.engage_p_max)
	var ra := g.rng.randf() * 100.0
	var rd := g.rng.randf() * 100.0
	var a_ok := ra < pa
	var d_ok := rd < pd
	var win := "loose"
	if a_ok and not d_ok: win = "ball"
	elif d_ok and not a_ok: win = "challenge"
	elif a_ok and d_ok: win = "ball" if pa - ra >= pd - rd else "challenge"
	var risk_a := 0.0 if ca.is_empty() else Data.num(ca["risk"], 0.0) / 100.0
	var risk_d := 0.0 if cd.is_empty() else Data.num(cd["risk"], 0.0) / 100.0
	var a_move := EngageCard.effect_str(ca, "move", "takeon" if e.move == "takeon" else "keep")
	var d_move := EngageCard.effect_str(cd, "move", e.move if e.move != "takeon" else "stand")
	if win == "challenge" and (d_move == "foul" or g.rng.randf() < risk_d * s.engage_risk_win_share): win = "foul"
	e.outcome = win
	e.note = "%s %.0f%% vs %s %.0f%%" % [a_move, pa, d_move, pd]
	match win:
		"ball": _ball_wins(e, c, d, ca, a_move, g.rng.randf() < risk_d)
		"challenge":
			if e.helper != null and not g.engage.double.deep and e.helper.pos.distance_to(c.pos) < s.engage_stand_reach + 1.0:
				g.poss.start_tackle(e.helper, c, true, true)                          # upfield: the helper takes it from behind
			else: _challenge_wins(e, c, d, cd, a_move, d_move, g.rng.randf() < risk_a)
		"foul": _foul(c, d)
		_: _loose(c, d)

# ---------------------------------------------------------------- outcomes
## the carrier beats him: a move = the take-on with the defender bitten (out for takeon_recover x strand); keeping it / a shield = his tackle bounces off
func _ball_wins(e: Engagement, c: Footballer, d: Footballer, ca: Dictionary, a_move: String, d_down: bool) -> void:
	var s := g.settings
	var strand := EngageCard.effect_num(ca, "strand", 1.0) * (s.engage_down_strand if d_down else 1.0)
	if a_move in ["takeon", "feint", "skill", "flick", "burst"]:
		var clip := EngageCard.clip(c, ca)
		if clip == "" and a_move in ["skill", "flick"]: clip = _pick(c, s.clips_takeon_skill)
		if g.dribble.take_on(c, d, 1, clip, strand, EngageCard.effect_num(ca, "burst", 1.0)): return
	if a_move == "shield": c.shield = s.engage_shield_time
	var dm := EngageCard.effect_str(e.card_of(d.team), "move", e.move if e.move != "takeon" else "stand")
	if dm == "slide": g.dribble.slide_tackle(d, c, 0)
	else: g.poss.start_tackle(d, c, false, true)
	if d_down: d.no_touch = maxf(d.no_touch, s.takeon_recover * strand)

## the defender wins it: against a move he reads it and tackles (take-on with a forced read), else his own move lands
func _challenge_wins(_e: Engagement, c: Footballer, d: Footballer, _cd: Dictionary, a_move: String, d_move: String, c_down: bool) -> void:
	var s := g.settings
	var dist := c.pos.distance_to(d.pos)
	if d_move == "slide" or dist > s.engage_stand_reach + 1.5:
		g.dribble.slide_tackle(d, c, 1)
	elif d_move == "poke":
		_poke(d, c)
	elif a_move in ["takeon", "feint", "skill", "flick", "burst"] and dist <= s.takeon_read_reach + 1.0:
		var clip := EngageCard.clip(c, _e.card_of(c.team))
		if not g.dribble.take_on(c, d, 0, clip): g.poss.start_tackle(d, c, true, true)
	else:
		g.poss.start_tackle(d, c, true, true)
	if c_down or d_move == "charge": c.ai["engage_fall"] = true

## a poke: the ball is knocked loose to the side, nobody has it
func _poke(d: Footballer, c: Footballer) -> void:
	var s := g.settings
	var clip := _pick(d, s.clips_tackle)
	d.vel = (c.pos - d.pos).normalized() * 4.0
	d.face = (c.pos - d.pos).normalized()
	g.motion.act(d, clip, g.motion.strike_frac(clip, 0.45), func(): _knock_loose(c, d, s.engage_poke_speed), 1.0, s.tackle_clip_time, true)

## both failed: the ball squirts loose between them
func _loose(c: Footballer, d: Footballer) -> void:
	var s := g.settings
	_knock_loose(c, d, s.engage_loose_speed)
	g.kicking.tumble(c, s.clips_stumble_light)
	g.kicking.tumble(d, s.clips_stumble_light)

func _knock_loose(c: Footballer, d: Footballer, speed: float) -> void:
	if g.carrier != c: return
	var away := (c.pos - d.pos).normalized()
	var side := Vector2(-away.y, away.x) * (1.0 if g.rng.randf() < 0.5 else -1.0)
	var dir := (side + away * 0.4).normalized()
	g.carrier = null
	g.offside.touched(d)
	g.last_touch = d
	c.no_touch = maxf(c.no_touch, 0.5)
	d.no_touch = maxf(d.no_touch, 0.25)
	g.ball.launch(g.ball.phys.pos, Vector3(dir.x, 0.0, dir.y), speed)
	g.ball.set_free()

## a foul: the carrier goes down and keeps the ball (free kicks are not in yet), the defender is out for a moment
func _foul(c: Footballer, d: Footballer) -> void:
	var s := g.settings
	g.kicking.tumble(c, s.clips_fall)
	c.shield = maxf(c.shield, s.engage_foul_shield)
	d.no_touch = maxf(d.no_touch, s.engage_foul_out)
	g.kicking.tumble(d, s.clips_stumble_medium)
	g.hud.message("FOUL", 1.2)

func _pick(f: Footballer, list: PackedStringArray) -> String:
	var ok := PackedStringArray()
	for n in list:
		if f.node.has_clip(n): ok.append(n)
	return "" if ok.is_empty() else ok[g.rng.randi() % ok.size()]
