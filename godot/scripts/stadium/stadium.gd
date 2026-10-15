@tool
class_name Stadium
extends Node3D
## TV-view stadium with real perspective. A flat pitch texture on the ground, stands / boards / goals / flags / floodlights built from simple
## 3D parts, and a Camera3D behind the near touchline that follows the play. Art comes from res://assets/pitches/<stadium_id>/ (export step
## "stadiums", data/stadiums.csv). Players stay 2D sprites: add them with add_actor(), the stadium projects them onto the screen every frame
## (position, size by distance, depth order), so the existing Player scene is used as it is.
##
## World: 1 unit = 1 metre. X along the pitch (own goal at -52.5, opponent goal at +52.5), Z across (far touchline at -34, near touchline at +34), Y up.
## Pitch coordinates (formations): x 0-100 across (0 = far touchline, the top of the screen), y 0-100 own goal to opponent goal.

const L := 105.0
const W := 68.0

@export var stadium_id := "ST01":
	set(v):
		stadium_id = v
		if is_node_ready(): rebuild()
@export_group("Camera")
@export var cam_height := 26.0          ## metres above the grass
@export var cam_back := 16.0            ## metres behind the near touchline
@export var look_z := -4.0              ## the camera aims at this Z on the grass (negative = towards the far touchline)
@export_range(10.0, 90.0) var fov := 34.0
@export var use_layout_camera := true   ## take height / back / aim / fov from the stadium (data/stadiums.csv); untick to set them here
@export var follow_speed := 4.0
@export var limit_x := 38.0             ## the camera never goes further than this along the pitch
@export_group("Players")
@export var player_height_m := 1.8
@export var sprite_height_px := 26.0    ## how tall a player sprite is in pixels at scale 1 (feet to top of head)

@onready var camera: Camera3D = $Camera
@onready var world: Node3D = $World
@onready var actors: Node2D = $Actors

var layout := {}
var focus := Vector2(50, 50)            ## pitch position the camera looks at
var _cam_x := 0.0
var _actors := {}                       ## Node2D -> pitch position (Vector2)
var _mats := {}
var goals: Array[Goal] = []
var _balls: Array[Ball] = []

func _ready() -> void:
	rebuild()
	if not Engine.is_editor_hint(): _adopt_placed()

## Players and balls placed under Actors in the scene editor (instances of player.tscn / ball.tscn) are registered when the game starts.
## Set their Pitch Position in the inspector; a player shows the look of its Preview Player id.
func _adopt_placed() -> void:
	for c in actors.get_children():
		if c is Player:
			add_actor(c, c.pitch_position)
			c.setup(Data.row("players", c.preview_player))
			c.face_vector(Vector2(1, 0))
		elif c is Ball:
			_adopt_ball(c)

func _adopt_ball(b: Ball) -> void:
	_balls.append(b)
	b.collider = ball_update
	b.launch(world_pos(b.pitch_position) + Vector3(0, 0.2, 0), Vector3.RIGHT, 0.0)
	_project_ball(b)

# ---- coordinates
func world_pos(p: Vector2) -> Vector3:
	return Vector3((p.y / 100.0 - 0.5) * L, 0.0, (p.x / 100.0 - 0.5) * W)

func pitch_pos(w: Vector3) -> Vector2:
	return Vector2((w.z / W + 0.5) * 100.0, (w.x / L + 0.5) * 100.0)

# ---- actors (2D players in the 3D scene)
func add_actor(n: Node2D, pitch: Vector2) -> void:
	if n.get_parent() != actors:
		if n.get_parent() != null: n.get_parent().remove_child(n)
		actors.add_child(n)
	_actors[n] = pitch
	_project(n)

func set_actor_pos(n: Node2D, pitch: Vector2) -> void:
	_actors[n] = pitch

func remove_actor(n: Node2D) -> void:
	_actors.erase(n)

func _project(n: Node2D) -> void:
	var w := world_pos(_actors[n])
	if camera.is_position_behind(w):
		n.visible = false
		return
	n.visible = true
	var foot := camera.unproject_position(w)
	var head := camera.unproject_position(w + Vector3(0, player_height_m, 0))
	n.position = foot
	n.scale = Vector2.ONE * (absf(foot.y - head.y) / sprite_height_px)
	n.z_index = clampi(int(foot.y), -4000, 4000)

