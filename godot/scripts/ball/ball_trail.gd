class_name BallTrail
extends Node2D
## A short fading trail behind a fast ball, so the bend of a finesse / trivela / flat bender and the skip of a low drive can be seen.
## Lives in the stadium's Actors layer at (0, 0) (screen coordinates); keeps the last `seconds` of the ball's 3D positions and projects them every frame.
## Numbers: MatchSettings > Ball trail.

var ball: Ball
var camera: Camera3D
var settings: MatchSettings
var _pts: Array = []          ## [Vector3 world position, age s]

func setup(b: Ball, cam: Camera3D, s: MatchSettings) -> void:
	ball = b
	camera = cam
	settings = s
	z_index = 3990

func _process(dt: float) -> void:
	if ball == null or camera == null or settings == null: return
	for p in _pts: p[1] += dt
	while not _pts.is_empty() and _pts[0][1] > settings.trail_seconds: _pts.pop_front()
	var v := ball.phys.vel
	var spin_kick := absf(Data.num(Data.row("kick_styles", ball.style).get("side"), 0.0)) > 0.0 or ball.style == "K09"
	var on := settings.trail_enabled and ball.live and v.length() >= (settings.trail_min_speed_spin if spin_kick else settings.trail_min_speed)
	if on: _pts.append([ball.world_pos(), 0.0])
	elif not _pts.is_empty() and _pts[-1][1] > 0.0 and not ball.live: _pts.clear()
	queue_redraw()

func _draw() -> void:
	if _pts.size() < 2: return
	var col := settings.trail_color
	var prev := Vector2.INF
	for i in _pts.size():
		var w: Vector3 = _pts[i][0]
		if camera.is_position_behind(w):
			prev = Vector2.INF
			continue
		var p := camera.unproject_position(w)
		if prev != Vector2.INF:
			var a := 1.0 - float(_pts[i][1]) / maxf(settings.trail_seconds, 0.01)
			draw_line(prev, p, Color(col, col.a * a * a), lerpf(1.0, settings.trail_width, a))
		prev = p
