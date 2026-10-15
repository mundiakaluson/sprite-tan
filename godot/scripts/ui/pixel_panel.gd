@tool
class_name PixelPanel
extends Control
## A HUD panel in the card language: dark field, 1 px frame with cut corners. `accent` tints the frame (team colour, command colour, ...).
## Needs assets/ui/panel.png (Export to game > HUD art). Put other pixel nodes inside it.

@export var accent := PixelUi.STEEL:
	set(v):
		accent = v
		queue_redraw()

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func _draw() -> void:
	PixelUi.nine(self, Rect2(Vector2.ZERO, size), PixelUi.tex("panel"), accent)
