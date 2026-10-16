class_name MatchOrders
extends RefCounted
## The human's orders to his players (from MatchControls and the HUD buttons). A run / press is stored on the footballer (`order`) and followed here until it is done.

var g: MatchGame
const GHOST := preload("res://scenes/engagement/zap_ghost.tscn")
var stat_curved := 0
var stat_straight := 0

func _init(game: MatchGame) -> void:
	g = game

## the order buttons that make sense for a player now
func menu_for(f: Footballer) -> Array:
	if f.is_keeper() and g.carrier != f: return ["rush"]
	if g.carrier == f: return ["pass", "through", "lob", "shoot", "run"]
	return ["run", "press", "tackle"]

## a run: he goes there by himself (the carrier dribbles there), then the AI takes over again
func run(f: Footballer, spot: Vector2) -> void:
	_run_order(f, spot)
	g.command.show("run", "RUN", f, null, "", g.settings.command_hold)

## a run order without the HUD command text (the AI uses it: one-twos, runners)
func send_run(f: Footballer, spot: Vector2, delay := 0.0) -> void:
	_run_order(f, spot, delay)

func _run_order(f: Footballer, spot: Vector2, delay := 0.0) -> void:
	spot.x = clampf(spot.x, -MatchGame.HALF_L + 1.0, MatchGame.HALF_L - 1.0)
	spot.y = clampf(spot.y, -MatchGame.HALF_W + 1.0, MatchGame.HALF_W - 1.0)
	f.order = {"kind": "run", "target": spot, "t": g.settings.run_order_time + delay, "delay": delay}

## chase the ball (or its carrier) for a few seconds
func press(f: Footballer) -> void:
	f.order = {"kind": "press", "t": g.settings.press_order_time}
	g.command.show("press", "PRESS", f, null, "", g.settings.command_hold)

## the keeper comes out to close the carrier down (a one on one); the AI does it by itself when nobody is back, this forces it
func keeper_rush(f: Footballer) -> void:
	if g.carrier == null or g.carrier.team == f.team:
		g.hud.toast("Nobody to rush out at")
		return
	f.order = {"kind": "rush", "t": g.settings.keeper_rush_order_time}
	g.command.show("rush", "KEEPER OUT", f, g.carrier, "", g.settings.command_hold)

func tackle(f: Footballer) -> void:
	if g.carrier == null or g.carrier.team == f.team:
		g.hud.toast("Nobody to tackle")
		return
	if f.pos.distance_to(g.carrier.pos) > 3.0:
		f.order = {"kind": "press", "t": g.settings.tackle_order_time}
		g.command.show("tackle", "CLOSING DOWN", f, null, "too far to tackle", g.settings.command_hold)
		return
	g.command.show("tackle", "TACKLE", f, g.carrier, "", g.settings.command_hold)
	g.poss.try_tackle(f)

## shoot at a spot of the grass (the drag from the ball carrier)
func shoot_at(f: Footballer, spot: Vector2) -> void:
	if g.carrier != f: return
	var over := {}
	if g.rng.randf() < g.settings.through_curve_chance: over["style"] = "K02"
	g.command.show("shoot", "SHOOT", f, null, "", g.settings.command_hold)
	g.poss.kick_action(f, "shot", spot, Vector2.ZERO, over)

## kind = "pass" / "through" / "lob". To a team mate (the ball leads him; a through ball also sends him running) or to a spot.
## `point`: where the human pointed (pitch metres); for a through ball the run goes that way from the mate (MatchSettings > Through-ball runs).
func pass_to(f: Footballer, kind: String, mate: Footballer, spot: Vector2, send_run := false, point := Vector2.INF) -> void:
	if g.carrier != f:
		g.hud.toast("%s has not got the ball" % f.display_name())
		return
	var action := kind if kind in ["pass", "through", "lob"] else "pass"
	if mate != null:
		var vel := Vector2.ZERO
		var plan := {}
		if action == "through" or send_run:
			var dir := Vector2(f.team.dir, 0.0)
			if point != Vector2.INF and point.distance_to(mate.pos) >= g.settings.through_point_min: dir = (point - mate.pos).normalized()
			vel = dir * g.settings.through_run_speed
			plan = plan_run(mate, dir, f)
			g.kicking.after_release(f, func(): send_runner(f, mate, vel, plan))  # he sets off when the ball is struck, not while the passer is still turning and winding up
		g.command.show(action, "LOB OVER THE TOP" if (action == "lob" and send_run) else action.to_upper(), f, mate, ("%s curls his run" if plan.has("curve") else "%s runs onto it") % mate.display_name() if send_run or action == "through" else "", g.settings.command_hold)
		if plan.has("curve"): g.poss.kick_action(f, action, plan["meet"], Vector2.ZERO, {"_to_space": true, "speed": plan["speed"]}, mate)       # into the space on his curved run, through a clear lane
		else: g.poss.kick_action(f, action, mate.pos, mate.vel if vel == Vector2.ZERO else vel, {}, mate)
	elif spot != Vector2.INF:
		g.command.show(action, action.to_upper() + " (SPACE)", f, null, "", g.settings.command_hold)
		g.poss.kick_action(f, action, spot)

