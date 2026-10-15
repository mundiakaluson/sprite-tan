@tool
class_name PixelImage
extends Control
## Draws one exported image (res://assets/<texture_path>) 1:1, nearest filtered, tiled to fill its rectangle. Used for the HUD strip. Blank until the export has run.

@export var texture_path := "ui/strip.png":
	set(v):
		texture_path = v
		queue_redraw()

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func _draw() -> void:
	var t := Data.tex(texture_path)
	if t != null: draw_texture_rect(t, Rect2(Vector2.ZERO, size), true)
