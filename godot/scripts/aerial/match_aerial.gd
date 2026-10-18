class_name MatchAerial
extends RefCounted
## Balls in the air. When a lob is kicked this predicts where it comes down (the yellow ring on the grass), sends the nearest player of each team to wait under it
## (AiContest does the walking), and when the ball is about to arrive and both are there, plays the duel: each picks an approach (header, shove-and-chest, shoulder leap),
## the better score wins, plays the clip timed so its strike frame meets the ball, and the loser jumps / stumbles. Alone under it, a player just waits and takes it.
## All numbers: MatchSettings > Aerial duels.

var g: MatchGame
var ev := {}                    ## the contest in progress: land, contest (Vector2), t_land, t_c (head height), parts {Team: Footballer}, resolved, ...
var marker: LandingMarker
var _t := 0.0
var _next_refresh := 0.0
var stat_events := 0            ## headless counters
var stat_duels := 0
var stat_push := 0
var stat_leap := 0
var stat_headers := 0
var stat_alone := 0

func _init(game: MatchGame) -> void:
	g = game
	marker = LandingMarker.new()
	g.stadium.add_actor(marker, Vector2(50, 50))

func active() -> bool:
	return not ev.is_empty()

## the contest spot for f when he is one of the two sent to it (else Vector2.INF)
func spot_for(f: Footballer) -> Vector2:
	if ev.is_empty() or ev.get("closed", false): return Vector2.INF
	for t in ev["parts"]:
		if ev["parts"][t] == f: return ev["contest"]
	return Vector2.INF

func update(dt: float) -> void:
	_t += dt
	var s := g.settings
	if g.phase != MatchGame.Phase.PLAY or g.ball == null:
		_end()
		return
	var b := g.ball
	if ev.is_empty():
		if g.carrier == null and b.live and b.action in s.aerial_actions and b.phys.pos.y > 0.3: _start()
		return
	if g.carrier != null or b.action != ev["action"] or (b.phys.pos.y < 0.5 and _t > float(ev["t_c"])):
		_end()
		return
	if _t >= _next_refresh:
		_next_refresh = _t + 0.2
		_refresh()
	var left := float(ev["t_land"]) - _t
	marker.show_at(clampf(left / maxf(float(ev["total"]), 0.1), 0.0, 1.0))
	g.stadium.set_actor_pos(marker, g.stadium.pitch_pos(Vector3(ev["land"].x, 0.0, ev["land"].y)))
	if not ev.get("resolved", false) and float(ev["t_c"]) - _t <= s.aerial_trigger: _resolve()
	_steer(dt)

# ---------------------------------------------------------------- prediction
## a copy of the ball's physics, stepped ahead: where and when it comes down to head height and to the grass
func predict() -> Dictionary:
	var s := g.settings
	var src := g.ball.phys
	var p := BallPhysics.new()
	for k in ["g", "rad", "drag", "mag", "knu", "knu_v", "crisis", "crisis_v", "e", "mu", "roll", "sdec", "spin_drag", "power", "touch", "mass", "pos", "vel", "spin", "t", "seed_value"]:
		p.set(k, src.get(k))
	var apex := p.pos.y
	var out := {"apex": apex, "t_c": -1.0, "contest": Vector2(p.pos.x, p.pos.z), "t_land": 0.0, "land": Vector2(p.pos.x, p.pos.z)}
	var t := 0.0
	var dt := 1.0 / 30.0
	while t < 8.0:
		p.step(dt)
		t += dt
		apex = maxf(apex, p.pos.y)
		if p.vel.y < 0.0 and p.pos.y <= s.head_height and out["t_c"] < 0.0:
			out["t_c"] = t
			out["contest"] = Vector2(p.pos.x, p.pos.z)
		if p.vel.y < 0.0 and p.pos.y <= p.rad + 0.05:
			out["t_land"] = t
			out["land"] = Vector2(p.pos.x, p.pos.z)
			break
	out["apex"] = apex
	if out["t_c"] < 0.0:
		out["t_c"] = out["t_land"]
		out["contest"] = out["land"]
	return out

func _start() -> void:
	var s := g.settings
	var pr := predict()
	if pr["apex"] < s.aerial_min_apex or pr["t_land"] <= 0.2: return
	ev = {"action": g.ball.action, "land": pr["land"], "contest": pr["contest"], "t_land": _t + float(pr["t_land"]), "t_c": _t + float(pr["t_c"]), "total": float(pr["t_land"]), "parts": {}, "resolved": false}
	stat_events += 1
	_pick()
	_next_refresh = _t + 0.2

