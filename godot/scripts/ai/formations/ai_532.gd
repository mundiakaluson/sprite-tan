class_name Ai532
extends AiShapedFormation
## 5-3-2 (F09), after tactico.pro/formations/5-3-2.
## Mid block: back five, a compact three 10-12 m ahead, the strikers screen 20 m further up; only one wing-back advances; the strikers are the counter.
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F09"])
	gap_back_mid = 11.0
	gap_mid_st = 22.0
	one_goes_one_stays = true
	wingback_ahead = 8.0
	sweeper_depth = 3.0
	block_depth = 0.4
	holder_drop = 3.0
	back_trail = 30.0
