@tool
class_name StanceGrid
extends GridContainer
## Holds the team stance buttons (they are created from the AI profile when the match starts). Move / resize it in the HUD scene; set `button_size` here to size them.
## In the editor it draws `placeholder_count` empty buttons so you can see the layout. Nothing is drawn in the game.

@export var button_size := Vector2(112, 20):
	set(v):
		button_size = v
		queue_redraw()
@export_range(0, 12) var placeholder_count := 6:
	set(v):
		placeholder_count = v
		queue_redraw()

func _draw() -> void:
	if not Engine.is_editor_hint() or get_child_count() > 0: return
	var hs := float(get_theme_constant("h_separation"))
	var vs := float(get_theme_constant("v_separation"))
	for i in placeholder_count:
		var r := Rect2((i % columns) * (button_size.x + hs), (i / columns) * (button_size.y + vs), button_size.x, button_size.y)
		draw_rect(r, Color(0.9, 0.3, 0.3, 0.12))
		draw_rect(r, Color(1.0, 0.5, 0.5, 0.8), false)
