class_name MatchCommand
extends RefCounted
## The "current command": the one thing the human is doing right now (a pass being lined up, a through ball, a shot, a run, a card, a team stance).
## It is the state store the HUD box shows; MatchControls writes it while you drag, MatchOrders / MatchCards write it when an order is given, anything can read it.
## A command with hold > 0 clears itself after that many seconds (the order just given); hold 0 = live, stays until replaced or cleared (the drag in progress).
## Kinds are free text; the HUD colours the known ones: pass, through, lob, shoot, run, press, tackle, card, team.

signal changed

var kind := ""
var text := ""                  ## big line in the box, e.g. "THROUGH"
var note := ""                  ## small line: the hint or detail
var who: Footballer             ## the player the command is for (the carrier, the runner)
var target: Footballer          ## the team mate it is aimed at (highlighted on the pitch)
var time_left := 0.0

func show(new_kind: String, new_text: String, new_who: Footballer = null, new_target: Footballer = null, new_note := "", hold := 0.0) -> void:
	if kind == new_kind and text == new_text and who == new_who and target == new_target and note == new_note and time_left == hold: return
	kind = new_kind
	text = new_text
	who = new_who
	target = new_target
	note = new_note
	time_left = hold
	changed.emit()

func clear() -> void:
	if kind == "" and time_left == 0.0: return
	kind = ""
	text = ""
	note = ""
	who = null
	target = null
	time_left = 0.0
	changed.emit()

## live = still being lined up (not yet given)
func is_live() -> bool:
	return kind != "" and time_left <= 0.0

func tick(dt: float) -> void:
	if time_left > 0.0:
		time_left -= dt
		if time_left <= 0.0: clear()
