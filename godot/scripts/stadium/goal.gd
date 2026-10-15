@tool
class_name Goal
extends Node3D
## A goal: posts, crossbar and a spring-mesh net that billows when the ball hits it, with posts and bar that wobble. Modular: pick a style (data/goals.csv; tune it in the
## manager tool's Goal simulator tab) or override single numbers in the inspector. Local space: +x points outward (behind the goal). Stadium rotates the left goal by 180 degrees.
##   goal.ball_update(ball.global_position, ball.velocity)  -> new ball velocity (call once per physics frame while the ball is near)
signal hit_net(point: Vector3)
signal hit_frame(part: String, point: Vector3)

@export var style_id := "G01":
	set(v):
		style_id = v
		if is_node_ready(): rebuild()
@export_group("Overrides (blank styles use data/goals.csv)")
@export var override_stiffness := -1.0      ## < 0 = use the style
@export var override_drag := -1.0
@export var override_post_sway := -1.0
@export var wear_override := -1.0            ## 0-100 net wear; < 0 = use the style (a stadium can have older nets)
@export var ball_radius := GoalNet.BALL_R

var net := GoalNet.new()
var style := {}
var _mesh := ImmediateMesh.new()
var _net_node: MeshInstance3D
var _left: MeshInstance3D
var _right: MeshInstance3D
var _bar: MeshInstance3D
var _ball_seen := false
var _local_ball := false

func _ready() -> void:
	rebuild()

func rebuild() -> void:
	for c in get_children(): c.queue_free()
	style = Data.row("goals", style_id)
	if style.is_empty():
		style = {"id": style_id}
		push_warning("Goal: style '%s' not found in goals.csv (run Export to game)" % style_id)
	if override_stiffness >= 0.0: style["stiffness"] = str(override_stiffness)
	if override_drag >= 0.0: style["drag"] = str(override_drag)
	if override_post_sway >= 0.0: style["post_sway"] = str(override_post_sway)
	net = GoalNet.new(); net.setup(style, wear_override)
	var pc := Color.html(str(style.get("post_color", "#f6f6f2"))); var nc := Color.html(str(style.get("net_color", "#f0f4f0")))
	nc.a = net.alpha / 255.0
	_left = _post(Vector3(0, net.h / 2.0, -net.hw), Vector3(net.pr * 2, net.h, net.pr * 2), pc)
	_right = _post(Vector3(0, net.h / 2.0, net.hw), Vector3(net.pr * 2, net.h, net.pr * 2), pc)
	_bar = _post(Vector3(0, net.h, 0), Vector3(net.pr * 2, net.pr * 2, net.hw * 2 + net.pr * 2), pc)
	var rp := net.pr * 0.8                                  # rear posts and top bar hold the net up
	_beam(Vector3(net.dep_low, 0, -net.hw), Vector3(net.dep, net.h, -net.hw), rp, pc); _beam(Vector3(net.dep_low, 0, net.hw), Vector3(net.dep, net.h, net.hw), rp, pc)
	_beam(Vector3(net.dep, net.h, -net.hw), Vector3(net.dep, net.h, net.hw), rp, pc)
	_net_node = MeshInstance3D.new(); _mesh = ImmediateMesh.new(); _net_node.mesh = _mesh
	var m := StandardMaterial3D.new(); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; m.albedo_color = nc; m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; m.cull_mode = BaseMaterial3D.CULL_DISABLED
	_net_node.material_override = m; add_child(_net_node)
	_draw_net()

func _post(at: Vector3, size: Vector3, col: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = size; mi.mesh = bm; mi.position = at
	var m := StandardMaterial3D.new(); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; m.albedo_color = col; mi.material_override = m
	add_child(mi)
	return mi

func _beam(a: Vector3, b: Vector3, r: float, col: Color) -> void:
	var dir := b - a
	var up := Vector3.RIGHT if absf(dir.normalized().y) > 0.99 else Vector3.UP
	var mi := _post((a + b) / 2.0, Vector3(r * 2.0, r * 2.0, dir.length()), col)
	mi.basis = Basis.looking_at(dir, up)

func _draw_net() -> void:
	_mesh.clear_surfaces()
	_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	for e in net.rest.size():
		_mesh.surface_add_vertex(net.p[net.edges[e * 2]]); _mesh.surface_add_vertex(net.p[net.edges[e * 2 + 1]])
	_mesh.surface_end()
	var s := GoalNet.SWAY_SCALE
	_left.rotation.z = -net.left.x * s / net.h
	_right.rotation.z = -net.right.x * s / net.h
	_bar.position = Vector3((net.left.x + net.right.x) * 0.5 * s, net.h + net.bar.x * s * 0.5, 0)

## Call once per physics frame with the ball in world space. Returns the ball's velocity after the net / posts have acted on it.
func ball_update(world_pos: Vector3, world_vel: Vector3, radius := -1.0) -> Vector3:
	var r := ball_radius if radius < 0.0 else radius
	var lp := to_local(world_pos); var lv := global_transform.basis.inverse() * world_vel
	_ball_seen = true
	if absf(lp.x) > 4.0 or absf(lp.z) > 6.0 or lp.y > 4.0:
		_advance(get_physics_process_delta_time(), false, lp, lv, r)
		return world_vel
	var out := _advance(get_physics_process_delta_time(), true, lp, lv, r)
	return global_transform.basis * (out["vel"] as Vector3)

func _advance(dt: float, has_ball: bool, lp: Vector3, lv: Vector3, r: float) -> Dictionary:
	var out := {"vel": lv}
	if not has_ball and net.energy < 0.02: return out
	var n := maxi(1, int(round(dt * 120.0)))
	var sub := dt / n
	for _i in n:
		out = net.step(sub, has_ball, lp, lv, r)
		lv = out["vel"]
		for h in out["hits"]:
			if h[0] == "net": hit_net.emit(to_global(h[1]))
			else: hit_frame.emit(h[0], to_global(h[1]))
	_draw_net()
	return out

func _physics_process(dt: float) -> void:
	if Engine.is_editor_hint(): return
	if _ball_seen: _ball_seen = false; return
	_advance(dt, false, Vector3.ZERO, Vector3.ZERO, ball_radius)
