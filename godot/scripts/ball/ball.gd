@tool
class_name Ball
extends Node2D
## The ball on the pitch: 3D physics (BallPhysics, numbers from data/balls.csv) drawn as a pixel sprite that rolls, with a ground shadow. Add it to a stadium with
## stadium.add_ball(ball): the stadium projects it every frame (position, size by distance, depth order) and wires the goal nets (collider).
## Gameplay hooks (from the ball row): power() scales kicks, touch() scales how easily a player controls it. Everything else (swerve, knuckle, bounce, grip) acts by itself.
##   var b := Ball.create("B02"); stadium.add_ball(b); b.launch(Vector3(0, 0.2, 0), Vector3(1, 0.1, 0), 28.0)
signal bounced(speed: float)

const SCENE := "res://scenes/ball/ball.tscn"
const FRAMES := 16
const SPRITE_DIAMETER := 14.0       # pixels of ball inside the 16 px cell

@export var ball_id := "B01":
	set(v):
		ball_id = v
		if is_node_ready(): setup(v)

@onready var sprite: Sprite2D = $Sprite
@onready var shadow: Sprite2D = $Shadow

var phys := BallPhysics.new()
var row := {}
var live := false
var collider := Callable()          ## (pos: Vector3, vel: Vector3, radius: float) -> Vector3, set by Stadium.add_ball
var _rolled := 0.0

static func create(id := "B01") -> Ball:
	var b := (load(SCENE) as PackedScene).instantiate() as Ball
	b.ball_id = id
	return b

func _ready() -> void:
	var img := Image.create(16, 8, false, Image.FORMAT_RGBA8)
	for y in 8:
		for x in 16:
			var d := Vector2((x - 7.5) / 8.0, (y - 3.5) / 4.0).length()
			if d <= 1.0: img.set_pixel(x, y, Color(0, 0, 0, 0.35))
	shadow.texture = ImageTexture.create_from_image(img)
	setup(ball_id)

func setup(id: String) -> void:
	row = Data.row("balls", id)
	if row.is_empty():
		push_warning("Ball: '%s' not found in balls.csv (run Export to game)" % id)
		return
	phys.setup(row)
	sprite.texture = Data.tex("balls/%s.png" % id)
	sprite.hframes = FRAMES
	sprite.frame = 0

func power() -> float: return phys.power
func touch() -> float: return phys.touch
func radius() -> float: return phys.rad
func world_pos() -> Vector3: return phys.pos

func launch(from: Vector3, dir: Vector3, speed: float, spin := Vector3.ZERO, seed_v := 1.0) -> void:
	phys.launch(from, dir, speed, spin, seed_v); live = true

func stop() -> void:
	phys.vel = Vector3.ZERO; phys.spin = Vector3.ZERO; live = false

func _physics_process(dt: float) -> void:
	if Engine.is_editor_hint() or not live: return
	var n := maxi(1, int(ceil(dt * 120.0)))
	var sub := dt / n
	for _i in n:
		var hit := phys.step(sub)
		if hit > 0.0: bounced.emit(hit)
		if collider.is_valid(): phys.vel = collider.call(phys.pos, phys.vel, phys.rad)
	_rolled += (Vector2(phys.vel.x, phys.vel.z).length() * dt) / phys.rad
	sprite.frame = int(_rolled / TAU * FRAMES) % FRAMES
	if phys.vel.length() < 0.05 and phys.pos.y <= phys.rad + 0.001: live = false

## called by the stadium each frame after it has placed this node: ground shadow offset in screen pixels (before this node's scale)
func place_shadow(offset_px: Vector2, height_m: float) -> void:
	shadow.position = offset_px / scale
	shadow.modulate.a = clampf(1.0 - height_m * 0.12, 0.25, 1.0)
	var s := clampf(1.0 - height_m * 0.06, 0.5, 1.0)
	shadow.scale = Vector2(s, s)
