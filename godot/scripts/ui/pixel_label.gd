@tool
class_name PixelLabel
extends Control
## Text in the 3x5 pixel font of the cards (PixelText). Upper case only. `text_scale` 1 = 4x6 px glyphs, 2 = chunky; keep it a whole number so the pixels stay square.
## Colour with `color` (or modulate). `wrap` breaks lines on spaces to fit the width; `shadow` draws a dark copy one pixel down-right.

@export var text := "":
	set(v):
		text = v
		queue_redraw()
		update_minimum_size()
@export var color := Color.WHITE:
	set(v):
		color = v
		queue_redraw()
@export_range(1, 6) var text_scale := 1:
	set(v):
		text_scale = v
		queue_redraw()
		update_minimum_size()
@export_enum("Left", "Center", "Right") var align := 0:
	set(v):
		align = v
		queue_redraw()
@export var wrap := false:
	set(v):
		wrap = v
		queue_redraw()
@export var shadow := true:
	set(v):
		shadow = v
		queue_redraw()

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func _get_minimum_size() -> Vector2:
	if wrap: return Vector2.ZERO
	return Vector2(PixelText.width(text, text_scale), 6 * text_scale)

func _lines() -> Array:
	var out: Array = []
	for para in text.split("\n"):
		if not wrap:
			out.append(para)
			continue
		var max_chars := maxi(1, int((size.x + text_scale) / (4.0 * text_scale)))
		var line := ""
		for word in para.split(" "):
			if line == "": line = word
			elif line.length() + 1 + word.length() <= max_chars: line += " " + word
			else:
				out.append(line)
				line = word
		out.append(line)
	return out

func _draw() -> void:
	var y := 0.0
	for line in _lines():
		var w := PixelText.width(line, text_scale)
		var x := 0.0
		if align == 1: x = floorf((size.x - w) / 2.0)
		elif align == 2: x = size.x - w
		if shadow: PixelText.draw(self, Vector2(x + text_scale, y + text_scale), line, Color(0, 0, 0, 0.85 * color.a), text_scale)
		PixelText.draw(self, Vector2(x, y), line, color, text_scale)
		y += 8.0 * text_scale
