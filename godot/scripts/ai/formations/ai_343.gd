class_name Ai343
extends AiShapedFormation
## 3-4-3 (F08), after tactico.pro/formations/3-4-3.
## All-out attack: wide forwards tuck into the midfield four without the ball (5-4-1), both wing-backs go, one runs back at once on a turnover.
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F08"])
	wide_forward_line = 1
	one_goes_one_stays = false
	gap_back_mid = 12.0
	gap_mid_st = 16.0
	wingback_ahead = 16.0
	sweeper_depth = 3.0
	block_depth = 0.5
