class_name AiProfile
extends Resource
## How a team plays: one AiRole resource per role. Open scenes/ai/profile_default.tres and edit every number in the inspector. Give the home and away team
## different profiles (MatchSettings > AI) to try styles against each other; duplicate the .tres to keep presets. A missing role falls back to its defaults.

@export var goalkeeper: AiGk
@export var centre_back: AiCb
## left back, right back and the wingbacks of a back three / five
@export var fullback: AiFullback
@export var holding_midfielder: AiCdm
@export var central_midfielder: AiCm
@export var attacking_midfielder: AiCam
## left and right wing, and the wide midfielders
@export var winger: AiWinger
@export var striker: AiSt


## fills every empty slot with that role's defaults (so a half-made profile still plays)
@export_group("Formations")
## team play per formation (4-4-2 here: banks, press triggers, who drops, overlaps). A role follows its formation's file first, then its own AI.
@export var formations: Array[AiFormation] = []

func formation_for(id: String) -> AiFormation:
	for x in formations:
		if x != null and id in x.formation_ids: return x
	return null

func fill() -> AiProfile:
	if formations.is_empty():
		var x := Ai442.new()
		x.formation_ids = PackedStringArray(["F01"])
		formations.append(x)
	if goalkeeper == null: goalkeeper = AiGk.new()
	if centre_back == null: centre_back = AiCb.new()
	if fullback == null: fullback = AiFullback.new()
	if holding_midfielder == null: holding_midfielder = AiCdm.new()
	if central_midfielder == null: central_midfielder = AiCm.new()
	if attacking_midfielder == null: attacking_midfielder = AiCam.new()
	if winger == null: winger = AiWinger.new()
	if striker == null: striker = AiSt.new()
	return self

func role_for(role: String) -> AiRole:
	match role:
		"GK": return goalkeeper
		"CB": return centre_back
		"LB", "RB": return fullback
		"CDM": return holding_midfielder
		"CAM": return attacking_midfielder
		"LW", "RW": return winger
		"ST": return striker
		_: return central_midfielder
