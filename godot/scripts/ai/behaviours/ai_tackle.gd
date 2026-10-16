class_name AiTackle
extends AiBehaviour
## A defender goes in on the carrier: a standing tackle when he is within reach, a slide when the carrier is running past him a few metres away (MatchDribble.slide_tackle, MatchPossession.start_tackle).
## The chance rises with DEF; it is lower for sliding inside his own box and he never slides when he is the last man with a team mate covering.

@export_group("Tackle")
## standing tackle: carrier within this many metres, attempts per second (x (DEF + 30) / (carrier DRI + 30))
@export var stand_range := 2.1
@export var stand_rate := 3.0
## slide: carrier between stand_range and this, running at least slide_min_speed m/s, and the defender's DEF at least slide_min_def; attempts per second
@export var slide_range := 4.5
@export var slide_min_speed := 3.0
@export var slide_min_def := 50
@export var slide_rate := 3.5
## sliding in his own box is risky: the rate is multiplied by this
@export var box_caution := 0.3
## seconds before the same defender goes in again
@export var cooldown := 2.0
## only the nearest defenders (the presser and team mates within this many metres of the carrier)
@export var helper_range := 3.5

func _init() -> void:
	roles = PackedStringArray(["CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"])
	when = DEFENDING
	priority = -5

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var carrier := c.carrier
	if carrier == null or f.lock > 0.0 or f.no_touch > 0.0 or c.game.dribble.busy(f) or c.game.dribble.busy(carrier): return false
	if f.ai.get("tackle_cd", 0.0) > _now(): return false
	var d := f.pos.distance_to(carrier.pos)
	if d > slide_range: return false
	if f != c.presser and d > helper_range: return false
	return _kind(f, c, d) != ""

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var carrier := c.carrier
	var d := f.pos.distance_to(carrier.pos)
	var kind := _kind(f, c, d)
	var i := AiIntent.new()
	i.move_to = carrier.pos
	i.speed = c.s.sprint_factor
	i.note = kind
	if kind != "":
		i.action = kind
		i.target = carrier
		f.ai["tackle_cd"] = _now() + cooldown
	return i

## "tackle" / "slide" for this frame, or "" (a random gate per frame, so he goes in now and then rather than the moment he arrives)
func _kind(f: Footballer, c: AiContext, d: float) -> String:
	var dt := c.game.get_physics_process_delta_time()
	var carrier := c.carrier
	var rng := c.game.rng
	if d <= stand_range:
		var p := stand_rate * (f.stat("DEF", 60) + 30.0) / (carrier.stat("DRI", 60) + 30.0) * dt
		return "tackle" if rng.randf() < p else ""
	if carrier.vel.length() < slide_min_speed or f.stat("DEF", 60) < slide_min_def: return ""
	if carrier.shield > 0.0: return ""
	var p2 := slide_rate * (f.stat("DEF", 60) + 30.0) / (carrier.stat("DRI", 60) + 30.0) * dt
	if c.in_zone(f.pos, "own_box"): p2 *= box_caution
	return "slide" if rng.randf() < p2 else ""

func _now() -> float:
	return Engine.get_physics_frames() / float(Engine.physics_ticks_per_second)
