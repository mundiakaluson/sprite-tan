@tool
class_name PlayerCard
extends Control
## A player card built live: shared layers (background, outline), the player's small face, and text/stats drawn from the CSV row.
## One face image per player is the only per-player art. Change a stat in players.csv and the card is right with no re-export.
## usage: var c := PlayerCard.new(); add_child(c); c.show_player(Data.row("players", "PL242")); c.scale = Vector2(3, 3)

## which player to show in the editor (and as the default in game). In game call show_player(row) instead.
@export var player_id := "PL242":
	set(v):
		player_id = v
		_load_preview()

var p := {}
var _fx := 0.0

func _init() -> void:
	custom_minimum_size = Vector2(64, 90)
	size = Vector2(64, 90)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func _ready() -> void:
	_load_preview()

func _load_preview() -> void:
	if not is_inside_tree() and not Engine.is_editor_hint(): return
	if not Data.ok: Data.reload()
	if Data.ok and player_id != "": show_player(Data.row("players", player_id))
	else: queue_redraw()

func show_player(row: Dictionary) -> void:
	p = row
	queue_redraw()

func is_special() -> bool:
	return str(p.get("special", "0")) in ["1", "True", "true"] and Data.rules.get("foil_by_rarity", {}).has(p.get("rarity", ""))

func _process(delta: float) -> void:
	if is_special():
		_fx = fposmod(_fx + delta / 3.0, 1.0)   # 3 second loop, the shimmer is the first part of it
		queue_redraw()

static func col(a) -> Color:
	return Color8(int(a[0]), int(a[1]), int(a[2]))

## the three stats that matter most for the role: [[key, value], ...]
static func key_stats(pl: Dictionary) -> Array:
	var gk: bool = pl.get("role", "") == "GK"
	var keys: Array = Data.rules.get("gk_stats", []) if gk else Data.rules.get("out_stats", [])
	if gk:
		var out := []
		for k in keys: out.append([k, Data.inum(pl.get(k))])
		return out
	var w: Array = Data.rules.get("rating_w", {}).get(pl.get("role", ""), [1, 1, 1, 1, 1, 1])
	var idx := range(keys.size())
	idx.sort_custom(func(a, b):
		if w[a] != w[b]: return w[a] > w[b]
		var va := Data.inum(pl.get(keys[a])); var vb := Data.inum(pl.get(keys[b]))
		if va != vb: return va > vb
		return a < b)
	var out2 := []
	for i in idx.slice(0, 3): out2.append([keys[i], Data.inum(pl.get(keys[i]))])
	return out2

const PARTICLES := ["van", "de", "dos", "da", "di", "del", "der", "den", "al", "el", "le", "la", "ter", "von", "bin"]

static func surname(nm: String) -> String:
	var w := nm.split(" ", false)
	if w.size() < 2: return nm.to_upper()
	if w[w.size() - 2].to_lower() in PARTICLES: return (w[w.size() - 2] + " " + w[w.size() - 1]).to_upper()
	return w[w.size() - 1].to_upper()

func _draw() -> void:
	if p.is_empty() or Data.rules.is_empty():
		draw_rect(Rect2(0, 0, 64, 90), Color(0.1, 0.1, 0.16))
		draw_string(ThemeDB.fallback_font, Vector2(6, 46), "no data", HORIZONTAL_ALIGNMENT_LEFT, 52, 10, Color.WHITE)
		draw_string(ThemeDB.fallback_font, Vector2(6, 58), "press Export", HORIZONTAL_ALIGNMENT_LEFT, 56, 8, Color(0.7, 0.7, 0.8))
		return
	var rar: String = p.get("rarity", "COMMON")
	var rc: Dictionary = Data.rules["rarity_colours"][rar]
	var main := col(rc["main"]); var dark := col(rc["dark"]); var light := col(rc["light"])
	var special := is_special()
	var edge := light if rar == "LEGEND" else main
	var lower := rar.to_lower()
	if special:
		var style: String = Data.rules["foil_by_rarity"][rar]
		var strip := Data.tex("card/foil_%s.png" % style)
		var n := int(Data.rules.get("foil_frames", 36))
		var shim := float(Data.rules.get("foil_shimmer", 0.3))
		# frame number inside the loop (the strip animates the shimmer in its first part, stills afterwards)
		var f := int(_fx * n) % n
		if strip != null: draw_texture_rect_region(strip, Rect2(0, 0, 64, 90), Rect2(f * 64, 0, 64, 90))
	else:
		var bg := Data.tex("card/bg_%s.png" % lower)
		if bg != null: draw_texture(bg, Vector2.ZERO)
	var fo: Array = Data.rules.get("face_offset", [11, 21])
	var face := Data.tex("faces/%s.png" % p.get("id", ""))
	if face != null: draw_texture(face, Vector2(fo[0], fo[1]))
	if not special:
		var top := Data.tex("card/top_%s.png" % lower)
		if top != null: draw_texture(top, Vector2.ZERO)
	var white := Color.WHITE
	PixelText.draw(self, Vector2(5, 5), str(p.get("rating", "")), white, 2)
	var role: String = p.get("role", "")
	PixelText.draw(self, Vector2(5, 18), role, light)
	draw_line(Vector2(5, 25.5), Vector2(5 + maxi(PixelText.width(role), 10), 25.5), main)
	var rn := rar
	var rw := PixelText.width(rn)
	PixelText.draw(self, Vector2(64 - 5 - rw, 5), rn, light)
	var nm := surname(p.get("name", ""))
	var ww := PixelText.width(nm)
	PixelText.draw(self, Vector2((64 - ww) / 2, 63), nm, white)
	draw_line(Vector2(5, 66.5), Vector2(32 - ww / 2 - 3, 66.5), dark)
	draw_line(Vector2(32 + ww / 2 + 3, 66.5), Vector2(58, 66.5), dark)
	draw_line(Vector2(26, 70.5), Vector2(37, 70.5), edge)
	var ks := key_stats(p)
	for ci in ks.size():
		var x0 := 4 + ci * 19
		var cxm := x0 + 9
		var k: String = ks[ci][0]
		var v: int = ks[ci][1]
		PixelText.draw(self, Vector2(cxm - PixelText.width(k) / 2, 76), k, Color8(140, 146, 176))
		PixelText.draw(self, Vector2(cxm - PixelText.width(str(v)) / 2, 82), str(v), white)
		if ci > 0: draw_line(Vector2(x0 - 1, 76.5), Vector2(x0 - 1, 86.5), dark)
		draw_line(Vector2(x0 + 3, 87.5), Vector2(x0 + 3 + int(12 * v / 100.0), 87.5), main)
