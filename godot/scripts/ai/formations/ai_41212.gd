class_name Ai41212
extends AiShapedFormation
## 4-1-2-1-2 (diamond) (F06), after tactico.pro/formations/4-1-2-1-2.
## Narrow diamond: press the middle and let the wide pass go; both full backs supply the width; only one shuttler (CM) goes forward at a time.
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F06"])
	mid_narrow = 0.8
	between_lines = 0.4
	one_goes_one_stays = false
	trigger_fullback = false
	build_push = 12.0
	overlap_ahead = 10.0
	holder_drop = 4.0
	pocket_depth = 12.0
