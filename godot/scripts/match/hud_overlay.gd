class_name HudOverlay
extends Control
## Drawn over the pitch by the HUD: the selection ring, the aim line, the drag arrow and the rings on the command's target / the snapped team mate. Reads MatchHud.

var hud: MatchHud

func _process(_dt: float) -> void:
	queue_redraw()

func _ring(n: Node2D, col: Color, radius: float, text: String) -> void:
	var sc := n.scale.x
	draw_set_transform(n.position, 0.0, Vector2(1.0, 0.45))
	draw_arc(Vector2.ZERO, radius * sc, 0.0, TAU, 32, col, 2.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if text != "": draw_string(ThemeDB.fallback_font, n.position + Vector2(-9.0, -30.0 * sc), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, col)

func _draw() -> void:
	if hud == null: return
	var n: Node2D = hud.selected_node
	if n != null and is_instance_valid(n):
		var sc := n.scale.x
		draw_set_transform(n.position, 0.0, Vector2(1.0, 0.45))
		draw_arc(Vector2.ZERO, 12.0 * sc, 0.0, TAU, 32, Color(1.0, 0.9, 0.2), 2.0)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		if hud.aiming:
			draw_line(n.position, hud.aim_to, Color(1.0, 0.9, 0.3, 0.8), 1.5)
			draw_circle(hud.aim_to, 4.0, Color(1.0, 0.9, 0.3, 0.9))
	var cmd: MatchCommand = hud.command
	if cmd != null and cmd.target != null and cmd.target.node != null:
		_ring(cmd.target.node, MatchHud.KIND_COLORS.get(cmd.kind, Color.WHITE), 15.0, "RUN" if cmd.kind == "through" else "")
	if hud.snap_node != null and is_instance_valid(hud.snap_node):
		_ring(hud.snap_node, MatchHud.KIND_COLORS.get(hud.snap_kind, Color.WHITE), 17.0, "RUN" if hud.snap_kind == "through" else "")
	if hud.dragging:
		var d: Vector2 = hud.drag_to - hud.drag_from
		var col := Color(1.0, 0.35, 0.3, 0.95) if hud.drag_shot else Color(1, 1, 1, 0.95)
		draw_line(hud.drag_from, hud.drag_to, col, 2.0)
		if d.length() > 6.0:
			var u := d.normalized()
			var side := Vector2(-u.y, u.x)
			draw_colored_polygon(PackedVector2Array([hud.drag_to, hud.drag_to - u * 9.0 + side * 5.0, hud.drag_to - u * 9.0 - side * 5.0]), col)

