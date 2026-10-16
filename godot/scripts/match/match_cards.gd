class_name MatchCards
extends RefCounted
## The hands of 8 skill cards (data/cards.csv), one per team: deals them, runs the cooldowns, answers what can be played in an engagement
## (EngagementDirector), and outside engagements still plays SHOT / PASS cards with the selected player (the old slice: success % decides a
## clean strike or a miscue). Duel cards (DRIBBLE / DEFEND with engage "duel") are only played in a duel. Cooldown seconds = cd x settings.cooldown_scale.

var g: MatchGame
var hands := {}                 ## Team -> Array of card rows (both sides hold a hand: the away AI plays its cards in engagements)
var cooldowns := {}             ## Team -> {card id: seconds left}
var hand: Array = []            ## the home hand (what the HUD shows)
var cooldown := {}              ## the home cooldowns

func _init(game: MatchGame) -> void:
	g = game

func deal() -> void:
	for t in g.teams:
		hands[t] = _deal_one(g.settings.home_hand if t == g.home else g.settings.away_hand)
		cooldowns[t] = {}
	hand = hands[g.home]
	cooldown = cooldowns[g.home]

## the chosen cards first (MatchSettings home_hand / away_hand), then 2 each of SHOT / PASS / DRIBBLE / DEFEND at random for the slots left;
## with engagements on, the random DRIBBLE and DEFEND ones are duel cards (decks come later)
func _deal_one(chosen: PackedStringArray) -> Array:
	var out: Array = []
	var cards := Data.table("cards")
	var cats := ["SHOT", "SHOT", "PASS", "PASS", "DRIBBLE", "DRIBBLE", "DEFEND", "DEFEND"]
	for id in chosen:
		var row := Data.row("cards", id.strip_edges().to_upper())
		if row.is_empty():
			push_warning("Hand: no card %s in cards.csv" % id)
			continue
		if out.size() >= 8 or out.has(row): continue
		out.append(row)
		var cat := String(row["cat"])
		if cat in cats: cats.erase(cat)
		else: cats.pop_back()
	for cat in cats:
		var duel: bool = g.settings.engage_on and cat in ["DRIBBLE", "DEFEND"]
		var pool := cards.filter(func(c): return c["cat"] == cat and not out.has(c) and (not duel or "duel" in String(c.get("engage", "")).split(" ", false)))
		if pool.is_empty(): continue
		out.append(pool[g.rng.randi() % pool.size()])
	return out

func tick(dt: float) -> void:
	for t in cooldowns:
		var cd: Dictionary = cooldowns[t]
		for id in cd.keys():
			cd[id] = maxf(0.0, float(cd[id]) - dt)

func hand_of(team: Team) -> Array:
	return hands.get(team, [])

## off cooldown
func ready(team: Team, c: Dictionary) -> bool:
	return float(cooldowns.get(team, {}).get(String(c["id"]), 0.0)) <= 0.0

## off cooldown and fits this engagement (type, side, the player's role)
func can_play(team: Team, c: Dictionary, e: Engagement) -> bool:
	return ready(team, c) and EngageCard.fits(c, e.type, e.side_of(team), e.player_of(team))

func playable(team: Team, e: Engagement) -> Array:
	return hand_of(team).filter(func(c): return can_play(team, c, e))

func start_cooldown(team: Team, c: Dictionary) -> void:
	if not cooldowns.has(team): cooldowns[team] = {}
	cooldowns[team][String(c["id"])] = Data.num(c["cd"], 3.0) * g.settings.cooldown_scale

func play(i: int) -> void:
	if g.engage.waiting_for(g.home):                                            # in an engagement the hand is the pick
		g.engage.pick_index(g.home, i)
		return
	if i >= hand.size() or g.phase != MatchGame.Phase.PLAY: return
	var f := g.selected
	var c: Dictionary = hand[i]
	if g.settings.engage_on and String(c.get("engage", "")) != "" and String(c["cat"]) in ["DRIBBLE", "DEFEND"]:
		g.hud.toast("%s: played in a duel" % c["name"])
		return
	if f == null:
		g.hud.toast("Pick a player first")
		return
	var id := String(c["id"])
	if float(cooldown.get(id, 0.0)) > 0.0:
		g.hud.toast("%s: cooling down" % c["name"])
		return
	var cat := String(c["cat"])
	if cat in ["SHOT", "PASS", "DRIBBLE"] and g.carrier != f:
		g.hud.toast("%s needs the ball" % c["name"])
		return
	var ok := false
	if cat == "SHOT": ok = _shot(f, c)
	elif cat == "PASS": ok = _pass(f, c)
	elif cat == "DRIBBLE": ok = _dribble(f, c)
	elif cat == "DEFEND": ok = _defend(f, c)
	else:
		g.hud.toast("%s is not in this build" % c["name"])
		return
	if ok:
		cooldown[id] = Data.num(c["cd"], 3.0) * g.settings.cooldown_scale
		g.hud.card_used(i)
		g.command.show("card", String(c["name"]).to_upper(), f, null, String(c["cat"]), g.settings.command_hold)

