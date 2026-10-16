class_name AiThroughBall
extends AiBehaviour
## On the ball: a team mate is running in behind (AiRunInBehind, f.ai["run_behind"]) - slide the ball into his path, through the defenders.
## Sees it more often with PAS; needs the lane to where the runner will be to be open (`lane` m either side free of opponents).

@export_group("Through ball")
## chances per second when a run is on (scaled by PAS)
@export var rate := 3.5
## the runner must already be running (m/s) and the pass this long at most (m)
@export var min_runner_speed := 3.0
@export var max_length := 38.0
## lane check to the lead point (where he will be lead_s seconds on)
@export var lead_s := 0.9
@export var lane := 1.4
## how often the pass is under-hit (x (1.3 - PAS/100)): half the time at PAS 80; an under-hit one goes at underhit_k of the speed, the runner has to check
## and the defenders / keeper get a chance at it
@export_range(0.0, 1.0) var underhit_chance := 0.6
@export var underhit_k := 0.68

static var stat_through := 0

func _init() -> void:
	priority = -4
	roles = PackedStringArray(["CM", "CAM", "CDM", "LW", "RW", "ST", "LB", "RB"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.game.kicking.busy(f) or f.lock > 0.0 or f.hold < 0.2: return false
	var r := _runner(f, c)
	if r == null: return false
	return c.game.rng.randf() < rate * (0.4 + f.stat("PAS", 60) / 100.0) * c.game.get_physics_process_delta_time()

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos + (f.vel if f.vel.length() > 0.5 else f.face).normalized() * 3.0
	i.speed = c.s.carry_factor
	var r := _runner(f, c)
	if r == null: return i
	i.action = "through"
	i.target = r
	if c.game.rng.randf() < underhit_chance * clampf(1.3 - f.stat("PAS", 60) / 100.0, 0.1, 1.0):
		i.over = {"speed_k": underhit_k}
	i.note = "through ball"
	stat_through += 1
	return i

func _runner(f: Footballer, c: AiContext) -> Footballer:
	for m in c.team.players:
		if m == f or not m.ai.has("run_behind") or m.vel.length() < min_runner_speed: continue
		var lead := m.pos + m.vel * lead_s
		if f.pos.distance_to(lead) > max_length: continue
		if (lead.x - f.pos.x) * c.dir < 2.0: continue                         # forward passes only
		if c.lane_blocked(f.pos, lead, lane): continue
		return m
	return null