func _refresh() -> void:
	var pr := predict()
	ev["land"] = pr["land"]
	ev["contest"] = pr["contest"]
	ev["t_land"] = _t + float(pr["t_land"])
	ev["t_c"] = _t + float(pr["t_c"])
	if not ev.get("resolved", false): _pick()

func _end() -> void:
	if ev.is_empty():
		marker.hide_marker()
		return
	for t in ev["parts"]:
		var f: Footballer = ev["parts"][t]
		if f != null: f.ai.erase("air_wait")
	ev = {}
	marker.hide_marker()

## the player of each team who can get to the spot first (the intended receiver is preferred); he keeps the job while he is still in time
func _pick() -> void:
	var s := g.settings
	var left := maxf(float(ev["t_c"]) - _t, 0.0)
	var c: Vector2 = ev["contest"]
	for t in g.teams:
		var best: Footballer = null
		var bs := 1e9
		for f in t.players:
			if f.is_keeper() or f.lock > 0.0 or g.offside.aware(f): continue
			var d := f.pos.distance_to(c)
			if d > s.aerial_range: continue
			var need := d / maxf(f.top_speed() * s.sprint_factor, 0.1)
			if need > left + s.aerial_slack: continue
			var score := need * (0.7 if f == g.pass_target else 1.0) - (0.3 if ev["parts"].get(t) == f else 0.0)
			if score < bs:
				bs = score
				best = f
		var k := _claimer(t, c, left)
		if k != null: best = k                                                # the keeper comes for it
		if best != null: ev["parts"][t] = best
		else: ev["parts"].erase(t)

## the keeper of t, when the ball comes down in his area and he can get there
func _claimer(t: Team, c: Vector2, left: float) -> Footballer:
	var s := g.settings
	if c.x * t.dir > -MatchGame.HALF_L + s.claim_depth or absf(c.y) > s.claim_width: return null
	for f in t.players:
		if not f.is_keeper() or f.lock > 0.0: continue
		if (f.stat("HAN", 60) + f.stat("POS", 60)) * 0.5 < s.claim_min: return null
		var need := f.pos.distance_to(c) / maxf(f.top_speed() * s.sprint_factor, 0.1)
		if need + s.claim_slack <= left: return f
	return null

# ---------------------------------------------------------------- the contest
func _resolve() -> void:
	ev["resolved"] = true
	var s := g.settings
	var c: Vector2 = ev["contest"]
	var list: Array = []
	for t in ev["parts"]:
		var f: Footballer = ev["parts"][t]
		if f.pos.distance_to(c) <= s.duel_reach and f.lock <= 0.0: list.append(f)
	if list.size() < 2:
		stat_alone += 1                                                       # nobody to challenge: he waits and takes it
		return
	for k in list:
		if k.is_keeper():
			_claim(k, list[1] if list[0] == k else list[0])
			return
	stat_duels += 1
	var pa := _plan(list[0], list[1])
	var pb := _plan(list[1], list[0])
	var win: Dictionary = pa if pa["score"] >= pb["score"] else pb
	var lose: Dictionary = pb if win == pa else pa
	_perform(win, lose)

var stat_claims := 0
var stat_claim_fails := 0

## the keeper against an attacker under a high ball: he claims it (catch, or a punch if it is too quick to hold), or misjudges it and the attacker gets the header
func _claim(k: Footballer, o: Footballer) -> void:
	var s := g.settings
	var heading := 0.5 * o.stat("PHY", 60) + 0.5 * o.stat("SHO", 60)
	var p := clampf(s.claim_base + ((k.stat("HAN", 60) + k.stat("POS", 60)) * 0.5 - heading) * s.claim_k / 100.0, 0.15, 0.95)
	var left := maxf(float(ev["t_c"]) - _t, 0.05)
	var clip: String = s.clips_claim[0] if not s.clips_claim.is_empty() else ""
	var frac := g.motion.strike_frac(clip, 0.45)
	var dur := clampf(left / frac, s.aerial_clip_min, s.aerial_clip_max)
	if g.rng.randf() < p:
		stat_claims += 1
		ev["acting"] = [k, o]
		g.motion.act(k, clip, frac, func(): _claimed(k), 0.0, dur)
		g.motion.act(o, s.clip_challenge, g.motion.strike_frac(s.clip_challenge, 0.45), func(): pass, 0.0, dur)
		return
	stat_claim_fails += 1                                                     # he comes and misses it: the attacker heads it
	var win := _plan(o, k)
	var lose := _plan(k, o)
	ev["acting"] = [o, k]
	g.motion.act(k, clip, frac, func(): pass, 0.0, dur)
	var oclip := String(win["head"]["clip"])
	g.motion.act(o, oclip, g.motion.strike_frac(oclip, 0.45), func(): _won(win, lose), 0.0, dur)

