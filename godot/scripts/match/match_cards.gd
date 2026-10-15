class_name MatchCards
extends RefCounted
## The hand of 8 skill cards (data/cards.csv): deals it, plays a card with the selected player, runs the cooldowns. Only SHOT, PASS, DRIBBLE and DEFEND cards do
## anything yet; success % decides a clean strike or a miscue. Cooldown seconds = cd x settings.cooldown_scale.

var g: MatchGame
var hand: Array = []
var cooldown := {}

func _init(game: MatchGame) -> void:
	g = game

func deal() -> void:
	hand.clear()
	var cards := Data.table("cards")
	for cat in ["SHOT", "SHOT", "PASS", "PASS", "DRIBBLE", "DRIBBLE", "DEFEND", "DEFEND"]:
		var pool := cards.filter(func(c): return c["cat"] == cat and not hand.has(c))
		if pool.is_empty(): continue
		hand.append(pool[g.rng.randi() % pool.size()])

func tick(dt: float) -> void:
	for id in cooldown.keys():
		cooldown[id] = maxf(0.0, float(cooldown[id]) - dt)

func play(i: int) -> void:
	if i >= hand.size() or g.phase != MatchGame.Phase.PLAY: return
	var f := g.selected
	if f == null:
		g.hud.toast("Pick a player first")
		return
	var c: Dictionary = hand[i]
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
	var good := _roll(c, (f.stat("SHO", 60) - 60) * 0.3)
	var spd := 14.0 + Data.num(c["ball_speed"], 5.0) * 2.6
	var noise := 1.5 if good else 8.0 + Data.num(c["risk"], 10.0) * 0.6
	if not good: spd *= 0.75
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
	var spd := clampf(dist * 0.85 + 6.0, 9.0, 26.0) * (1.0 + Data.num(c["ball_speed"], 4.0) * 0.03)
	if arc >= 2.0:
		style = "K05"
		spd = clampf(sqrt(dist * 10.3), 8.0, 30.0)
	elif String(c["name"]).findn("cross") >= 0:
		style = "K08"
	var good := _roll(c, (f.stat("PAS", 60) - 60) * 0.3)
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
	var good := _roll(c, (f.stat("DRI", 60) - 60) * 0.3)
	var clip_name := _clip(f, c, "")
	var dir := f.face
	if clip_name != "": g.motion.act(f, clip_name, 0.5, func(): pass)
	f.shield = 1.3
	f.vel = dir * 7.0
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
	if f.pos.distance_to(target.pos) > 3.0 + Data.num(c["reach"], 4.0) * 0.25:
		g.hud.toast("%s: too far" % c["name"])
		return false
	var good := _roll(c, (f.stat("DEF", 60) - target.stat("DRI", 60)) * 0.3)
	f.vel = (target.pos - f.pos).normalized() * 6.5
	g.hud.toast(String(c["name"]) if good else "%s: missed" % c["name"])
	g.motion.act(f, _clip(f, c, "df01_stand_tackle"), 0.45, func(): g.poss.resolve_tackle(f, target, 1.0 if good else -1.0))
	return true
