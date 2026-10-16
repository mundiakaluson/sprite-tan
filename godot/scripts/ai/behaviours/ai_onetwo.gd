class_name AiOneTwo
extends AiBehaviour
## The simple one-two (give and go). The man with the ball sees a defender in his way and a team mate close by who is free: he plays it to him and runs past the defender; the team mate
## (if he is still free) returns it first time with a through ball into the run. Both halves are this one behaviour: `wants()` is also true for the wall man who owes a return.
## The enhanced version (a skill card with its own attributes) comes later: the numbers here are what that card would set.

@export_group("One-two")
## roles that start one (anyone can be the wall and return it)
@export var starter_roles := PackedStringArray(["CM", "CAM", "LW", "RW", "ST", "CDM", "LB", "RB"])
## per second, for a player with the ball in the attacking part of the pitch who meets the conditions
@export var rate := 1.6
## the defender he wants to get past: in front (within this many degrees of the way he faces) and between these distances (m)
@export var cone_deg := 50.0
@export var defender_min := 3.0
@export var defender_max := 11.0
## the wall: a team mate between these distances, ahead or alongside (within this angle of his facing), with no opponent closer than `wall_free` m
@export var wall_min := 5.0
@export var wall_max := 15.0
@export var wall_cone_deg := 85.0
@export var wall_free := 4.0
## pitch depth 0..1 (own goal to opponent goal) where he tries it
@export var min_depth := 0.35
@export var max_depth := 0.88
## he runs this far (m) ahead and this far to the side the defender is not
@export var run_ahead := 13.0
@export var run_side := 4.0
## the wall man returns it within this many seconds of the pass, unless an opponent is already this close (m) to him
@export var return_window := 2.5
@export var return_min_gap := 1.2
## seconds the team waits before another one-two
@export var cooldown := 8.0

static var stat_started := 0     ## headless counters
static var stat_returned := 0

func _init() -> void:
	priority = -2
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, role: AiRole) -> bool:
	var ret = f.ai.get("onetwo_return", null)
	if ret != null:
		if _now() > float(ret["until"]) or ret["to"].team != f.team or c.pressure(f.pos) < return_min_gap: f.ai.erase("onetwo_return")
		else: return f.hold >= 0.1                                      # take it, then play it first time
	if not f.role in starter_roles: return false
	if c.game.kicking.busy(f) or c.game.dribble.busy(f) or f.lock > 0.0 or f.hold < 0.4: return false
	if float(c.team.ai.get("onetwo_cd", 0.0)) > _now(): return false
	var depth := c.depth(f.pos)
	if depth < min_depth or depth > max_depth: return false
	if _defender(f, c) == null: return false
	if _wall(f, c) == null: return false
	return c.game.rng.randf() < rate * (0.4 + f.stat("PAS", 60) / 100.0) * (0.5 + role.dribble_urge) * c.game.get_physics_process_delta_time()

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	var ret = f.ai.get("onetwo_return", null)
	if ret != null:                                                       # the return: a through ball to the runner
		f.ai.erase("onetwo_return")
		stat_returned += 1
		i.action = "through"
		i.target = ret["to"]
		i.note = "one-two return"
		return i
	var d := _defender(f, c)
	var wall := _wall(f, c)
	c.team.ai["onetwo_cd"] = _now() + cooldown
	var dirv := (c.goal() - f.pos).normalized()
	var side := Vector2(-dirv.y, dirv.x)
	if side.dot(d.pos - f.pos) > 0.0: side = -side                       # away from the defender
	var spot := c.clamp_pitch(f.pos + dirv * run_ahead + side * run_side, 1.0)
	wall.ai["onetwo_return"] = {"to": f, "until": _now() + return_window + 1.5}
	stat_started += 1
	i.action = "pass"
	i.target = wall
	var orders := c.game.orders
	c.game.kicking.after_release(f, func(): orders.send_run(f, spot, 0.1))   # he sets off once the ball has gone
	i.note = "one-two"
	return i

func _defender(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bd := defender_max
	for o in c.other.players:
		if o.is_keeper(): continue
		var to := o.pos - f.pos
		var d := to.length()
		if d > defender_max or d < defender_min or d >= bd: continue
		if absf(f.face.angle_to(to)) > deg_to_rad(cone_deg): continue
		best = o
		bd = d
	return best

func _wall(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f or m.is_keeper() or m.lock > 0.0: continue
		var to := m.pos - f.pos
		var d := to.length()
		if d < wall_min or d > wall_max: continue
		if absf(f.face.angle_to(to)) > deg_to_rad(wall_cone_deg): continue
		var opp := c.nearest_opponent(m.pos)
		if opp != null and opp.pos.distance_to(m.pos) < wall_free: continue
		if c.lane_blocked(f.pos, m.pos, 1.3): continue
		var score := to.normalized().dot((c.goal() - f.pos).normalized()) * 4.0 + (opp.pos.distance_to(m.pos) if opp != null else 8.0) * 0.3 + m.stat("PAS", 60) * 0.03
		if score > bs:
			bs = score
			best = m
	return best

func _now() -> float:
	return Engine.get_physics_frames() / float(Engine.physics_ticks_per_second)
