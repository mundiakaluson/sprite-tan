class_name AiCdm
extends AiRole
## Holding midfielder. Drops between the centre backs to receive in build-up, screens the defence when the team has lost the ball, and recycles possession.
## Formation switch: with two of them (4-2-3-1) they stay level; alone (4-3-3, 4-1-4-1) he sits deeper.

func _init() -> void:
	push_weight = 0.5
	shoot_bias = 0.1
	dribble_urge = 0.15

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.phase == AiBrain.Phase.BUILD_UP and c.carrier != null:
		# show for the pass: a few metres ahead of the ball carrier, across from him
		var show := c.carrier.pos + Vector2(c.dir * 8.0, -signf(c.carrier.pos.y) * 7.0)
		match c.formation_id:
			"F02", "F04", "F06": spot = spot.lerp(show, 0.6)       # lone holding midfielder
			_: spot = spot.lerp(show, 0.35)
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pass_bias(_f: Footballer, m: Footballer, _c: AiContext) -> float:
	return 3.0 if m.role == "CM" or m.role == "CAM" else 0.0
