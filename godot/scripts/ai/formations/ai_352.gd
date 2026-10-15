class_name Ai352
extends AiShapedFormation
## 3-5-2 (F07), after tactico.pro/formations/3-5-2.
## Wing-backs drop into a back five, the holder screens, the strike pair splits (one links, one runs); one wing-back goes, one stays.
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F07"])
	gap_back_mid = 11.0
	gap_mid_st = 15.0
	one_goes_one_stays = true
	wingback_ahead = 14.0
	sweeper_depth = 3.0
	holder_drop = 4.0