## the runner of a through ball sets off (after a short reaction) towards where the ball will be; with a plan that has a curve he bends round the defenders
func send_runner(passer: Footballer, mate: Footballer, vel: Vector2, plan := {}) -> void:
	if mate.team != passer.team: return
	if plan.has("curve"):
		_run_order(mate, plan["end"], g.settings.through_react)
		var c: Array = plan["curve"]
		mate.order["curve"] = [mate.pos, c[1], c[2]]                              # starts from where he is now
		mate.order["ct"] = 0.0
		mate.order["meet_t"] = float(plan.get("meet_t", 1.0))
		mate.order["ghost_t"] = 0.0
		stat_curved += 1
		return
	stat_straight += 1
	_run_order(mate, mate.pos + vel * g.settings.through_lead, g.settings.through_react)

## the run of a through ball in direction `dir`: {end} straight, or {end, meet, curve: [start, control, end]} when he is clever enough
## (game sense >= curve_sense_min) and a defender sits on the straight line while a curve round one side is clearer. `meet` is where the
## ball is played: a point late on the curve with the passing lane from `passer` clear too.
func plan_run(mate: Footballer, dir: Vector2, passer: Footballer = null) -> Dictionary:
	var s := g.settings
	var start := mate.pos
	var end := start + dir * s.through_run_speed * s.through_lead
	end.x = clampf(end.x, -MatchGame.HALF_L + 1.0, MatchGame.HALF_L - 1.0)
	end.y = clampf(end.y, -MatchGame.HALF_W + 1.0, MatchGame.HALF_W - 1.0)
	var out := {"end": end}
	var sense := (mate.stat("PAS", 60) + mate.stat("DRI", 60)) * 0.5
	if sense < s.curve_sense_min: return out
	var other := g.away if mate.team == g.home else g.home
	var from := passer.pos if passer != null else start
	var straight := minf(_clearance(other, start, (start + end) * 0.5, end), _lane(other, from, start.lerp(end, 0.8)))
	if straight >= s.curve_block: return out
	var perp := Vector2(-dir.y, dir.x)
	var bend := lerpf(s.curve_bend_min, s.curve_bend_max, clampf((sense - s.curve_sense_min) / maxf(99.0 - s.curve_sense_min, 1.0), 0.0, 1.0))
	var best := straight + s.curve_gain
	for side in [1.0, -1.0]:
		var ctrl: Vector2 = (start + end) * 0.5 + perp * side * bend * 2.0          # the curve passes about `bend` m off the line at its middle
		if absf(ctrl.y) > MatchGame.HALF_W + 4.0: continue
		var run_cl := _clearance(other, start, ctrl, end)
		for t in [0.65, 0.8, 1.0]:
			var meet := bezier(start, ctrl, end, t)
			var cl := minf(run_cl, _lane(other, from, meet))
			if cl > best:
				best = cl
				out["curve"] = [start, ctrl, end]
				out["meet"] = meet
				out["meet_t"] = t
	if out.has("curve") and passer != null: out["speed"] = _through_speed(mate, passer, out)
	return out

## the pace of a through ball onto a curved run: the ball reaches `meet` when he does (his reaction, the run up to speed, the curve's length)
func _through_speed(mate: Footballer, passer: Footballer, plan: Dictionary) -> float:
	var s := g.settings
	var c: Array = plan["curve"]
	var length := 0.0
	var prev: Vector2 = c[0]
	for k in range(1, 21):
		var q := bezier(c[0], c[1], c[2], float(plan["meet_t"]) * k / 20.0)
		length += prev.distance_to(q)
		prev = q
	var v := mate.top_speed() * s.sprint_factor * (1.0 + s.curve_run_boost)
	var t := s.through_react + length / v + v / maxf(s.accel, 0.1) * 0.5        # reaction + distance + the time lost getting up to speed
	var style := String(Data.row("ball_actions", "through").get("style", "K07"))
	var from := Vector3(passer.pos.x, g.ball.phys.pos.y, passer.pos.y)
	return g.ball.speed_for_time(from, plan["meet"], style, t)