func _clip(f: Footballer, c: Dictionary, fallback: String) -> String:
	var s := ""
	for ch in String(c["name"]).to_lower():
		s += ch if (ch >= "a" and ch <= "z") or (ch >= "0" and ch <= "9") else "_"
	var clip_name := "%s_%s" % [String(c["id"]).to_lower(), s]
	return clip_name if f.node.has_clip(clip_name) else fallback

func _roll(c: Dictionary, bonus: float) -> bool:
	return g.rng.randf() * 100.0 < Data.num(c["succ"], 70.0) + bonus

func _shot(f: Footballer, c: Dictionary) -> bool:
	var curve := Data.num(c["ball_curve"])
	var style := "K01"
	if curve > 0.0: style = "K02"
	elif curve < 0.0: style = "K03"
	elif Data.num(c["ball_arc"]) >= 2.0: style = "K06"
	if String(c["name"]).findn("knuckle") >= 0: style = "K04"
	var good := _roll(c, (f.stat("SHO", 60) - 60) * g.settings.stat_roll_k)
	var spd := g.settings.shot_base_speed + Data.num(c["ball_speed"], 5.0) * g.settings.shot_speed_per_point
	var noise := g.settings.shot_good_noise if good else g.settings.shot_bad_noise + Data.num(c["risk"], 10.0) * g.settings.shot_risk_noise
	if not good: spd *= g.settings.shot_miss_speed
	var to := Vector2(MatchGame.HALF_L * f.team.dir + f.team.dir * 1.5, 0.0)
	g.hud.toast(String(c["name"]) if good else "%s: miscued" % c["name"])
	g.motion.act(f, _clip(f, c, "kick"), 0.4, func(): g.poss.launch(f, "shot", to, Vector2.ZERO, {"style": style, "speed": spd, "noise": noise}))
	return true

func _pass(f: Footballer, c: Dictionary) -> bool:
	var tgt := _best_mate(f)
	var to := f.pos + f.face * 18.0 if tgt == null else tgt.pos + tgt.vel * 0.5
	var dist := f.pos.distance_to(to)
	var arc := Data.num(c["ball_arc"])
	var style := "K07"
	var spd := clampf(dist * g.settings.pass_speed_per_m + g.settings.pass_speed_base, g.settings.pass_speed_min, g.settings.pass_speed_max) * (1.0 + Data.num(c["ball_speed"], 4.0) * 0.03)
	if arc >= 2.0:
		style = "K05"
		spd = clampf(sqrt(dist * 10.3), 8.0, 30.0)
	elif String(c["name"]).findn("cross") >= 0:
		style = "K08"
	var good := _roll(c, (f.stat("PAS", 60) - 60) * g.settings.stat_roll_k)
	g.hud.toast(String(c["name"]) if good else "%s: scuffed" % c["name"])
	var over := {"style": style, "speed": spd, "noise": 1.0 if good else 10.0}
	g.motion.act(f, _clip(f, c, "kick"), 0.4, func(): g.poss.launch(f, "lob" if style == "K05" else "pass", to, Vector2.ZERO, over, tgt))
	return true

func _best_mate(f: Footballer) -> Footballer:
	var ctx: AiContext = g.brain.ctx[f.team]
	var best: Footballer = null
	var bs := -1e9
	for o in ctx.pass_options(f):
		var sc: float = o["forward"] * 0.3 + minf(o["open"], 10.0) - (25.0 if o["blocked"] else 0.0)
		if sc > bs:
			bs = sc
			best = o["mate"]
	return best

func _dribble(f: Footballer, c: Dictionary) -> bool:
	var good := _roll(c, (f.stat("DRI", 60) - 60) * g.settings.stat_roll_k)
	var clip_name := _clip(f, c, "")
	var dir := f.face
	if clip_name != "": g.motion.act(f, clip_name, 0.5, func(): pass)
	f.shield = g.settings.dribble_shield
	f.vel = dir * g.settings.dribble_burst
	if good:
		g.hud.toast(String(c["name"]))
	else:
		g.hud.toast("%s: lost it" % c["name"])
		g.carrier = null
		f.no_touch = 0.7
		g.ball.launch(g.ball.phys.pos, Vector3(dir.x, 0.0, dir.y), 4.0)
		g.ball.set_free()
	return true

func _defend(f: Footballer, c: Dictionary) -> bool:
	var target := g.carrier
	if target == null or target.team == f.team:
		g.hud.toast("%s: nobody to challenge" % c["name"])
		return false
	if f.pos.distance_to(target.pos) > g.settings.tackle_card_reach + Data.num(c["reach"], 4.0) * g.settings.tackle_reach_per_point:
		g.hud.toast("%s: too far" % c["name"])
		return false
	var good := _roll(c, (f.stat("DEF", 60) - target.stat("DRI", 60)) * g.settings.stat_roll_k)
	f.vel = (target.pos - f.pos).normalized() * g.settings.tackle_dash
	g.hud.toast(String(c["name"]) if good else "%s: missed" % c["name"])
	g.motion.act(f, _clip(f, c, "df01_stand_tackle"), 0.45, func(): g.poss.resolve_tackle(f, target, 1.0 if good else -1.0))
	return true
