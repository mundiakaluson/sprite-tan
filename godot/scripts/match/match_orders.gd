class_name MatchOrders
extends RefCounted
## The human's orders to his players (from MatchControls and the HUD buttons). A run / press is stored on the footballer (`order`) and followed here until it is done.

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

## the order buttons that make sense for a player now
func menu_for(f: Footballer) -> Array:
	if g.carrier == f: return ["through", "run"]
	return ["run", "press", "tackle"]

## a run: he goes there by himself (the carrier dribbles there), then the AI takes over again
func run(f: Footballer, spot: Vector2) -> void:
	spot.x = clampf(spot.x, -MatchGame.HALF_L + 1.0, MatchGame.HALF_L - 1.0)
	spot.y = clampf(spot.y, -MatchGame.HALF_W + 1.0, MatchGame.HALF_W - 1.0)
	f.order = {"kind": "run", "target": spot, "t": 9.0}
	g.hud.toast("%s: run" % f.display_name())

## chase the ball (or its carrier) for a few seconds
func press(f: Footballer) -> void:
	f.order = {"kind": "press", "t": 5.0}
	g.hud.toast("%s: press" % f.display_name())

func tackle(f: Footballer) -> void:
	if g.carrier == null or g.carrier.team == f.team:
		g.hud.toast("Nobody to tackle")
		return
	if f.pos.distance_to(g.carrier.pos) > 3.0:
		f.order = {"kind": "press", "t": 3.0}
		g.hud.toast("Too far: closing down")
		return
	g.poss.try_tackle(f)

## shoot at a spot of the grass (the drag from the ball carrier)
func shoot_at(f: Footballer, spot: Vector2) -> void:
	if g.carrier != f: return
	var over := {}
	if g.rng.randf() < 0.12: over["style"] = "K02"
	g.poss.kick_action(f, "shot", spot, Vector2.ZERO, over)

## kind = "pass" / "through" / "lob". To a team mate (the ball leads him; a through ball also sends him running) or to a spot.
func pass_to(f: Footballer, kind: String, mate: Footballer, spot: Vector2) -> void:
	if g.carrier != f:
		g.hud.toast("%s has not got the ball" % f.display_name())
		return
	var action := kind if kind in ["pass", "through", "lob"] else "pass"
	if mate != null:
		var vel := Vector2.ZERO
		if action == "through":
			vel = Vector2(f.team.dir * 7.0, 0.0)
			run(mate, mate.pos + vel * 1.5)
		g.poss.kick_action(f, action, mate.pos, mate.vel if vel == Vector2.ZERO else vel, {}, mate)
	elif spot != Vector2.INF:
		g.poss.kick_action(f, action, spot)

## called by the AI brain for a player with an order
func follow(f: Footballer, dt: float) -> void:
	var o := f.order
	o["t"] = float(o.get("t", 5.0)) - dt
	if o["t"] <= 0.0:
		f.order = {}
		return
	var s := g.settings
	var kind := String(o["kind"])
	if kind == "run":
		var to: Vector2 = o["target"] - f.pos
		if to.length() < 1.2:
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