func _claimed(k: Footballer) -> void:
	if g.carrier != null: return
	var bp := g.ball.phys.pos
	if k.pos.distance_to(Vector2(bp.x, bp.z)) > g.settings.claim_reach or bp.y > g.settings.keeper_reach_height + 0.4: return
	var s := g.settings
	if g.ball.phys.vel.length() <= s.save_speed_base + k.stat("HAN", 60) * s.save_speed_per_han:
		g.poss.take(k)
	else:                                                                      # too hot to hold: punched clear
		var away := Vector2(k.team.dir, g.rng.randf_range(-0.8, 0.8)).normalized()
		g.offside.touched(k)
		g.last_touch = k
		g.ball.set_free()
		g.ball.phys.vel = Vector3(away.x * 14.0, 6.0, away.y * 14.0)
		k.no_touch = 0.4

## how one player goes for it: approach, header kind and a score
func _plan(p: Footballer, o: Footballer) -> Dictionary:
	var s := g.settings
	var rng := g.rng
	var defensive := p.role in s.defensive_roles
	var phy := p.stat("PHY", 60)
	var heading := 0.5 * phy + 0.5 * (p.stat("DEF", 60) if defensive else p.stat("SHO", 60))
	var intel := (p.stat("PAS", 60) + p.stat("DRI", 60)) * 0.5
	var approach := "header"
	var bonus := 0.0
	if phy >= s.push_phy and phy - o.stat("PHY", 60) >= s.push_margin and rng.randf() < s.push_chance:
		approach = "push"
		bonus = s.push_bonus
	elif intel >= s.smart_min and p.pos.distance_to(o.pos) <= s.leap_range and rng.randf() < s.leap_chance:
		approach = "leap"
		bonus = s.leap_bonus
	var score := heading + s.jump_share * phy + rng.randf_range(-s.duel_noise, s.duel_noise) + bonus + (s.receiver_bonus if p == g.pass_target else 0.0)
	return {"f": p, "o": o, "approach": approach, "score": score, "head": _head_plan(p)}

func _perform(win: Dictionary, lose: Dictionary) -> void:
	var s := g.settings
	var w: Footballer = win["f"]
	var l: Footballer = lose["f"]
	var left := maxf(float(ev["t_c"]) - _t, 0.05)
	var clip := s.clip_push if win["approach"] == "push" else (s.clip_leap if win["approach"] == "leap" else String(win["head"]["clip"]))
	var frac := g.motion.strike_frac(clip, 0.45)
	var dur := clampf(left / frac, s.aerial_clip_min, s.aerial_clip_max)
	match win["approach"]:
		"push": stat_push += 1
		"leap": stat_leap += 1
	_face(w, l)
	_face(l, w)
	ev["acting"] = [w, l]
	g.motion.act(w, clip, frac, func(): _won(win, lose), 0.0, dur)
	g.motion.act(l, s.clip_challenge, g.motion.strike_frac(s.clip_challenge, 0.45), func(): pass, 0.0, dur)

func _face(a: Footballer, b: Footballer) -> void:
	var d := b.pos - a.pos
	if d.length() > 0.05: a.face = d.normalized()

