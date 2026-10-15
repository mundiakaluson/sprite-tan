@tool
class_name FormationSlot
extends Resource
## One outfield position of a formation layout (the keeper is automatic). x = across the pitch 0..100 (0 = left touchline as the team faces the opponent), y = along 0..100 (0 = own goal line, 100 = opponent's).
## Same numbers as data/formation_slots.csv (F01 4-4-2: LB x15 y22, CM x38 y46, ST x40 y72).

@export_enum("CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST") var role := "CM"
## the style gives him his habits in each phase (data/styles.csv: fullback, wingback, stopper, anchor, box_to_box, playmaker, winger, inside_forward, shadow, target, poacher ...)
@export var style := "box_to_box"
@export_range(0.0, 100.0) var x := 50.0
@export_range(0.0, 100.0) var y := 50.0

func _validate_property(property: Dictionary) -> void:
	if property.name != "style": return
	var names: Array = []
	for r in Data.table("styles"): names.append(str(r.get("style", "")))
	if names.is_empty(): return
	property.hint = PROPERTY_HINT_ENUM
	property.hint_string = ",".join(names)