## put a Ball in the stadium: it is projected like the players and its physics is wired to the goal nets
func add_ball(b: Ball) -> void:
	if b.get_parent() != actors:
		if b.get_parent() != null: b.get_parent().remove_child(b)
		actors.add_child(b)
	_balls.append(b)
	b.collider = ball_update
	_project_ball(b)

func _project_ball(b: Ball) -> void:
	var w := b.world_pos()
	if camera.is_position_behind(w):
		b.visible = false
		return
	b.visible = true
	var p := camera.unproject_position(w)
	var g := camera.unproject_position(Vector3(w.x, 0.0, w.z))
	var edge := camera.unproject_position(w + camera.global_transform.basis.x * b.radius())
	var s := maxf(0.2, absf(edge.x - p.x) * 2.0 / Ball.SPRITE_DIAMETER)
	b.position = p
	b.scale = Vector2.ONE * s
	b.set_view(camera.global_transform.basis.inverse())
	b.place_shadow(g - p, w.y)
	b.z_index = clampi(int(g.y) + 1, -4000, 4000)

func _process(dt: float) -> void:
	if Engine.is_editor_hint(): return
	_cam_x = lerpf(_cam_x, clampf(world_pos(focus).x, -limit_x, limit_x), clampf(follow_speed * dt, 0.0, 1.0))
	_update_camera()
	for b in _balls:
		if is_instance_valid(b): _project_ball(b)
	for n in _actors.keys():
		if is_instance_valid(n): _project(n)
		else: _actors.erase(n)

func _update_camera() -> void:
	camera.fov = fov
	camera.look_at_from_position(Vector3(_cam_x, cam_height, W / 2.0 + cam_back), Vector3(_cam_x, 0.0, look_z), Vector3.UP)

## snap the camera onto the focus without easing (after a restart, a kick-off, ...)
func snap_camera() -> void:
	_cam_x = clampf(world_pos(focus).x, -limit_x, limit_x)
	_update_camera()

# ---- building
func _load_json(path: String) -> Variant:
	if not FileAccess.file_exists(path): return null
	return JSON.parse_string(FileAccess.get_file_as_string(path))

func _tex(path: String) -> Texture2D:
	if ResourceLoader.exists(path):
		var t = load(path)
		if t is Texture2D: return t
	if FileAccess.file_exists(path):
		var img := Image.load_from_file(ProjectSettings.globalize_path(path))
		if img != null: return ImageTexture.create_from_image(img)
	return null

func _mat(tex: Texture2D, color := Color.WHITE, alpha := false) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.albedo_color = color
	if tex != null:
		m.albedo_texture = tex
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
	if alpha: m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return m

## a quad from 4 corners p0..p3 (in order around it) with uvs
func _quad(parent: Node3D, p: Array, uv: Array, mat: Material) -> MeshInstance3D:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in [0, 1, 2, 0, 2, 3]:
		st.set_uv(uv[i]); st.add_vertex(p[i])
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit(); mi.material_override = mat
	parent.add_child(mi)
	return mi

