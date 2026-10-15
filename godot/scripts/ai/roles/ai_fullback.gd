class_name AiFullback
extends AiRole
## Left and right back (and wingbacks in a back three / five). Overlaps when the winger in front has the ball, tucks in when the team defends.
## style "wingback" (styles.csv) goes much higher than "fullback" by data; the formation's `overlap` number says how eager.

func _init() -> void:
	push_weight = 0.7
	shoot_bias = 0.1
	dribble_urge = 0.3

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.phase == AiBrain.Phase.FINAL_THIRD or c.phase == AiBrain.Phase.PROGRESS:
		# overlap: run past the carrier on the wide side when the overlap number is high
		var on_my_side := c.carrier != null and signf(c.carrier.pos.y) == signf(f.slot.y)
		if on_my_side and c.f("overlap") > 0.5:
			spot.x = maxf(spot.x * c.dir, c.carrier.pos.x * c.dir + 6.0) * c.dir
		match c.family:
			"THREE_BACK", "FIVE_BACK": spot.y = signf(f.slot.y) * 30.0       # wingbacks hug the touchline
			_: pass
	return _go(c, c.clamp_pitch(spot, 1.5), c.s.jog_factor)
