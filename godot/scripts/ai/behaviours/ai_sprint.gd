class_name AiSprint
extends AiBehaviour
## An attacker with the ball sees open grass ahead and sprints into it (the sprint clip, faster than the carry pace, drains stamina). He stops sprinting when a defender closes in,
## when he is near goal (the role shoots) or when he is tired. Fresh, quick players do it more.

@export_group("Sprint")
## open space: no opponent within this many metres ahead, inside this half-angle (degrees) of the line to goal
@export var space_range := 16.0
@export var cone_deg := 28.0
## no opponent this close (m) in any direction when he starts
@export var min_gap := 3.5
## it breaks off when one gets this close ahead
@export var break_gap := 4.5
## per second at PAC 60 and full stamina; he sprints for `duration` s
@export var rate := 1.6
@export var duration := 2.6
@export var min_stamina := 0.4
## pitch depth (0 own goal .. 1 opponent goal) in which he sprints
@export var min_depth := 0.3
@export var max_depth := 0.86

func _init() -> void:
	roles = PackedStringArray(["LW", "RW", "ST", "CAM", "CM", "LB", "RB", "CDM"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if f.lock > 0.0 or c.game.dribble.busy(f) or not f.aim_done.is_null(): return false
	var depth := c.depth(f.pos)
	if depth < min_depth or depth > max_depth: return false
	var now := _now()
	var active: bool = float(f.ai.get("sprint_until", 0.0)) > now
	if active:
		if f.stamina < 0.15 or _nearest_ahead(f, c) < break_gap: f.ai["sprint_until"] = 0.0
		else: return true
		return false
	if f.stamina < min_stamina or f.hold < 0.4 or float(f.ai.get("sprint_cd", 0.0)) > now: return false
	if c.pressure(f.pos) < min_gap or _nearest_ahead(f, c) < space_range: return false
	var p := rate * (0.5 + f.stat("PAC", 60) / 120.0) * c.game.get_physics_process_delta_time()
	if c.game.rng.randf() >= p: return false
	f.ai["sprint_until"] = now + duration
	f.ai["sprint_cd"] = now + duration + 2.0
	return true

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = c.clamp_pitch(f.pos + _line(f, c) * 22.0, 1.0)
	i.speed = c.s.sprint_factor
	i.note = "sprint"
	return i

## unit vector towards the opponents' goal (a little towards the middle)
func _line(f: Footballer, c: AiContext) -> Vector2:
	var to := Vector2(c.goal().x, f.pos.y * 0.5) - f.pos
	return to.normalized() if to.length() > 0.1 else f.face

## distance to the nearest opponent inside the cone ahead (a big number when none within space_range)
func _nearest_ahead(f: Footballer, c: AiContext) -> float:
	var dir := _line(f, c)
	var best := 999.0
	for o in c.other.players:
		var to := o.pos - f.pos
		var d := to.length()
		if d > space_range or d < 0.1: continue
		if absf(dir.angle_to(to)) > deg_to_rad(cone_deg): continue
		best = minf(best, d)
	return best

func _now() -> float:
	return Engine.get_physics_frames() / float(Engine.physics_ticks_per_second)
