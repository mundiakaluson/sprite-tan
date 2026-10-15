class_name AiFullback
extends AiRole
## Left and right back (and wingbacks in a back three / five). Overlaps when the winger in front has the ball, tucks in when the team defends.
## style "wingback" (styles.csv) goes much higher than "fullback" by data; the formation's `overlap` number says how eager.

@export_group("Fullback")
## overlap when the formation's overlap number is above this, running this far past the carrier
@export_range(0.0, 1.0) var overlap_threshold := 0.5
@export var overlap_ahead := 6.0
## wingbacks (back three / five) hug the touchline at this distance from the centre line
@export var touchline_z := 30.0

func _init() -> void:
	push_weight = 0.7
	shoot_bias = 0.1
	dribble_urge = 0.3

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.phase == AiBrain.Phase.FINAL_THIRD or c.phase == AiBrain.Phase.PROGRESS:
		var on_my_side := c.carrier != null and signf(c.carrier.pos.y) == signf(f.slot.y)
		if on_my_side and c.f("overlap") > overlap_threshold:
			spot.x = maxf(spot.x * c.dir, c.carrier.pos.x * c.dir + overlap_ahead) * c.dir
		match c.family:
			"THREE_BACK", "FIVE_BACK": spot.y = signf(f.slot.y) * touchline_z
			_: pass
	return _go(c, c.clamp_pitch(spot, 1.5), c.s.jog_factor)
