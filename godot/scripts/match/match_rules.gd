class_name MatchRules
extends RefCounted
## Kick-off, goals, the ball going out (throw-in, goal kick, corner) and free kicks. Every restart goes through restart(): the taker is put on the spot with the ball,
## play stops (MatchGame.Phase.RESTART, the clock runs on) for MatchSettings > Restarts > restart_wait_<kind> while everybody else takes up position, opponents are
## kept restart_distance from the ball, then play resumes and the taker plays it. `kind` stays set until his first kick is released (consume()), which is how
## the offside law knows the kick came from a throw-in, goal kick or corner. Set-piece positions (who stands where) come in batch 5 of the behaviour catalogue.

var g: MatchGame
var kind := ""                     ## restart in force: "kickoff", "throw_in", "goal_kick", "corner", "free_kick" ("" in open play)
var taker: Footballer
var team: Team                     ## the side taking it
var spot := Vector2.ZERO           ## where the ball is
var indirect := false
var _waited := 0.0
var stat := {}                     ## kind -> count

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
	var pick := kicking.players[0]
	var best := 1e9
	for f in kicking.players:
		if f.is_keeper(): continue
		var d := f.pos.length()
		if d < best:
			best = d
			pick = f
	pick.pos = Vector2(-0.8 * kicking.dir, 0.0)
	g.offside.clear()
	g.carrier = null
	g.poss.take(pick)
	kind = "kickoff"
	taker = pick
	team = kicking
	spot = Vector2.ZERO
	stat["kickoff"] = int(stat.get("kickoff", 0)) + 1
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
	if absf(bp.z) > MatchGame.HALF_W:
		var taking := g.away if (g.last_touch != null and g.last_touch.team == g.home) else g.home
		restart("throw_in", taking, Vector2(clampf(bp.x, -MatchGame.HALF_L + 2.0, MatchGame.HALF_L - 2.0), signf(bp.z) * (MatchGame.HALF_W - 0.7)), "THROW-IN")
		return
	var defending := g.away if bp.x > 0.0 else g.home       # the side whose goal line it crossed
	var attacking := g.home if defending == g.away else g.away
	if g.last_touch != null and g.last_touch.team == attacking:
		restart("goal_kick", defending, Vector2(-defending.dir * (MatchGame.HALF_L - 6.0), 0.0), "GOAL KICK")
	else:
		restart("corner", attacking, Vector2(signf(bp.x) * (MatchGame.HALF_L - 0.8), signf(bp.z) * (MatchGame.HALF_W - 0.8)), "CORNER")

## the set-piece positions in force (AiSetPiece) were last worked out for this
func is_restart() -> bool:
	return g.phase == MatchGame.Phase.RESTART

## a free kick to `taking` at `at` (offside, a foul); indirect = no goal straight from it
func free_kick(taking: Team, at: Vector2, text: String, is_indirect := false) -> void:
	restart("free_kick", taking, at, text)
	indirect = is_indirect

## stop play and put the ball with the taker on `at`
func restart(k: String, taking: Team, at: Vector2, text: String, chosen: Footballer = null) -> void:
	g.offside.clear()
	var pick: Footballer = chosen
	var best := 1e9 if chosen == null else -1.0
	for f in taking.players:
		if chosen != null: break
		if (k == "goal_kick") != f.is_keeper(): continue
		var d := f.pos.distance_to(at)
		if d < best:
			best = d
			pick = f
	if pick == null: return
	for f in g.all:                                                  # whatever anyone was doing stops with the whistle
		f.pending = Callable()
		f.aim_done = Callable()
		f.order = {}
	pick.pos = at - Vector2(taking.dir, 0.0) * 0.4 if k != "corner" else at
	pick.vel = Vector2.ZERO
	pick.face = Vector2(taking.dir, 0.0) if k != "corner" else (Vector2(-at.x * 0.4, -at.y)).normalized()
	g.carrier = null
	g.poss.take(pick)
	pick.no_touch = 0.0
	pick.lock = 0.0
	kind = k
	taker = pick
	team = taking
	spot = at
	indirect = false
	stat[k] = int(stat.get(k, 0)) + 1
	g.phase = MatchGame.Phase.RESTART
	g.phase_t = _wait(k)
	_waited = 0.0
	g.hud.message(text, 1.2)

func _wait(k: String) -> float:
	var s := g.settings
	match k:
		"throw_in": return s.restart_wait_throw_in
		"goal_kick": return s.restart_wait_goal_kick
		"corner": return s.restart_wait_corner
		"penalty": return s.restart_wait_penalty
	return s.restart_wait_free_kick

## every physics frame while play is stopped for a restart: the taker waits on the ball, opponents keep their distance; then play resumes
func update_restart(dt: float) -> void:
	if taker == null or g.carrier != taker:
		g.phase = MatchGame.Phase.PLAY
		return
	taker.want = Vector2.ZERO
	taker.vel = Vector2.ZERO
	var dist := g.settings.restart_distance_throw if kind == "throw_in" else g.settings.restart_distance
	for f in g.all:
		if kind == "penalty" and f != taker and not f.is_keeper():         # a penalty: everybody else outside the box
			var gx := signf(spot.x) * (MatchGame.HALF_L - 16.5)
			if f.pos.x * signf(spot.x) > gx * signf(spot.x) - 0.5: f.pos.x = gx - signf(spot.x) * 0.6
		if kind == "goal_kick" and f.team != team and f.pos.x * team.dir < -MatchGame.HALF_L + 16.5 and absf(f.pos.y) < 20.16:
			f.pos.x = (-MatchGame.HALF_L + 17.0) * team.dir                  # opponents outside the box at a goal kick
		if f.team == team: continue
		var d := f.pos - spot
		if d.length() < dist:
			f.pos = spot + (d.normalized() if d.length() > 0.05 else Vector2(-team.dir, 0.0)) * dist
			if f.want.dot(-d) > 0.0: f.want = Vector2.ZERO
	g.phase_t -= dt / maxf(Engine.time_scale, 0.05)
	_waited += dt / maxf(Engine.time_scale, 0.05)
	var ready := g.brain == null or g.brain.unplaced == 0
	if g.phase_t <= 0.0 and (ready or _waited > g.settings.restart_max_wait):
		g.phase = MatchGame.Phase.PLAY
		taker.think = minf(taker.think, 0.15)

## the taker's kick was released: returns the restart it took ("" in open play) and ends it
func consume(f: Footballer) -> String:
	if kind == "" or f != taker:
		kind = ""
		return ""
	var k := kind
	kind = ""
	taker = null
	return k

## while play is stopped, or until he plays it, the taker is not to be pressed / tackled
func is_taker(f: Footballer) -> bool:
	return kind != "" and f == taker

func stats() -> Dictionary:
	return stat
