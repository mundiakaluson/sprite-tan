class_name Ai541
extends AiShapedFormation
## 5-4-1 (F10), after tactico.pro/formations/5-4-1.
## Low block: two banks 12 m apart, one block height held, we do not hunt the ball in their half (few press moments), wing-backs and wide mids break forward in support of the lone striker.
## The play is in ai_shaped_formation.gd; this file only holds this formation's numbers (all editable in the inspector).

func _init() -> void:
	formation_ids = PackedStringArray(["F10"])
	back_trail = 18.0
	back_min = -36.0
	back_max = -6.0
	gap_back_mid = 12.0
	gap_mid_st = 18.0
	block_depth = 0.35
	trigger_fullback = false
	trigger_back_pass = false
	trigger_facing_own_goal = false
	one_goes_one_stays = false
	wingback_ahead = 12.0
	sweeper_depth = 3.0
	wide_forward_line = 1
	width_z = 26.0
