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
@export_group("Stances")
## team commands (HUD TEAM buttons): each one nudges the formation. "auto" must exist
@export var stances: Array[TeamStance] = []
## "auto" switches stance by itself: protect a lead late on, press when behind
@export var park_after_minute := 80.0
@export var park_lead := 1
@export var park_stance := "park_bus"
@export var press_after_minute := 60.0
@export var press_deficit := 1
@export var press_stance := "press_high"

@export_group("Interact")
## team interaction: cover for a defender who steps out, the striker looking for space when a midfielder presses, player traits (roamer)
@export var interact: AiInteract

@export_group("Line")
## the back line as one unit (step up / drop / offside trap) and forwards staying onside (scenes/ai/line.tres)
@export var line: AiLine

@export_group("Transition")
## counter-press, recovery runs, rest defence, counter-attacks (scenes/ai/transition.tres)
@export var transition: AiTransition

@export_group("Box")
## box zones when the ball is wide: runners to near post / far post / spot / cut-back / edge, and defending the box (scenes/ai/box.tres)
@export var box: AiBox

@export_group("Set pieces")
## who stands where at corners, free kicks (the wall), goal kicks, throw-ins and penalties (scenes/ai/set_piece.tres)
@export var set_piece: AiSetPiece

@export_group("Scan")
## scanning before receiving, open body shape, first touch away from pressure (scenes/ai/scan.tres)
@export var scan: AiScan

@export_group("Behaviours")
## every script in scripts/ai/behaviours/ is used automatically (see ai_behaviour.gd). Add an entry here only to give THIS team its own copy of one (different numbers, or switched off):
## it replaces the automatic one of the same script. Entries of other scripts are added to the list.
@export var behaviours: Array[AiBehaviour] = []
var _all: Array[AiBehaviour] = []
var _all_ready := false

## the behaviours this team uses: the automatic ones (replaced by this profile's own copy of the same script), plus the extra entries
func all_behaviours() -> Array[AiBehaviour]:
	if _all_ready: return _all
	_all_ready = true
	for b in AiBehaviour.discover():
		var mine: AiBehaviour = null
		for e in behaviours:
			if e != null and e.get_script() == b.get_script(): mine = e
		_all.append(mine if mine != null else b)
	for e in behaviours:
		if e != null and not _all.has(e): _all.append(e)
	_all.sort_custom(AiBehaviour.before)
	return _all

@export_group("Formations")
## team play per formation (4-4-2 here: banks, press triggers, who drops, overlaps). A role follows its formation's file first, then its own AI.
@export var formations: Array[AiFormation] = []

func formation_for(id: String) -> AiFormation:
	for x in formations:
		if x != null and id in x.formation_ids: return x
	var lay := MatchSettings.layout(id)          # a formation made in the inspector (MatchSettings > Custom Formations)
	if lay != null: return lay.play_for()
	return null

func stance_for(id: String) -> TeamStance:
	for s in stances:
		if s != null and s.id == id: return s
	for s in stances:
		if s != null and s.id == "auto": return s
	return stances[0]

## what "auto" turns into: minute (0-90) and goal difference (ours minus theirs)
func auto_stance_id(minute: float, diff: int) -> String:
	if diff >= park_lead and minute >= park_after_minute: return park_stance
	if diff <= -press_deficit and minute >= press_after_minute: return press_stance
	return "auto"

func fill() -> AiProfile:
	if stances.is_empty(): stances = TeamStance.defaults()
	if formations.is_empty():
		var x := Ai442.new()
		x.formation_ids = PackedStringArray(["F01"])
		formations.append(x)
	if interact == null: interact = AiInteract.new()
	interact.fill()
	if line == null: line = AiLine.new()
	if transition == null: transition = AiTransition.new()
	if scan == null: scan = AiScan.new()
	if box == null: box = AiBox.new()
	if set_piece == null: set_piece = AiSetPiece.new()
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
