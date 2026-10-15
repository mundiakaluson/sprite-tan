class_name Ai433
extends AiShapedFormation
## 4-3-3 (F02), after tactico.pro/formations/4-3-3.
## High line, high press: wide forwards stay up, the holder (CDM) drops between the centre backs, one full back goes and one stays.
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F02"])
	back_trail = 22.0
	back_max = 14.0
	back_min = -30.0
	gap_mid_st = 15.0
	wide_forward_line = 2
	block_depth = 0.6
	one_goes_one_stays = true
	holder_drop = 4.0
