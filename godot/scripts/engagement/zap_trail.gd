@tool
class_name ZapTrail
extends Node2D
## The zap path: a thin bolt that runs along a zig-zag path on the grass and leaves a faint crackling charge that fizzles out.
## Lives in the stadium's Actors layer at (0, 0) like BallTrail (screen coordinates; the path is kept in world metres and projected every frame).
## Animation "zap" (edit it in the Animation panel): `head` 0 -> 1 = how far along the path the zap is (the player rides it: DoubleTeam reads `head`),
## then `charge` 1 -> 0 = the crackle on the grass fizzling out. The node frees itself when the animation ends.
## In the editor (no camera) it draws a sample path so the animation can be previewed.

@export_range(0.0, 1.0) var head := 1.0:
	set(v):
		head = v
		queue_redraw()
@export_range(0.0, 1.0) var charge := 1.0:
	set(v):
		charge = v
		queue_redraw()
@export var color := Color(0.35, 0.82, 1.0)
## the bolt at the head (px) and the crackle left behind
@export var bolt_width := 2.0
@export var crackle_width := 1.0
## how much of the path the head bolt covers (0..1 of the path)
@export var bolt_length := 0.2
## piece length (px) and the share of pieces that crackle at full charge
@export var crackle_step := 7.0
@export_range(0.0, 1.0) var crackle_share := 0.3
@export var jitter := 1.5
## the faint scorch line under it (alpha at full charge)
@export_range(0.0, 1.0) var scorch_alpha := 0.25

var camera: Camera3D
var path: PackedVector3Array = PackedVector3Array()
var _seed := 0

func _ready() -> void:
	z_index = -3990
	if not Engine.is_editor_hint(): $AnimationPlayer.animation_finished.connect(func(_n): queue_free())

func start() -> void:
	$AnimationPlayer.play("zap")

func _process(_dt: float) -> void:
	_seed += 1
	queue_redraw()

## the point and direction (world) at fraction t of the path
func point_at(t: float) -> Vector3:
	if path.size() < 2: return Vector3.ZERO
	var total := 0.0
	for i in path.size() - 1: total += path[i].distance_to(path[i + 1])
	var want := clampf(t, 0.0, 1.0) * total
	for i in path.size() - 1:
		var l := path[i].distance_to(path[i + 1])
		if want <= l or i == path.size() - 2: return path[i].lerp(path[i + 1], 0.0 if l < 0.0001 else clampf(want / l, 0.0, 1.0))
		want -= l
	return path[path.size() - 1]

func _screen() -> PackedVector2Array:
	var out := PackedVector2Array()
	if camera == null or path.size() < 2:
		for i in 6: out.append(Vector2(i * 40.0, (12.0 if i % 2 else -12.0) * (0.0 if i == 0 or i == 5 else 1.0)))      # editor sample
		return out
	for w in path:
		if camera.is_position_behind(w): return PackedVector2Array()
		out.append(camera.unproject_position(w))
	return out

## the screen polyline cut at fractions a..b
func _cut(pts: PackedVector2Array, a: float, b: float) -> PackedVector2Array:
	var lens: Array[float] = []
	var total := 0.0
	for i in pts.size() - 1:
		lens.append(pts[i].distance_to(pts[i + 1]))
		total += lens[i]
	var out := PackedVector2Array()
	var s := 0.0
	for i in pts.size() - 1:
		var l := lens[i]
		var t0 := clampf((a * total - s) / maxf(l, 0.0001), 0.0, 1.0)
		var t1 := clampf((b * total - s) / maxf(l, 0.0001), 0.0, 1.0)
		if t1 > t0:
			if out.is_empty(): out.append(pts[i].lerp(pts[i + 1], t0))
			out.append(pts[i].lerp(pts[i + 1], t1))
		s += l
	return out

func _draw() -> void:
	var pts := _screen()
	if pts.size() < 2: return
	var rng := RandomNumberGenerator.new()
	rng.seed = _seed
	var done := _cut(pts, 0.0, head)
	if done.size() >= 2 and charge > 0.0:
		draw_polyline(done, Color(color.darkened(0.6), scorch_alpha * charge), 1.0)
		for i in done.size() - 1:                                                   # the crackle: short jagged bits that flicker
			var a := done[i]
			var b := done[i + 1]
			var n := maxi(1, int(a.distance_to(b) / crackle_step))
			for k in n:
				if rng.randf() > crackle_share * charge: continue
				var p0 := a.lerp(b, float(k) / n)
				var p1 := a.lerp(b, float(k + 1) / n)
				var mid := (p0 + p1) * 0.5 + Vector2(rng.randf_range(-jitter, jitter), rng.randf_range(-jitter, jitter))
				draw_polyline(PackedVector2Array([p0, mid, p1]), Color(color, 0.6 * charge), crackle_width)
	if head > 0.0 and head < 1.0:                                                  # the bolt at the head
		var bolt := _cut(pts, maxf(0.0, head - bolt_length), head)
		if bolt.size() >= 2:
			var jag := PackedVector2Array()
			for i in bolt.size():
				jag.append(bolt[i] + (Vector2.ZERO if i == bolt.size() - 1 else Vector2(rng.randf_range(-2, 2), rng.randf_range(-2, 2))))
			for i in jag.size(): jag[i] += Vector2(0, -8)                          # at waist height
			draw_polyline(jag, Color(color, 0.7), bolt_width)
			draw_polyline(jag, Color(1, 1, 1, 0.6), 1.0)
