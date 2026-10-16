@tool
class_name Ball
extends Node2D
## The ball on the pitch: 3D physics (BallPhysics, numbers from data/balls.csv) drawn as a pixel sprite that rolls, with a ground shadow. Add it to a stadium with
## stadium.add_ball(ball): the stadium projects it every frame (position, size by distance, depth order) and wires the goal nets (collider).
## The sprite is drawn by shaders/ball.gdshader from the ball's real 3D orientation (turned by its spin each physics step): a rolling ball rolls, a trivela turns about a tilted axis, a knuckle ball barely turns.
## Gameplay hooks (from the ball row): power() scales kicks, touch() scales how easily a player controls it. Everything else (swerve, knuckle, bounce, grip) acts by itself.
##   var b := Ball.create("B02"); stadium.add_ball(b); b.launch(Vector3(0, 0.2, 0), Vector3(1, 0.1, 0), 28.0)
signal bounced(speed: float)
signal state_changed(from_state: StringName, to_state: StringName)

const SCENE := "res://scenes/ball/ball.tscn"
const CHASE_VIEW := Basis(Vector3(0, 0, -1), Vector3(0, 1, 0), Vector3(1, 0, 0))   # world x -> view -z, y -> y, z -> x
const SPRITE_DIAMETER := 14.0       # pixels of ball inside the 16 px cell

@export var ball_id := "B01":
	set(v):
		ball_id = v
		if is_node_ready(): setup(v)

## where the ball rests when this scene is placed inside a Stadium's Actors node (pitch coords)
@export var pitch_position := Vector2(50, 50)

@export_group("Animation preview")
## spin the ball by hand (rad/s, world axes; +x = roll about the travel axis, +y = side spin, +z = backspin). The AnimationPlayer clips (one per kick style, generated from
## data/kick_styles.csv) set this, so play a clip in the Animation tab to see that kick's spin. Ignored while the ball is flying (live).
@export var preview_spin := Vector3.ZERO
@export_range(0.05, 2.0) var preview_speed := 0.3        ## slow motion for the preview

## The Shadow and Sprite nodes are made in _ready() (not saved into the scene, so the scene file stays clean); the clips in the AnimationPlayer find the sprite by the name "Sprite".
var sprite: Sprite2D
## how big the ball is drawn (1 = full size); MatchGame sets it from MatchSettings > Ball and first touch
var visual_scale := 0.7:
	set(v):
		visual_scale = v
		if sprite != null: sprite.scale = Vector2.ONE * v
var shadow: Sprite2D
@onready var anim_player: AnimationPlayer = $AnimationPlayer
## Free / Held / Pass / Through / Lob / Shot (child nodes, scenes/ball/ball.tscn)
@onready var sm: BallStateMachine = get_node_or_null("StateMachine") as BallStateMachine
## the kick action of the last kick ("pass", "through", "lob", "shot"), kept while the ball is still flying
var action := ""
## the kick style id (data/kick_styles.csv) of the last kick; the keeper reads its save_difficulty, the trail shows spin kicks
var style := ""

var phys := BallPhysics.new()
var row := {}
var live := false
var collider := Callable()          ## (pos: Vector3, vel: Vector3, radius: float) -> Vector3, set by Stadium.add_ball
var orient := Basis()               ## ball-local -> world
var _view := CHASE_VIEW             ## world -> camera, set by the stadium each frame (the default looks at the ball from behind)
var _mat: ShaderMaterial

static func create(id := "B01") -> Ball:
	var b := (load(SCENE) as PackedScene).instantiate() as Ball
	b.ball_id = id
	return b

