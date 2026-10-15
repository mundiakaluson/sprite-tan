class_name Ai4231
extends AiShapedFormation
## 4-2-3-1 (F03), after tactico.pro/formations/4-2-3-1.
## Wingers drop into a midfield four (4-4-1-1 without the ball), the 10 stays between the lines, a double pivot (one holds, one steps forward).
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F03"])
	wide_forward_line = 1
	between_lines = 0.35
	mid_narrow = 0.9
	holder_drop = 2.0
	gap_mid_st = 14.0
	one_goes_one_stays = true
