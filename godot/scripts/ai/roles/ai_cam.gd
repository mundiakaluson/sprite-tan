class_name AiCam
extends AiRole
## Attacking midfielder / second striker. Finds pockets between the lines, plays through balls, shoots from the edge of the box.
## Formation switch: `shadow` style (4-3-2-1) runs beyond the striker; `playmaker` (4-2-3-1, diamond) stays behind him.

func _init() -> void:
	push_weight = 0.9
	shoot_bias = 0.8
	dribble_urge = 0.4

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if f.style == "shadow" and c.phase == AiBrain.Phase.FINAL_THIRD:
		spot.x += c.dir * 6.0
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pick_pass(f: Footballer, c: AiContext) -> Dictionary:
	var o := super._pick_pass(f, c)
	# a through ball to a striker in space is his signature
	if not o.is_empty() and o["mate"].role == "ST" and c.pressure(o["mate"].pos) > 4.0 and c.depth(o["mate"].pos) > 0.7:
		o["action"] = "through"
	return o
