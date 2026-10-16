class_name MatchOrders
extends RefCounted
## The human's orders to his players (from MatchControls and the HUD buttons). A run / press is stored on the footballer (`order`) and followed here until it is done.

var g: MatchGame

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
func pass_to(f: Footballer, kind: String, mate: Footballer, spot: Vector2, send_run := false) -> void:
	if g.carrier != f:
		g.hud.toast("%s has not got the ball" % f.display_name())
		return
	var action := kind if kind in ["pass", "through", "lob"] else "pass"
	if mate != null:
		var vel := Vector2.ZERO
		if action == "through" or send_run:
			vel = Vector2(f.team.dir * g.settings.through_run_speed, 0.0)
			g.kicking.after_release(f, func(): send_runner(f, mate, vel))        # he sets off when the ball is struck, not while the passer is still turning and winding up
		g.command.show(action, "LOB OVER THE TOP" if (action == "lob" and send_run) else action.to_upper(), f, mate, "%s runs onto it" % mate.display_name() if send_run or action == "through" else "", g.settings.command_hold)
		g.poss.kick_action(f, action, mate.pos, mate.vel if vel == Vector2.ZERO else vel, {}, mate)
	elif spot != Vector2.INF:
		g.command.show(action, action.to_upper() + " (SPACE)", f, null, "", g.settings.command_hold)
		g.poss.kick_action(f, action, spot)

## the runner of a through ball sets off (after a short reaction) towards where the ball will be
func send_runner(passer: Footballer, mate: Footballer, vel: Vector2) -> void:
	if mate.team != passer.team: return
	_run_order(mate, mate.pos + vel * g.settings.through_lead, g.settings.through_react)

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
