class_name PlayerTip
extends Control
## Hover tooltip with every stat, drawn live from the row (no image per player).

var p := {}
const W := 148

func show_player(row: Dictionary) -> void:
	p = row
	var stats: Array = Data.rules.get("gk_stats", []) if p.get("role", "") == "GK" else Data.rules.get("out_stats", [])
	size = Vector2(W, 8 + 7 + 8 + stats.size() * 7 + 4 + 7 + 8)
	custom_minimum_size = size
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	queue_redraw()

func _draw() -> void:
	if p.is_empty() or Data.rules.is_empty(): return
	var rc: Dictionary = Data.rules["rarity_colours"].get(p.get("rarity", "COMMON"), Data.rules["rarity_colours"]["COMMON"])
	var main := PlayerCard.col(rc["main"]); var light := PlayerCard.col(rc["light"])
	var stats: Array = Data.rules.get("gk_stats", []) if p.get("role", "") == "GK" else Data.rules.get("out_stats", [])
	var sc := PlayerCard.col(Data.rules.get("stat_colour", [110, 214, 140]))
	draw_rect(Rect2(Vector2.ZERO, size), PlayerCard.col(Data.rules["ink"]))
	draw_rect(Rect2(Vector2(1, 1), size - Vector2(2, 2)), main)
	draw_rect(Rect2(Vector2(2, 2), size - Vector2(4, 4)), PlayerCard.col(Data.rules["panel"]))
	PixelText.draw(self, Vector2(6, 6), str(p.get("name", "")).to_upper(), light)
	PixelText.draw(self, Vector2(6, 13), "%s  %s  RATING %s" % [p.get("rarity", ""), p.get("role", ""), p.get("rating", "")], Color8(150, 156, 190))
	var y := 22
	for k in stats:
		var v := Data.inum(p.get(k))
		PixelText.draw(self, Vector2(6, y), k, Color8(170, 176, 208))
		PixelText.draw(self, Vector2(30, y), str(v), sc)
		draw_rect(Rect2(44, y + 1, W - 52, 3), Color8(48, 48, 70))
		draw_rect(Rect2(44, y + 1, int((W - 52) * v / 100.0), 3), sc)
		y += 7
	y += 3
	var roles: String = p.get("roles", "")
	if roles == "": roles = p.get("role", "")
	PixelText.draw(self, Vector2(6, y), "PLAYS " + roles.replace("|", " "), Color8(235, 238, 250))
