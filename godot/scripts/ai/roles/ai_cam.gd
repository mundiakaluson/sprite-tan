class_name AiCam
extends AiRole
## Attacking midfielder / second striker. Finds pockets between the lines, plays through balls, shoots from the edge of the box.
## Formation switch: `shadow` style (4-3-2-1) runs beyond the striker; `playmaker` (4-2-3-1, diamond) stays behind him.

@export_group("Attacking midfielder")
## the shadow style runs this much further forward in the final third
@export var shadow_run := 6.0
## a through ball is played to a striker with at least this much space, deeper than through_depth (0..1 of the pitch)
@export var through_open := 4.0
@export_range(0.0, 1.0) var through_depth := 0.7

func _init() -> void:
	push_weight = 0.9
	shoot_bias = 0.8
	dribble_urge = 0.4

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if f.style == "shadow" and c.phase == AiBrain.Phase.FINAL_THIRD:
		spot.x += c.dir * shadow_run
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pick_pass(f: Footballer, c: AiContext) -> Dictionary:
	var o := super._pick_pass(f, c)
	if not o.is_empty() and o["mate"].role == "ST" and c.pressure(o["mate"].pos) > through_open and c.depth(o["mate"].pos) > through_depth:
		o["action"] = "through"
	return o
