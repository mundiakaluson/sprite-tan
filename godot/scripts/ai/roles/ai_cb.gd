class_name AiCb
extends AiRole
## Centre back. Holds the line, splits wide in build-up so the keeper has a pass, plays safe (never shoots, rarely dribbles) and lets the ball playing styles step forward.
## Formation switch: in a back three the middle one (style sweeper) covers behind; in a back five all three stay compact.

func _init() -> void:
	push_weight = 0.35
	shoot_bias = 0.0
	dribble_urge = 0.1

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.phase == AiBrain.Phase.BUILD_UP:
		# split wide of the ball so the carrier has an angle
		match c.family:
			"THREE_BACK", "FIVE_BACK": spot.y = spot.y * 1.25
			_: spot.y = spot.y * 1.5
	if f.style == "sweeper": spot.x -= c.dir * 3.0
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pass_bias(f: Footballer, m: Footballer, c: AiContext) -> float:
	# prefer keeping it: sideways or forward to a midfielder, not a long ball
	var b := 0.0
	if m.role == "CDM" or m.role == "CM": b += 4.0
	if m.pos.distance_to(f.pos) > 25.0: b -= 6.0
	return b
