class_name AiWinger
extends AiRole
## Winger (LW / RW, also the wide midfielders of a 4-4-2). Hugs the touchline to stretch play, tracks back to form the bank, runs at the full back.
## Formation switch: `inside_forward` (4-3-3, 3-4-3) cuts in towards goal; `winger` stays wide; `wide_mid` drops back to defend.

func _init() -> void:
	push_weight = 1.0
	shoot_bias = 0.6
	dribble_urge = 0.55

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	match f.style:
		"winger": spot.y = signf(f.slot.y) * 29.0
		"inside_forward":
			if c.phase == AiBrain.Phase.FINAL_THIRD: spot.y = signf(f.slot.y) * 12.0
		_: pass
	return _go(c, c.clamp_pitch(spot, 1.5), c.s.jog_factor)

func _pick_pass(f: Footballer, c: AiContext) -> Dictionary:
	var o := super._pick_pass(f, c)
	# in the final third a cross into the box beats a short pass
	if not o.is_empty() and c.phase == AiBrain.Phase.FINAL_THIRD and absf(f.pos.y) > 22.0 and o["mate"].role == "ST":
		o["action"] = "lob"
	return o
