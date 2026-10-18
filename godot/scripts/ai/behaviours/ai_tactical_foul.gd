class_name AiTacticalFoul
extends AiBehaviour
## The tactical foul (behaviour catalogue section 2 "Tactical foul"). Their counter is starting, we are out of shape, and he is the man the carrier has just got
## past: he pulls him back. Not when he is already booked, not near our box (the free kick would be worse than the counter), more often for a defensive midfielder.
## MatchReferee gives the free kick and (almost always) the yellow.

@export_group("Tactical foul")
## the carrier within reach (m) and already level with or past him towards our goal
@export var reach := 1.8
## we are out of shape: at most this many of ours goal side of the ball (outfield)
@export var max_goal_side := 3
## not with the ball closer to our goal line than this (m)
@export var min_from_goal := 30.0
## chance per second while it is on (x role factor)
@export var rate := 1.6
@export var role_k := {"CDM": 1.4, "CM": 1.0, "CB": 0.8, "LB": 0.8, "RB": 0.8, "CAM": 0.6}

static var stat_fouls := 0

func _init() -> void:
	priority = -15
	roles = PackedStringArray(["CDM", "CM", "CB", "LB", "RB", "CAM"])
	when = DEFENDING

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var k := c.carrier
	if k == null or f.lock > 0.0 or c.game.referee.yellows(f) > 0: return false
	if k.pos.distance_to(f.pos) > reach: return false
	if (k.pos.x - f.pos.x) * c.dir > 0.5: return false                       # he is not past me yet
	if k.pos.distance_to(c.own_goal()) < min_from_goal: return false
	if c.game.engage.busy(k) or c.game.engage.busy(f): return false
	var n := 0
	for m in c.team.players:
		if not m.is_keeper() and (m.pos.x - k.pos.x) * c.dir < 0.0: n += 1
	if n > max_goal_side: return false
	return c.game.rng.randf() < rate * float(role_k.get(f.role, 1.0)) * c.game.get_physics_process_delta_time()

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = c.carrier.pos
	i.action = "foul"
	i.target = c.carrier
	i.note = "tactical foul"
	stat_fouls += 1
	return i
