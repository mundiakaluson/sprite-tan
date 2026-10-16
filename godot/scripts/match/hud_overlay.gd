class_name HudOverlay
extends Control
## Drawn over the pitch by the HUD: the selection ring, the aim line, the drag arrow and the rings on the command's target / the snapped team mate. Reads MatchHud.

var hud: MatchHud

func _init() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func _process(_dt: float) -> void:
	queue_redraw()

## a pixel ring (assets/ui/ring_select.png solid, ring_target.png dashed) under a player's feet, scaled with him; `text` is written above his head in the pixel font
func _ring(n: Node2D, col: Color, kind: String, text: String) -> void:
	var t := PixelUi.tex(kind)
	if t == null: return
	var sc := n.scale.x
	var sz := Vector2(roundf(t.get_width() * sc), roundf(t.get_height() * sc))
	draw_texture_rect(t, Rect2((n.position - sz / 2.0).round(), sz), false, col)
	if text != "": PixelText.draw(self, (n.position + Vector2(-PixelText.width(text) / 2.0, -32.0 * sc)).round(), text, col)

func _draw() -> void:
	if hud == null: return
	var n: Node2D = hud.selected_node
	if n != null and is_instance_valid(n):
		_ring(n, Color(1.0, 0.9, 0.2), "ring_select", "")
		if hud.aiming:
			draw_line(n.position, hud.aim_to, Color(1.0, 0.9, 0.3, 0.8), 1.5)
			draw_circle(hud.aim_to, 4.0, Color(1.0, 0.9, 0.3, 0.9))
	var cmd: MatchCommand = hud.command
	if cmd != null and cmd.target != null and cmd.target.node != null:
		_ring(cmd.target.node, MatchHud.KIND_COLORS.get(cmd.kind, Color.WHITE), "ring_target", "RUN" if cmd.kind == "through" else "")
	if hud.snap_node != null and is_instance_valid(hud.snap_node):
		_ring(hud.snap_node, MatchHud.KIND_COLORS.get(hud.snap_kind, Color.WHITE), "ring_target", "RUN" if hud.snap_kind == "through" else "")
	if hud.dragging:
		var d: Vector2 = hud.drag_to - hud.drag_from
		var col := Color(1.0, 0.35, 0.3, 0.95) if hud.drag_shot else Color(1, 1, 1, 0.95)
		var tip := hud.drag_to
		if hud.drag_path.size() >= 2:                                        # a bent pass: the line follows the curve
			draw_polyline(hud.drag_path, col, 2.0)
			tip = hud.drag_path[hud.drag_path.size() - 1]
			d = tip - hud.drag_path[maxi(0, hud.drag_path.size() - 3)]
			draw_line(tip, hud.drag_to, Color(col, 0.35), 1.0)
		else:
			draw_line(hud.drag_from, hud.drag_to, col, 2.0)
		if d.length() > 0.5:
			var u := d.normalized()
			var side := Vector2(-u.y, u.x)
			draw_colored_polygon(PackedVector2Array([tip, tip - u * 9.0 + side * 5.0, tip - u * 9.0 - side * 5.0]), col)

