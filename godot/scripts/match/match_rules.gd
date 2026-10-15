class_name MatchRules
extends RefCounted
## Kick-off, goals, and the ball going out (throw-in, goal kick, corner). Restarts put the nearest player on the spot with the ball; no referee yet.

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

func kickoff(kicking: Team) -> void:
	for t in g.teams:
		for f in t.players:
			f.pos = f.slot
			if f.pos.x * t.dir > -2.0: f.pos.x = -2.0 * t.dir
			f.vel = Vector2.ZERO
			f.want = Vector2.ZERO
			f.lock = 0.0
			f.no_touch = 0.0
			f.shield = 0.0
			f.pending = Callable()
			f.order = {}
			f.face = Vector2(t.dir, 0.0)
			f.think = g.rng.randf_range(0.2, 0.8)
	var taker := kicking.players[0]
	var best := 1e9
	for f in kicking.players:
		if f.is_keeper(): continue
		var d := f.pos.length()
		if d < best:
			best = d
			taker = f
	taker.pos = Vector2(-0.8 * kicking.dir, 0.0)
	g.carrier = null
	g.poss.take(taker)
	g.stadium.focus = Vector2(50, 50)
	g.stadium.snap_camera()

## goal or out of play, every physics frame while playing
func check() -> void:
	var bp := g.ball.phys.pos
	if absf(bp.x) > MatchGame.HALF_L + 0.2:
		if absf(bp.z) < MatchGame.GOAL_HALF and bp.y < MatchGame.BAR + g.ball.phys.rad: g.goal(g.home if bp.x > 0.0 else g.away)
		elif absf(bp.x) > MatchGame.HALF_L + 0.6: _out(bp)
	elif absf(bp.z) > MatchGame.HALF_W + 0.3:
		_out(bp)

func _out(bp: Vector3) -> void:
	var spot := Vector2.ZERO
	var taking: Team
	var text := ""
	if absf(bp.z) > MatchGame.HALF_W:
		taking = g.away if (g.last_touch != null and g.last_touch.team == g.home) else g.home
		spot = Vector2(clampf(bp.x, -MatchGame.HALF_L + 2.0, MatchGame.HALF_L - 2.0), signf(bp.z) * (MatchGame.HALF_W - 0.7))
		text = "THROW-IN"
	else:
		var defending := g.away if bp.x > 0.0 else g.home       # the side whose goal line it crossed
		var attacking := g.home if defending == g.away else g.away
		if g.last_touch != null and g.last_touch.team == attacking:
			taking = defending
			spot = Vector2(-defending.dir * (MatchGame.HALF_L - 6.0), 0.0)
			text = "GOAL KICK"
		else:
			taking = attacking
			spot = Vector2(signf(bp.x) * (MatchGame.HALF_L - 0.8), signf(bp.z) * (MatchGame.HALF_W - 0.8))
			text = "CORNER"
	var taker: Footballer = null
	var best := 1e9
	for f in taking.players:
		if (text == "GOAL KICK") != f.is_keeper(): continue
		var d := f.pos.distance_to(spot)
		if d < best:
			best = d
			taker = f
	if taker == null: return
	taker.pos = spot
	taker.vel = Vector2.ZERO
	taker.face = Vector2(taking.dir, 0.0) if text != "CORNER" else (-spot).normalized()
	g.carrier = null
	g.poss.take(taker)
	taker.no_touch = 0.0
	g.hud.message(text, 1.2)
