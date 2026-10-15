@tool
class_name FormationLayout
extends Resource
## A formation made in the inspector: MatchSettings > Match > Custom Formations > add an element > New FormationLayout. Fill in the name, the family and the ten outfield slots
## (role, style, x, y); then it shows in the Home / Away Formation lists. It plays with `play` (an AiShapedFormation resource, so you can tune its press / block numbers) or, if that is empty,
## the default shared play. The shape numbers below override the family's (leave at -1 to use the family's). The 10 built-in formations come from the manager tool (data/formations.csv).

@export var id := "C01"
## shown in the formation lists, e.g. "3-4-2-1"
@export var layout_name := "3-4-2-1":
	set(v):
		layout_name = v
		emit_changed()
@export_enum("FOUR_BACK", "THREE_BACK", "FIVE_BACK") var family := "THREE_BACK"
@export_multiline var note := ""
@export var slots: Array[FormationSlot] = []
## team play of this formation: an AiShapedFormation (or any AiFormation). Its formation_ids are filled in with this layout's id automatically
@export var play: AiFormation

@export_group("Shape numbers (-1 = the family's)")
@export_range(-1.0, 1.0) var line_height := -1.0
@export_range(-1.0, 1.0) var width := -1.0
@export_range(-1.0, 1.0) var compactness := -1.0
@export_range(-1.0, 1.0) var press := -1.0
@export_range(-1.0, 1.0) var overlap := -1.0
@export_range(-1.0, 1.0) var directness := -1.0
@export_range(-1.0, 1.0) var counter := -1.0
@export_range(-1.0, 1.0) var risk := -1.0

## the row formations.csv would have, as strings ("" = the family's number)
func row() -> Dictionary:
	var r := {"id": id, "name": layout_name, "family": family, "note": note}
	for k in ["line_height", "width", "compactness", "press", "overlap", "directness", "counter", "risk"]:
		var v: float = get(k)
		r[k] = "" if v < 0.0 else str(v)
	return r

## the play object for this formation (its own, or a shared default), with the id set
func play_for() -> AiFormation:
	var p: AiFormation = play
	if p == null:
		if _default == null: _default = AiShapedFormation.new()
		p = _default
	if not (id in p.formation_ids): p.formation_ids = PackedStringArray([id])
	return p

var _default: AiShapedFormation
