@tool
class_name HandBar
extends Control
## Holds the skill-card slots (Slot1.. each a Control with a SkillCard inside). NOTHING is laid out by code: move, resize and scale the slots and cards in the scene
## (cards: select a Card, set Scale; slots: drag them) and the game uses exactly that. The game only fills the slots with the hand and hides the unused ones.

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

## the cards of the slots, in order
func cards() -> Array[SkillCard]:
	var out: Array[SkillCard] = []
	for s in get_children():
		for c in s.get_children():
			if c is SkillCard: out.append(c)
	return out