func _box(parent: Node3D, size: Vector3, at: Vector3, color: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = size
	mi.mesh = bm; mi.material_override = _mat(null, color); mi.position = at
	parent.add_child(mi)
	return mi

func rebuild() -> void:
	for c in world.get_children(): c.queue_free()
	var dir := "res://assets/pitches/%s/" % stadium_id
	var l = _load_json(dir + "layout.json")
	if l == null:
		push_warning("Stadium: no art for '%s' (run Export to game)" % stadium_id)
		return
	layout = l
	if use_layout_camera and layout.has("cam"):
		var cm = layout["cam"]; cam_height = cm["height"]; cam_back = cm["back"]; look_z = cm["look_z"]; fov = cm["fov"]
	var sky := Color8(layout["sky"][0], layout["sky"][1], layout["sky"][2])
	var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = sky
	var we := WorldEnvironment.new(); we.environment = env; world.add_child(we)
	var apr: float = layout["apron"]; var hx := L / 2.0 + apr; var hz := W / 2.0 + apr
	# pitch
	_quad(world, [Vector3(-hx, 0, -hz), Vector3(hx, 0, -hz), Vector3(hx, 0, hz), Vector3(-hx, 0, hz)], [Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], _mat(_tex(dir + "pitch.png")))
	# stands: far side and both ends rise away from the pitch; a dark wall behind them keeps the sky out of the gaps
	var stand_mat := _mat(_tex(dir + "stand.png"))
	var stand_col := Color8(layout["stand"][0], layout["stand"][1], layout["stand"][2]).darkened(0.55)
	var rise := 14.0; var run := 17.0; var yb := 1.0
	var sx := hx + 14.0
	_quad(world, [Vector3(-sx, yb, -hz - 1), Vector3(sx, yb, -hz - 1), Vector3(sx, yb + rise, -hz - 1 - run), Vector3(-sx, yb + rise, -hz - 1 - run)],
		[Vector2(0, 1), Vector2(sx * 2.0 / 58.0, 1), Vector2(sx * 2.0 / 58.0, 0), Vector2(0, 0)], stand_mat)
	_quad(world, [Vector3(-sx, yb + rise, -hz - 1 - run), Vector3(sx, yb + rise, -hz - 1 - run), Vector3(sx, yb + rise + 16, -hz - 1 - run), Vector3(-sx, yb + rise + 16, -hz - 1 - run)],
		[Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], _mat(null, stand_col))
	for s in [-1.0, 1.0]:
		var ex: float = s * (hx + 1.0); var ox: float = s * run
		_quad(world, [Vector3(ex, yb, -hz - 1), Vector3(ex, yb, hz + 8), Vector3(ex + ox, yb + rise, hz + 8), Vector3(ex + ox, yb + rise, -hz - 1 - run)],
			[Vector2(0, 1), Vector2((hz * 2.0 + 9.0) / 58.0, 1), Vector2((hz * 2.0 + 9.0) / 58.0, 0), Vector2(0, 0)], stand_mat)
	# advertising boards around the grass
	var bm := _mat(_tex(dir + "boards.png"))
	var bw := hx * 2.0 / 32.0; var bd := hz * 2.0 / 32.0
	_quad(world, [Vector3(-hx, 0, -hz), Vector3(hx, 0, -hz), Vector3(hx, 1.0, -hz), Vector3(-hx, 1.0, -hz)], [Vector2(0, 1), Vector2(bw, 1), Vector2(bw, 0), Vector2(0, 0)], bm)
	_quad(world, [Vector3(-hx, 0, hz), Vector3(hx, 0, hz), Vector3(hx, 1.0, hz), Vector3(-hx, 1.0, hz)], [Vector2(0, 1), Vector2(bw, 1), Vector2(bw, 0), Vector2(0, 0)], bm)
	for s in [-1.0, 1.0]:
		_quad(world, [Vector3(s * hx, 0, -hz), Vector3(s * hx, 0, hz), Vector3(s * hx, 1.0, hz), Vector3(s * hx, 1.0, -hz)], [Vector2(0, 1), Vector2(bd, 1), Vector2(bd, 0), Vector2(0, 0)], bm)
	# goals and corner flags
	goals.clear()
	_goal(-1.0); _goal(1.0)
	for cx in [-L / 2.0, L / 2.0]:
		for cz in [-W / 2.0, W / 2.0]: _flag(Vector3(cx, 0, cz))
	if layout.get("towers", false):
		for tx in [-hx - 6.0, hx + 6.0]:
			for tz in [-hz - 8.0, hz + 8.0]: _tower(Vector3(tx, 0, tz))
	snap_camera()

func _goal(side: float) -> void:      # side -1 = own goal (left), +1 = opponent goal (right). Goal's local +x points outward.
	var g := Goal.new()
	g.wear_override = float(layout.get("net_wear", -1.0))
	g.style_id = String(layout.get("goal", "G01"))
	g.position = Vector3(side * L / 2.0, 0, 0)
	if side < 0.0: g.rotation.y = PI
	world.add_child(g); goals.append(g)

## the ball (world space) near a goal: returns its new velocity after the net and posts acted on it. Call once per physics frame.
func ball_update(pos: Vector3, vel: Vector3, radius := GoalNet.BALL_R) -> Vector3:
	for g in goals: vel = g.ball_update(pos, vel, radius)
	return vel

func _flag(at: Vector3) -> void:
	_box(world, Vector3(0.05, 1.5, 0.05), at + Vector3(0, 0.75, 0), Color(0.96, 0.96, 0.92))
	_box(world, Vector3(0.4, 0.3, 0.02), at + Vector3(0.22, 1.35, 0), Color(0.93, 0.27, 0.2))

func _tower(at: Vector3) -> void:
	_box(world, Vector3(0.7, 32.0, 0.7), at + Vector3(0, 16.0, 0), Color(0.23, 0.25, 0.29))
	_box(world, Vector3(7.0, 3.5, 0.8), at + Vector3(0, 33.5, 0), Color(1.0, 0.97, 0.82))
