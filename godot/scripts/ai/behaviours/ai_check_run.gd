class_name AiCheckRun
extends AiBehaviour
## Getting free of a marker (behaviour catalogue: "Come and go", striker "Come and go", the checking run). Off the ball, with a man tight on him and the pass to him
## not on, he CHECKS: a sharp few metres towards the ball. If the marker follows him, he SPINS in behind the space the marker left (and the passer can play him in:
## it is flagged like a run in behind for AiThroughBall); if the marker lets him go, he has made himself the open man and shows for the ball.

@export_group("Check and spin")
## marker within this (m), goal side of him; the carrier 8 to max_from_carrier m away
@export var marked_within := 2.8
@export var max_from_carrier := 30.0
## chances per second when marked (x game sense / 100)
@export var rate := 0.7
## the check: this far towards the ball, for this long (real s)
@export var check_dist := 4.5
@export var check_time := 0.55
## still followed after the check (marker within follow_within m): spin in behind, this far, for this long
@export var follow_within := 3.2
@export var spin_dist := 10.0
@export var spin_time := 1.3
## not followed: show for the ball this long
@export var show_time := 1.0
@export var cooldown := 4.0

static var stat_checks := 0
static var stat_spins := 0

func _init() -> void:
	priority = -2
	roles = PackedStringArray(["CM", "CAM", "ST", "LW", "RW"])
	when = SUPPORT

func _now(c: AiContext) -> float:
	return c.game.clock

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var st = f.ai.get("check", null)
	if st != null:
		if _now(c) < float(st["until"]) and c.has_ball: return true
		f.ai.erase("check")
		if st["phase"] == "spin":
			f.ai.erase("run_behind")
		return false
	if f.lock > 0.0 or float(f.ai.get("check_cd", -1e9)) > _now(c) or f.ai.has("run_behind"): return false
	var k := c.carrier
	if k == null or k.is_keeper(): return false
	var dk := f.pos.distance_to(k.pos)
	if dk < 8.0 or dk > max_from_carrier: return false
	var o := c.nearest_opponent(f.pos)
	if o == null or o.pos.distance_to(f.pos) > marked_within: return false
	if (o.pos.x - f.pos.x) * c.dir < -0.5: return false                       # the marker is not goal side of him
	var sense := (f.stat("PAS", 60) + f.stat("DRI", 60)) * 0.5
	return c.game.rng.randf() < rate * sense / 100.0 * c.game.get_physics_process_delta_time()

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var now := _now(c)
	var st = f.ai.get("check", null)
	if st == null:
		var to_ball := (c.ball - f.pos).normalized()
		st = {"phase": "check", "until": now + c.game_s(check_time), "spot": f.pos + to_ball * check_dist}
		f.ai["check"] = st
		f.ai["check_cd"] = now + c.game_s(check_time + spin_time + cooldown)
		stat_checks += 1
	elif st["phase"] == "check" and now >= float(st["until"]) - c.game_s(0.05):
		var o := c.nearest_opponent(f.pos)
		if o != null and o.pos.distance_to(f.pos) < follow_within:                 # he came with me: go in behind him
			var spot := c.clamp_pitch(f.pos + (c.goal() - f.pos).normalized() * spin_dist, 3.0)
			st = {"phase": "spin", "until": now + c.game_s(spin_time), "spot": spot}
			f.ai["run_behind"] = {"until": Engine.get_physics_frames() / float(Engine.physics_ticks_per_second) + spin_time, "spot": spot}
			stat_spins += 1
		else:
			st = {"phase": "show", "until": now + c.game_s(show_time), "spot": f.pos}
		f.ai["check"] = st
	var i := AiIntent.new()
	i.move_to = st["spot"]
	i.speed = c.s.sprint_factor if st["phase"] != "show" else c.s.jog_factor * 0.5
	i.note = "check " + String(st["phase"])
	return i
