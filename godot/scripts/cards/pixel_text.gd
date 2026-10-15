class_name PixelText
## The 3x5 pixel font used on cards. Atlas assets/font/pixel.png, characters in assets/font/chars.txt (same order as the atlas).
## Call from any CanvasItem's _draw():  PixelText.draw(self, Vector2(5, 5), "HELLO", Color.WHITE, 2)

static var _atlas: Texture2D
static var _chars := ""

static func _load() -> void:
	if _atlas != null and _chars != "": return
	_atlas = Data.tex("font/pixel.png")
	var p := "res://assets/font/chars.txt"
	if FileAccess.file_exists(p): _chars = FileAccess.get_file_as_string(p)

static func width(s: String, k := 1) -> int:
	return maxi(0, s.length() * 4 * k - k)

## draws s with its top-left at pos; returns the x after the last glyph
static func draw(ci: CanvasItem, pos: Vector2, s: String, col: Color, k := 1) -> float:
	_load()
	if _atlas == null: return pos.x
	var cols := int(Data.rules.get("font_columns", 16))
	var x := pos.x
	for ch in s.to_upper():
		var i := _chars.find(ch)
		if i >= 0 and ch != " ":
			var src := Rect2((i % cols) * 4, (i / cols) * 6, 4, 6)
			ci.draw_texture_rect_region(_atlas, Rect2(Vector2(x, pos.y), Vector2(4 * k, 6 * k)), src, col)
		x += 4 * k
	return x

static func rect(ci: CanvasItem, r: Rect2, col: Color) -> void:
	ci.draw_rect(r, col)
