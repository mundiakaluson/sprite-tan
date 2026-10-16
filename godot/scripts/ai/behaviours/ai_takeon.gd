class_name AiTakeOn
extends AiBehaviour
## The man with the ball sees a defender in front of him with room to go past and takes him on: a feint one way and a burst the other (MatchDribble.take_on). Fast, skilled dribblers do it more.

@export_group("Take-on")
## a defender this close (m) in front of him, inside this half-angle (degrees) of his facing
@export var range_max := 7.0
@export var range_min := 1.8
@export var cone_deg := 55.0
## attempts per second at DRI 60 for a role with dribble_urge 0.3; scales with DRI and the role's urge
@export var rate := 3.0
## seconds before he tries again
@export var cooldown := 2.5
## never in his own third, never when a shot is on (pitch depth 0..1)
@export var min_depth := 0.3
@export var max_depth := 0.97
## in the final stretch (depth over final_depth) attackers try it final_boost times as often: they go at their man instead of passing back
@export var final_depth := 0.72
@export var final_boost := 2.5
@export var attack_roles := PackedStringArray(["ST", "LW", "RW", "CAM"])
## not with another defender this close behind the first (a double team: pass instead)
@export var second_man := 3.0

func _init() -> void:
	roles = PackedStringArray(["LW", "RW", "ST", "CAM", "CM", "CDM", "LB", "RB"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, role: AiRole) -> bool:
	if c.game.dribble.busy(f) or f.lock > 0.0 or f.hold < 0.3: return false
	if f.ai.get("takeon_cd", 0.0) > _now(): return false
	var depth := c.depth(f.pos)
	if depth < min_depth or depth > max_depth: return false
	var d := _defender(f, c)
	if d == null: return false
	var p := rate * (0.4 + f.stat("DRI", 60) / 100.0) * (0.5 + role.dribble_urge) * c.game.get_physics_process_delta_time()
	if depth > final_depth and f.role in attack_roles: p *= final_boost
	return c.game.rng.randf() < p

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	i.action = "takeon"
	i.target = _defender(f, c)
	f.ai["takeon_cd"] = _now() + cooldown
	i.note = "take-on"
	return i

## physics seconds since the start (not the match clock, which runs about 22x faster)
func _now() -> float:
	return Engine.get_physics_frames() / float(Engine.physics_ticks_per_second)

func _defender(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bd := range_max
	for o in c.other.players:
		if o.is_keeper(): continue
		var to := o.pos - f.pos
		var d := to.length()
		if d > range_max or d < range_min or d >= bd: continue
		if absf(f.face.angle_to(to)) > deg_to_rad(cone_deg): continue
		best = o
		bd = d
	if best == null: return null
	for o in c.other.players:
		if o != best and not o.is_keeper() and o.pos.distance_to(best.pos) < second_man and o.pos.distance_to(f.pos) < range_max + 2.0: return null
	return best
