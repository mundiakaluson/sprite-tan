class_name TeamStance
extends Resource
## How a whole team plays right now: the HUD's TEAM buttons (and the AI's auto rules) pick one. A stance never replaces the formation: it ADDS to the formation's
## numbers (data/formations.csv: line height, width, compactness, press, overlap, directness, counter, risk, all 0..1) and nudges the formation file (block depth, pressing).
## So the team always organises itself inside its formation: "auto" = the formation as designed, the others lean it towards pressing, a low block, etc.
## Edit them in the inspector: scenes/ai/profile_default.tres > Stances. A formation file reads block_shift / press_always / press_never; roles read push_scale.

## id used by the buttons and Team.stance_id ("auto" must exist)
@export var id := "auto"
@export var label := "AUTO"
## what the button's tooltip / the command box says
@export var note := "Play the formation as designed"

@export_group("Added to the formation's numbers")
@export_range(-1.0, 1.0) var d_line_height := 0.0
@export_range(-1.0, 1.0) var d_width := 0.0
@export_range(-1.0, 1.0) var d_compactness := 0.0
@export_range(-1.0, 1.0) var d_press := 0.0
@export_range(-1.0, 1.0) var d_overlap := 0.0
@export_range(-1.0, 1.0) var d_directness := 0.0
@export_range(-1.0, 1.0) var d_counter := 0.0
@export_range(-1.0, 1.0) var d_risk := 0.0

@export_group("Block and pressing")
## the whole defensive block moves this many metres up (+) or back (-) the pitch
@export var block_shift := 0.0
## multiplies how far the team pushes up with the ball (Team shape in MatchSettings)
@export_range(0.0, 2.0) var push_scale := 1.0
## close down the carrier whenever he is in reach, trigger or not
@export var press_always := false
## never leave the block to close down: stand off and contain
@export var press_never := false

func delta(key: String) -> float:
	match key:
		"line_height": return d_line_height
		"width": return d_width
		"compactness": return d_compactness
		"press": return d_press
		"overlap": return d_overlap
		"directness": return d_directness
		"counter": return d_counter
		"risk": return d_risk
	return 0.0

static func make(sid: String, lab: String, text: String, values := {}) -> TeamStance:
	var s := TeamStance.new()
	s.id = sid
	s.label = lab
	s.note = text
	for k in values: s.set(k, values[k])
	return s

## the stances every profile starts with
static func defaults() -> Array[TeamStance]:
	var out: Array[TeamStance] = []
	out.append(make("auto", "AUTO", "Play the formation as designed"))
	out.append(make("press_high", "PRESS HIGH", "Squeeze them high up the pitch", {"d_press": 0.35, "d_line_height": 0.2, "d_compactness": 0.1, "block_shift": 8.0, "push_scale": 1.2, "press_always": true}))
	out.append(make("mid_block", "MID BLOCK", "Two compact banks, press on triggers", {"d_line_height": -0.05, "d_compactness": 0.1}))
	out.append(make("park_bus", "PARK BUS", "Drop deep, stay narrow, do not chase", {"d_line_height": -0.35, "d_press": -0.4, "d_compactness": 0.25, "d_width": -0.15, "d_counter": 0.2, "block_shift": -14.0, "push_scale": 0.4, "press_never": true}))
	out.append(make("push_up", "PUSH UP", "Everyone forward, full backs overlap", {"d_line_height": 0.25, "d_overlap": 0.25, "d_risk": 0.15, "block_shift": 6.0, "push_scale": 1.5}))
	out.append(make("counter", "COUNTER", "Sit back, win it, go long and quick", {"d_line_height": -0.15, "d_counter": 0.3, "d_directness": 0.3, "d_press": -0.15, "block_shift": -6.0, "push_scale": 0.8}))
	return out
