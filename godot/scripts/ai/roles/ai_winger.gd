class_name AiWinger
extends AiRole
## Winger (LW / RW, also the wide midfielders of a 4-4-2). Hugs the touchline to stretch play, tracks back to form the bank, runs at the full back.
## Formation switch: `inside_forward` (4-3-3, 3-4-3) cuts in towards goal; `winger` stays wide; `wide_mid` drops back to defend.

@export_group("Winger")
## the winger style stands this far from the centre line; an inside forward cuts in to cut_in_z in the final third
@export var wide_z := 29.0
@export var cut_in_z := 12.0
## in the final third, from further out than cross_z a pass to a striker becomes a cross (lob)
@export var cross_z := 22.0

func _init() -> void:
	attacker = true
	push_weight = 1.0
	shoot_bias = 0.6
	dribble_urge = 0.55

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	match f.style:
		"winger": spot.y = signf(f.slot.y) * wide_z
		"inside_forward":
			if c.phase == AiBrain.Phase.FINAL_THIRD: spot.y = signf(f.slot.y) * cut_in_z
		_: pass
	return _go(c, c.clamp_pitch(spot, 1.5), c.s.jog_factor)

func _pick_pass(f: Footballer, c: AiContext) -> Dictionary:
	var o := super._pick_pass(f, c)
	if not o.is_empty() and c.phase == AiBrain.Phase.FINAL_THIRD and absf(f.pos.y) > cross_z and o["mate"].role == "ST":
		o["action"] = "lob"
	return o
