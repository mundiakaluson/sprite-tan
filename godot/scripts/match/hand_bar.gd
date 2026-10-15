@tool
class_name HandBar
extends HBoxContainer
## The row the skill cards are added to. Resize / move it in the HUD scene (it sits inside HandPanel) and the cards follow: they are centred in this rectangle.
## In the editor it draws `placeholder_count` empty card outlines at the right size, so you can see where the real cards will land. Nothing is drawn in the game.

## 1 = the full 64 x 90 card pixel for pixel; 1.5 is bigger but a touch uneven; 2 is exact (needs a tall strip)
@export_range(0.5, 2.0, 0.25) var card_scale := 1.5:
	set(v):
		card_scale = v
		queue_redraw()
@export_range(0, 12) var placeholder_count := 8:
	set(v):
		placeholder_count = v
		queue_redraw()

func _init() -> void:
	alignment = BoxContainer.ALIGNMENT_CENTER
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func card_size() -> Vector2:
	return Vector2(64, 90) * card_scale

func _draw() -> void:
	if not Engine.is_editor_hint() or get_child_count() > 0: return
	var cs := card_size()
	var gap := float(get_theme_constant("separation"))
	var total := placeholder_count * cs.x + maxi(0, placeholder_count - 1) * gap
	var x0 := floorf((size.x - total) / 2.0)
	var y0 := floorf((size.y - cs.y) / 2.0)
	for i in placeholder_count:
		var r := Rect2(x0 + i * (cs.x + gap), y0, cs.x, cs.y)
		draw_rect(r, Color(0.3, 0.5, 0.9, 0.12))
		draw_rect(r, Color(0.5, 0.7, 1.0, 0.8), false)
