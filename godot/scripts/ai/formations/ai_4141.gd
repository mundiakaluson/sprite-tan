class_name Ai4141
extends AiShapedFormation
## 4-1-4-1 (F04), after tactico.pro/formations/4-1-4-1.
## A flat four in front of a screen: the holder never presses, he delays; wide mids tuck in or jump the full back; the lone striker presses the centre back.
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F04"])
	holder_drop = 8.0
	holder_contains = true
	gap_back_mid = 14.0
	gap_mid_st = 16.0
	wide_forward_line = 1
	one_goes_one_stays = true
	build_push = 10.0
