class_name AiCm
extends AiRole
## Central midfielder. Box to box: supports the carrier in a triangle, arrives late in the box, covers when the team loses the ball.
## `playmaker` style looks for forward passes, `box_to_box` carries more.

func _init() -> void:
	push_weight = 0.8
	shoot_bias = 0.5
	dribble_urge = 0.4

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.carrier != null and c.phase != AiBrain.Phase.FINAL_THIRD:
		# triangle: offer an angle 9 m from the carrier, ahead and to one side
		var side := signf(f.slot.y - c.carrier.pos.y)
		if side == 0.0: side = 1.0
		spot = spot.lerp(c.carrier.pos + Vector2(c.dir * 6.0, side * 9.0), 0.4)
	elif c.phase == AiBrain.Phase.FINAL_THIRD and f.style == "box_to_box":
		spot.x += c.dir * 5.0       # arrive late into the box
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pass_bias(f: Footballer, m: Footballer, c: AiContext) -> float:
	# a playmaker wants the forward ball
	if f.style == "playmaker" and c.depth(m.pos) > c.depth(f.pos) + 0.1: return 5.0
	return 0.0
