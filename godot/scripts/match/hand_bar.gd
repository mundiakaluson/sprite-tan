@tool
class_name HandBar
extends HBoxContainer
## The row of skill-card slots. Each child is a slot (Control) holding one SkillCard, so you can see, select and move everything in the scene tree.
## Resize / move this node (it sits inside HandPanel) and the cards follow: they are centred in its rectangle. Add or delete slots to change the most cards the hand can show.
## `card_scale`: 1 = the full 64 x 90 card pixel for pixel; 1.5 is bigger but a touch uneven; 2 is exact (needs a tall strip).
## In the game the HUD fills the slots with the cards in the hand and hides the unused ones. In the editor the slots show sample cards.

@export_range(0.5, 2.0, 0.25) var card_scale := 1.5:
	set(v):
		card_scale = v
		refit()

func _init() -> void:
	alignment = BoxContainer.ALIGNMENT_CENTER
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _ready() -> void:
	refit()

func card_size() -> Vector2:
	return Vector2(64, 90) * card_scale

## the cards of the slots, in order
func cards() -> Array[SkillCard]:
	var out: Array[SkillCard] = []
	for s in get_children():
		for c in s.get_children():
			if c is SkillCard: out.append(c)
	return out

## sizes every slot and card to card_scale
func refit() -> void:
	for s in get_children():
		var slot := s as Control
		if slot == null: continue
		slot.custom_minimum_size = card_size()
		slot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		slot.mouse_filter = Control.MOUSE_FILTER_IGNORE
		for c in slot.get_children():
			if c is SkillCard:
				c.position = Vector2.ZERO
				c.scale = Vector2.ONE * card_scale
