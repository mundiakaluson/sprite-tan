class_name AiCm
extends AiRole
## Central midfielder. Box to box: supports the carrier in a triangle, arrives late in the box, covers when the team loses the ball.
## `playmaker` style looks for forward passes, `box_to_box` carries more.

@export_group("Central midfielder")
## triangle support: offer an angle this far ahead of and across from the carrier, going this much of the way there
@export var triangle_ahead := 6.0
@export var triangle_across := 9.0
@export_range(0.0, 1.0) var triangle_blend := 0.4
## box_to_box in the final third arrives this much further forward
@export var late_arrival := 5.0
## playmaker pass taste: bonus for a pass that is at least forward_gap (0..1 of the pitch) deeper than him
@export var playmaker_bonus := 5.0
@export_range(0.0, 0.5) var forward_gap := 0.1

func _init() -> void:
	push_weight = 0.8
	shoot_bias = 0.5
	dribble_urge = 0.4

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.carrier != null and c.phase != AiBrain.Phase.FINAL_THIRD:
		var side := signf(f.slot.y - c.carrier.pos.y)
		if side == 0.0: side = 1.0
		spot = spot.lerp(c.carrier.pos + Vector2(c.dir * triangle_ahead, side * triangle_across), triangle_blend)
	elif c.phase == AiBrain.Phase.FINAL_THIRD and f.style == "box_to_box":
		spot.x += c.dir * late_arrival
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pass_bias(f: Footballer, m: Footballer, c: AiContext) -> float:
	if f.style == "playmaker" and c.depth(m.pos) > c.depth(f.pos) + forward_gap: return playmaker_bonus
	return 0.0