func _ready() -> void:
	shadow = Sprite2D.new(); shadow.name = "Shadow"; shadow.z_index = -1; add_child(shadow)
	sprite = Sprite2D.new(); sprite.name = "Sprite"; add_child(sprite)
	var img := Image.create(16, 8, false, Image.FORMAT_RGBA8)
	for y in 8:
		for x in 16:
			var d := Vector2((x - 7.5) / 8.0, (y - 3.5) / 4.0).length()
			if d <= 1.0: img.set_pixel(x, y, Color(0, 0, 0, 0.35))
	shadow.texture = ImageTexture.create_from_image(img)
	_mat = ShaderMaterial.new(); _mat.shader = load("res://shaders/ball.gdshader")
	var white := Image.create(16, 16, false, Image.FORMAT_RGBA8); white.fill(Color.WHITE)
	sprite.texture = ImageTexture.create_from_image(white); sprite.material = _mat
	sprite.scale = Vector2.ONE * visual_scale
	setup(ball_id)

func setup(id: String) -> void:
	row = Data.row("balls", id)
	if row.is_empty():
		push_warning("Ball: '%s' not found in balls.csv (run Export to game)" % id)
		return
	phys.setup(row)
	_mat.set_shader_parameter("map", Data.tex("balls/%s_map.png" % id))
	_mat.set_shader_parameter("shine", _f(row, "shine", 1.0))
	_refresh_orient()

static func _f(r: Dictionary, k: String, d: float) -> float:
	var v = r.get(k, "")
	return float(v) if str(v) != "" else d

func power() -> float: return phys.power
func touch() -> float: return phys.touch
func radius() -> float: return phys.rad
func world_pos() -> Vector3: return phys.pos

func launch(from: Vector3, dir: Vector3, speed: float, spin := Vector3.ZERO, seed_v := 1.0) -> void:
	phys.launch(from, dir, speed, spin, seed_v); live = true

## The ball goes to a player's feet (state Held). The caller keeps placing it.
func hold() -> void:
	live = false
	action = ""
	if sm != null: sm.go(&"Held")

## The ball is loose (state Free).
func set_free() -> void:
	if sm != null: sm.go(&"Free")

## Kick it as a pass / through / lob / shot (the kick states, numbers in data/ball_actions.csv). target = metres (x along, z across), stats = the kicker's player row,
## target_vel = how the receiver moves (the state aims ahead of him by its lead). `over` may replace "style", "speed", "noise" (skill cards do that). Returns the plan used.
func play_action(action_id: String, target: Vector2, stats := {}, target_vel := Vector2.ZERO, over := {}) -> Dictionary:
	var st: BallKick = sm.kick_state(action_id) if sm != null else null
	if st == null:
		push_warning("Ball.play_action: no kick state for '%s'" % action_id)
		return {}
	var plan := st.plan(phys.pos, target, stats, target_vel)
	for k in over: plan[k] = over[k]
	if plan.has("speed_k"): plan["speed"] = float(plan["speed"]) * float(plan["speed_k"])     # an under- / over-hit pass
	var tgt: Vector2 = plan["target"]
	var from := phys.pos
	var noise: float = plan["noise"]
	var aim := Vector3(tgt.x - from.x, 0.0, tgt.y - from.z).rotated(Vector3.UP, deg_to_rad(randf_range(-noise, noise)))
	var s := Data.row("kick_styles", str(plan["style"]))
	var base := _f(s, "speed", 25.0) * _f(s, "power", 1.0)
	kick(from, aim, str(plan["style"]), float(plan["speed"]) / maxf(base, 0.1))
	action = action_id
	sm.go(st.name)
	return plan

func stop() -> void:
	phys.vel = Vector3.ZERO; phys.spin = Vector3.ZERO; live = false

func _process(dt: float) -> void:
	if live: return
	if preview_spin.length() > 0.0001:                  # animation preview (editor and game): turn by the clip's spin in slow motion
		orient = (Basis(preview_spin.normalized(), preview_spin.length() * dt * preview_speed) * orient).orthonormalized()
		_refresh_orient()

func _physics_process(dt: float) -> void:
	if Engine.is_editor_hint(): return
	if live: _simulate(dt)
	if sm != null: sm.update(dt)