## the strike frame: the winner meets the ball
func _won(win: Dictionary, lose: Dictionary) -> void:
	var s := g.settings
	var w: Footballer = win["f"]
	var l: Footballer = lose["f"]
	if g.carrier != null: return
	var bp := g.ball.phys.pos
	if w.pos.distance_to(Vector2(bp.x, bp.z)) > s.header_reach or bp.y > s.header_max_h or bp.y < s.header_min_h: return      # he missed it
	if g.offside.touched(w): return                                       # he was offside when it was played
	if win["approach"] == "push":
		g.kicking.tumble(l, s.clips_fall if g.rng.randf() < s.push_fall_chance else s.clips_stumble_medium)
		_chest(w, l)                                                         # chested down: the ball stays free and drops at his feet, no snapping
		return
	stat_headers += 1
	var h: Dictionary = win["head"]
	var plan := g.ball.play_action(h["action"], h["to"], w.row, Vector2.ZERO, {"speed": h["speed"], "noise": s.head_noise})
	if plan.is_empty(): return
	g.last_touch = w
	g.pass_target = h["mate"]
	w.no_touch = g.settings.no_touch_after_kick
	g.offside.played(w, "")                                                   # a headed pass: offside is judged again from here

## the chest takes the pace off: the ball keeps its own physics, loses most of its speed and drops just ahead of him; he is first to it (receiver reach) and the loser is out of it for a moment
func _chest(w: Footballer, l: Footballer) -> void:
	var s := g.settings
	var b := g.ball
	b.set_free()
	var v := b.phys.vel
	var ahead := w.face * s.chest_drop_ahead
	b.phys.vel = Vector3(v.x * s.chest_keep + ahead.x, minf(v.y, 0.0) * 0.2 + s.chest_pop, v.z * s.chest_keep + ahead.y)
	b.phys.spin *= 0.3
	g.pass_target = w
	g.last_touch = w
	l.no_touch = maxf(l.no_touch, s.chest_shield)

## while a duel is being played the two keep adjusting under the ball (the clips are locked in place, so this slides them to where it really comes down)
func _steer(dt: float) -> void:
	var s := g.settings
	var c: Vector2 = ev["contest"]
	for a in ev.get("acting", []):
		var f: Footballer = a
		if f.pending.is_null(): continue
		var to: Vector2 = c - f.pos
		if to.length() > 0.25: f.pos += to.normalized() * minf(to.length(), s.aerial_steer_speed * dt)

## what the winner does with the header: clear (defensive roles, or nobody to find), shoot (close to goal) or pass to the best team mate
func _head_plan(p: Footballer) -> Dictionary:
	var s := g.settings
	var dir := p.team.dir
	var goal := Vector2(MatchGame.HALF_L * dir, 0.0)
	var out := {"kind": "clear", "action": "lob", "speed": s.head_clear_speed, "mate": null, "clip": s.clip_header_clear, "to": Vector2.ZERO}
	if not p.role in s.defensive_roles:
		if p.pos.distance_to(goal) <= s.head_shoot_range:
			out["kind"] = "shoot"
			out["action"] = "shot"
			out["speed"] = s.head_shot_speed
			out["clip"] = s.clip_header_shot
			out["to"] = Vector2(goal.x + dir * 1.5, g.rng.randf_range(-MatchGame.GOAL_HALF + 1.0, MatchGame.GOAL_HALF - 1.0))
			return out
		var mate := _best_mate(p)
		if mate != null:
			out["kind"] = "pass"
			out["action"] = "pass"
			out["speed"] = s.head_pass_speed
			out["clip"] = s.clip_header_pass
			out["mate"] = mate
			out["to"] = mate.pos
			return out
	var opp_y := 0.0
	for o in g.all:
		if o.team != p.team and not o.is_keeper() and o.pos.distance_to(p.pos) < 12.0: opp_y += o.pos.y - p.pos.y
	var side := -signf(opp_y) if absf(opp_y) > 0.5 else (1.0 if g.rng.randf() < 0.5 else -1.0)
	out["to"] = Vector2(clampf(p.pos.x + dir * s.head_clear_length, -MatchGame.HALF_L + 6.0, MatchGame.HALF_L - 6.0), side * (MatchGame.HALF_W - 8.0))
	return out

func _best_mate(p: Footballer) -> Footballer:
	var best: Footballer = null
	var bs := -1e9
	var dir := p.team.dir
	for m in p.team.players:
		if m == p or m.is_keeper(): continue
		var d := m.pos.distance_to(p.pos)
		if d < 6.0 or d > 30.0: continue
		var fwd := (m.pos.x - p.pos.x) * dir
		if fwd < -4.0: continue
		var open := 20.0
		for o in g.all:
			if o.team != p.team and not o.is_keeper(): open = minf(open, o.pos.distance_to(m.pos))
		var score := open * 1.0 + fwd * 0.25 - d * 0.1
		if open < 3.0: continue
		if score > bs:
			bs = score
			best = m
	return best
