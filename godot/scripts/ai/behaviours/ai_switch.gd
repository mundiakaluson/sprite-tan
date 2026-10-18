class_name AiSwitch
extends AiBehaviour
## Overload then switch (catalogue section 1, Coaches' Voice "overload to isolate"): our side is blocked (their players crowd the ball) and the far side is open:
## a centre back, a 6 or an 8 switches it with a long diagonal to the far winger / full back who is in space, quickly, before they can shift back.

@export_group("Switch")
## crowded: at least this many of theirs within crowd_radius (m) of the ball
@export var crowd := 4
@export var crowd_radius := 14.0
## the target: on the other side (at least far_z from the middle, opposite the ball), nobody within free (m), 22 to max_len m away
@export var far_z := 14.0
@export var free := 7.0
@export var max_len := 48.0
## chances per second when it is on (x PAS / 100)
@export var rate := 2.5

static var stat_switches := 0

func _init() -> void:
	priority = 1
	roles = PackedStringArray(["CB", "CDM", "CM", "LB", "RB"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.game.kicking.busy(f) or f.lock > 0.0 or f.hold < 0.25: return false
	var n := 0
	for o in c.other.players:
		if o.pos.distance_to(f.pos) < crowd_radius: n += 1
	if n < crowd: return false
	if _target(f, c) == null: return false
	return c.game.rng.randf() < rate * f.stat("PAS", 60) / 100.0 * c.game.get_physics_process_delta_time()

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	var t := _target(f, c)
	if t == null: return i
	i.action = "lob"
	i.target = t
	i.note = "switch"
	stat_switches += 1
	return i

func _target(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bs := 0.0
	for m in c.team.players:
		if m == f or m.is_keeper(): continue
		if absf(m.pos.y) < far_z or signf(m.pos.y) == signf(f.pos.y): continue
		var d := m.pos.distance_to(f.pos)
		if d < 22.0 or d > max_len: continue
		if c.game.offside.would_be(m, f.pos.x): continue
		var room := c.pressure(m.pos)
		if room < free: continue
		var sc := room + (m.pos.x - f.pos.x) * c.dir * 0.2
		if sc > bs:
			bs = sc
			best = m
	return best