func _simulate(dt: float) -> void:
	var n := maxi(1, int(ceil(dt * 120.0)))
	var sub := dt / n
	for _i in n:
		var hit := phys.step(sub)
		if hit > 0.0: bounced.emit(hit)
		if collider.is_valid(): phys.vel = collider.call(phys.pos, phys.vel, phys.rad)
	if phys.spin.length() > 0.0001:
		orient = (Basis(phys.spin.normalized(), phys.spin.length() * dt) * orient).orthonormalized()
	_refresh_orient()
	if phys.vel.length() < 0.05 and phys.pos.y <= phys.rad + 0.001: live = false

func set_view(world_to_camera: Basis) -> void:
	_view = world_to_camera
	_refresh_orient()

func _refresh_orient() -> void:
	if _mat == null: return
	var m := _view * orient                      # ball-local -> view: its columns are the ball's own axes seen from the camera
	_mat.set_shader_parameter("axis_x", m.x)
	_mat.set_shader_parameter("axis_y", m.y)
	_mat.set_shader_parameter("axis_z", m.z)

## A kick: style_id from data/kick_styles.csv (Finesse, Trivela, Knuckle, ...). aim = direction on the ground / towards the target (any length), strength = the player's power 0..1.3.
## Speed = style speed x strength x style power x this ball's power. Aim error (degrees) is the style's error divided by this ball's touch. Spin is built in the travel frame:
## roll about the travel axis, side about the vertical, back about the horizontal across the travel. Returns the style row.
func kick(from: Vector3, aim: Vector3, style_id: String, strength := 1.0, rng_seed := -1.0) -> Dictionary:
	var k := Data.row("kick_styles", style_id)
	style = style_id
	if k.is_empty():
		push_warning("Ball.kick: no kick style '%s' (run Export to game)" % style_id)
		return k
	var flat := Vector3(aim.x, 0.0, aim.z)
	if flat.length() < 0.001: flat = Vector3.RIGHT
	flat = flat.normalized()
	var err := _f(k, "error", 0.0) / maxf(0.3, phys.touch)
	var yaw := deg_to_rad(_f(k, "azim", 0.0) + randf_range(-err, err))
	var elev := deg_to_rad(_f(k, "elev", 0.0) + randf_range(-err, err) * 0.5)
	var ex := flat.rotated(Vector3.UP, -yaw)                       # travel direction on the ground
	var dir := (ex * cos(elev) + Vector3.UP * sin(elev))
	var ey := Vector3.UP
	var ez := ex.cross(ey)
	var spin := ex * _f(k, "roll", 0.0) + ey * _f(k, "side", 0.0) + ez * _f(k, "back", 0.0)
	var sp := _f(k, "speed", 25.0) * strength * _f(k, "power", 1.0)
	launch(from, dir, sp, spin, (randf() * 100.0) if rng_seed < 0.0 else rng_seed)
	return k

## a copy of this ball's physics (same numbers, position, velocity and spin) to step forward for predictions
func copy_physics() -> BallPhysics:
	var p := BallPhysics.new()
	for key in ["g", "rad", "drag", "mag", "knu", "knu_v", "crisis", "crisis_v", "e", "mu", "roll", "sdec", "spin_drag", "power", "touch", "mass", "pos", "vel", "spin", "t", "seed_value"]:
		p.set(key, phys.get(key))
	return p

## where a kick would cross the line x = line_x (no aim error): launched from `from` towards `aim` (pitch x / z) with a kick style and a ball speed (m/s).
## Returns the 3D point (x, height, z), or the last point if it never gets there within `max_t` s. Used by the AI to aim curlers so the bend takes them into the corner.
func predict_cross(from: Vector3, aim: Vector2, style_id: String, speed: float, line_x: float, max_t := 3.0) -> Vector3:
	var k := Data.row("kick_styles", style_id)
	var p := copy_physics()
	var flat := Vector3(aim.x - from.x, 0.0, aim.y - from.z)
	if flat.length() < 0.001: return from
	flat = flat.normalized()
	var ex := flat.rotated(Vector3.UP, -deg_to_rad(_f(k, "azim", 0.0)))
	var elev := deg_to_rad(_f(k, "elev", 0.0))
	var spin := ex * _f(k, "roll", 0.0) + Vector3.UP * _f(k, "side", 0.0) + ex.cross(Vector3.UP) * _f(k, "back", 0.0)
	p.launch(from, ex * cos(elev) + Vector3.UP * sin(elev), speed, spin, 1.0)
	var side := signf(line_x - from.x)
	var t := 0.0
	var dt := 1.0 / 60.0
	while t < max_t:
		var before := p.pos
		p.step(dt)
		t += dt
		if (p.pos.x - line_x) * side >= 0.0:
			var u := (line_x - before.x) / maxf(absf(p.pos.x - before.x), 0.0001) * side
			return before.lerp(p.pos, clampf(absf(u), 0.0, 1.0))
	return p.pos

