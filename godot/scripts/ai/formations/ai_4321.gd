class_name Ai4321
extends AiShapedFormation
## 4-3-2-1 (F05), after tactico.pro/formations/4-3-2-1.
## Christmas tree: two 10s lock the opposition pivots and funnel play wide, full backs carry all the width (one goes, one stays).
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F05"])
	mid_narrow = 0.85
	between_lines = 0.5
	one_goes_one_stays = true
	build_push = 12.0
	pocket_depth = 10.0
	holder_drop = 4.0
