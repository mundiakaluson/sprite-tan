class_name AiCdm
extends AiRole
## Holding midfielder. Drops between the centre backs to receive in build-up, screens the defence when the team has lost the ball, and recycles possession.
## Formation switch: with two of them (4-2-3-1) they stay level; alone (4-3-3, 4-1-4-1) he sits deeper.

@export_group("Holding midfielder")
## in build-up he shows for the pass this far ahead of and across from the carrier
@export var show_ahead := 8.0
@export var show_across := 7.0
## how much of the way to that spot he goes when he is the lone holder (F02, F04, F06) / one of two
@export_range(0.0, 1.0) var lone_blend := 0.6
@export_range(0.0, 1.0) var pair_blend := 0.35
## pass taste: bonus for a pass to a central or attacking midfielder
@export var midfield_bonus := 3.0

func _init() -> void:
	push_weight = 0.5
	shoot_bias = 0.1
	dribble_urge = 0.15

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.phase == AiBrain.Phase.BUILD_UP and c.carrier != null:
		var show := c.carrier.pos + Vector2(c.dir * show_ahead, -signf(c.carrier.pos.y) * show_across)
		match c.formation_id:
			"F02", "F04", "F06": spot = spot.lerp(show, lone_blend)
			_: spot = spot.lerp(show, pair_blend)
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pass_bias(_f: Footballer, m: Footballer, _c: AiContext) -> float:
	return midfield_bonus if m.role == "CM" or m.role == "CAM" else 0.0