## the flight of a kick (no aim error): launched from `from` towards `aim` (pitch x / z) with a kick style and speed, a point every `every` s for `max_t` s
## (stops early when it has stopped rolling). The same launch as Ball.kick, so what the planner sees is what the ball does.
func simulate_path(from: Vector3, aim: Vector2, style_id: String, speed: float, max_t := 2.5, every := 1.0 / 30.0) -> PackedVector3Array:
	var k := Data.row("kick_styles", style_id)
	var p := copy_physics()
	var out := PackedVector3Array()
	var flat := Vector3(aim.x - from.x, 0.0, aim.y - from.z)
	if flat.length() < 0.001: return out
	flat = flat.normalized()
	var ex := flat.rotated(Vector3.UP, -deg_to_rad(_f(k, "azim", 0.0)))
	var elev := deg_to_rad(_f(k, "elev", 0.0))
	var spin := ex * _f(k, "roll", 0.0) + Vector3.UP * _f(k, "side", 0.0) + ex.cross(Vector3.UP) * _f(k, "back", 0.0)
	p.launch(from, ex * cos(elev) + Vector3.UP * sin(elev), speed, spin, 1.0)
	out.append(p.pos)
	var t := 0.0
	var dt := 1.0 / 60.0
	var next := every
	while t < max_t:
		p.step(dt)
		t += dt
		if t >= next:
			out.append(p.pos)
			next += every
		if p.vel.length() < 0.5: break
	return out

## seconds a kick from `from` to the spot `to` (pitch x / z) takes to get there with this style and speed (no aim error); INF if it stops short.
## Used to weight a through ball so it arrives when the runner does (MatchOrders.plan_run).
func time_to_reach(from: Vector3, to: Vector2, style_id: String, speed: float, max_t := 4.0) -> float:
	var k := Data.row("kick_styles", style_id)
	var p := copy_physics()
	var flat := Vector3(to.x - from.x, 0.0, to.y - from.z)
	var dist := flat.length()
	if dist < 0.1: return 0.0
	flat = flat.normalized()
	var elev := deg_to_rad(_f(k, "elev", 0.0))
	p.launch(from, flat * cos(elev) + Vector3.UP * sin(elev), speed, Vector3.ZERO, 1.0)
	var t := 0.0
	var dt := 1.0 / 60.0
	while t < max_t:
		p.step(dt)
		t += dt
		if Vector2(p.pos.x - from.x, p.pos.z - from.z).length() >= dist: return t
		if p.vel.length() < 0.3: return INF
	return INF

## the kick speed (m/s) that gets a kick to `to` in about `want_t` seconds, between lo and hi
func speed_for_time(from: Vector3, to: Vector2, style_id: String, want_t: float, lo := 6.0, hi := 28.0) -> float:
	var a := lo
	var b := hi
	for i in 14:
		var mid := (a + b) * 0.5
		if time_to_reach(from, to, style_id, mid) > want_t: a = mid
		else: b = mid
	return b

## called by the stadium each frame after it has placed this node: ground shadow offset in screen pixels (before this node's scale)
func place_shadow(offset_px: Vector2, height_m: float) -> void:
	shadow.position = offset_px / scale
	shadow.modulate.a = clampf(1.0 - height_m * 0.12, 0.25, 1.0)
	var s := clampf(1.0 - height_m * 0.06, 0.5, 1.0)
	shadow.scale = Vector2(s, s) * visual_scale