## the closest any opponent (not the keeper) comes to the curve start-ctrl-end (a straight line when ctrl is the middle)
func _clearance(team: Team, a: Vector2, ctrl: Vector2, b: Vector2) -> float:
	var best := 1e9
	for k in range(2, 11):
		var p := bezier(a, ctrl, b, k / 10.0)
		for o in team.players:
			if o.is_keeper(): continue
			best = minf(best, o.pos.distance_to(p))
	return best

## the closest any opponent (not the keeper) comes to the passing lane a -> b
func _lane(team: Team, a: Vector2, b: Vector2) -> float:
	var best := 1e9
	for o in team.players:
		if o.is_keeper(): continue
		best = minf(best, o.pos.distance_to(Geometry2D.get_closest_point_to_segment(o.pos, a, b)))
	return best

static func bezier(a: Vector2, c: Vector2, b: Vector2, t: float) -> Vector2:
	var u := 1.0 - t
	return a * u * u + c * 2.0 * u * t + b * t * t

## called by the AI brain for a player with an order
func follow(f: Footballer, dt: float) -> void:
	var o := f.order
	o["t"] = float(o.get("t", 5.0)) - dt
	if o["t"] <= 0.0:
		f.order = {}
		return
	var s := g.settings
	var kind := String(o["kind"])
	if float(o.get("delay", 0.0)) > 0.0:                                 # reacting to the ball being played
		o["delay"] = float(o["delay"]) - dt
		return
	if kind == "run" and o.has("curve"):                                  # a smart run: follow the curve, a little faster, faint afterimages
		if g.carrier == f:                                                  # he has it: the curve is done, his own play takes over
			f.order = {}
			return
		var c: Array = o["curve"]
		var ct := float(o["ct"])
		while ct < 1.0 and f.pos.distance_to(bezier(c[0], c[1], c[2], ct)) < 2.0: ct += 0.02
		o["ct"] = ct
		var aim := bezier(c[0], c[1], c[2], minf(1.0, ct + 0.08))
		var ball := Vector2(g.ball.phys.pos.x, g.ball.phys.pos.z)
		var bvel := Vector2(g.ball.phys.vel.x, g.ball.phys.vel.z)
		if g.carrier == null and (ct >= float(o.get("meet_t", 1.0)) - 0.1 or f.pos.distance_to(ball) < s.curve_chase_dist):
			aim = ball + bvel * s.curve_chase_lead                               # the ball is here: go and get it
		var to_c: Vector2 = aim - f.pos
		if ct >= 1.0 and f.pos.distance_to(c[2]) < s.arrive_distance and f.pos.distance_to(ball) > s.curve_chase_dist:
			f.order = {}
			return
		f.want = to_c.normalized() * f.top_speed() * s.sprint_factor * (1.0 + s.curve_run_boost)
		if s.curve_ghost_every > 0.0:
			o["ghost_t"] = float(o["ghost_t"]) - dt
			if o["ghost_t"] <= 0.0:
				o["ghost_t"] = s.curve_ghost_every
				_ghost(f)
		return
	if kind == "run":
		var to: Vector2 = o["target"] - f.pos
		if to.length() < g.settings.arrive_distance:
			f.order = {}
			return
		f.want = to.normalized() * f.top_speed() * (s.carry_factor if g.carrier == f else s.sprint_factor)
	elif kind == "press":
		if g.carrier != null and g.carrier.team == f.team and g.carrier != f:
			f.order = {}
			return
		var tgt := g.carrier.pos if g.carrier != null and g.carrier != f else Vector2(g.ball.phys.pos.x, g.ball.phys.pos.z)
		var to2 := tgt - f.pos
		f.want = to2.limit_length(f.top_speed() * s.sprint_factor) if to2.length() > 0.8 else Vector2.ZERO

## a very faint afterimage of him (the zap ghost scene, its "soft" animation)
func _ghost(f: Footballer) -> void:
	var gh: ZapGhost = GHOST.instantiate()
	g.stadium.add_actor(gh, g.stadium.pitch_pos(Vector3(f.pos.x, 0.0, f.pos.y)))
	gh.copy_from(f.node)
	gh.tree_exiting.connect(func(): g.stadium.remove_actor(gh))
	gh.start("soft")
