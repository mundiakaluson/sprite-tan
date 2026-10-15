extends Node
## Debug: the TV-view stadium with a few players standing about. A / D (or left / right) move the camera along the pitch, 1 2 3 switch stadium.
## (Keys are plain physical keys here on purpose; the real match view will use Input Map actions.)

@onready var stadium: Stadium = $Stadium
@onready var info: Label = $Hud/Info
var ids := ["ST01", "ST02", "ST03"]
var idx := 0
var ball: MeshInstance3D
var ball_vel := Vector3.ZERO
var ball_live := false

func _ready() -> void:
	if not Data.ok:
		info.text = "No exported data. Press EXPORT TO GAME in the manager tool first."
		return
	var rows := Data.table("players")
	var spots := [Vector2(50, 8), Vector2(20, 22), Vector2(78, 25), Vector2(50, 40), Vector2(30, 52), Vector2(70, 60), Vector2(48, 75), Vector2(52, 92)]
	for i in mini(spots.size(), rows.size()):
		var p := Player.create(); stadium.add_actor(p, spots[i]); p.setup(rows[i])
		p.face_vector(Vector2(1, 0))
	ball = MeshInstance3D.new(); var sm := SphereMesh.new(); sm.radius = 0.11; sm.height = 0.22; ball.mesh = sm
	var bm := StandardMaterial3D.new(); bm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; ball.material_override = bm
	stadium.add_child(ball); ball.visible = false
	_label()

func shoot() -> void:
	var goal_x := Stadium.L / 2.0
	ball.position = Vector3(goal_x - 16.0, 0.11, randf_range(-6.0, 6.0)); ball.visible = true
	var target := Vector3(goal_x, randf_range(0.3, 2.3), randf_range(-3.4, 3.4))
	var t := (target.x - ball.position.x) / 24.0
	ball_vel = Vector3(24.0, (target.y - ball.position.y + 0.5 * 9.81 * t * t) / t, (target.z - ball.position.z) / t)
	ball_live = true
	stadium.focus = Vector2(50, 85)

func _physics_process(dt: float) -> void:
	if not ball_live: return
	ball_vel.y -= 9.81 * dt
	ball.position += ball_vel * dt
	if ball.position.y < 0.11 and ball_vel.y < 0.0:
		ball.position.y = 0.11; ball_vel.y *= -0.6; ball_vel.x *= 0.92; ball_vel.z *= 0.92
	ball_vel = stadium.ball_update(ball.position, ball_vel)
	if absf(ball.position.x) > 70.0 or ball_vel.length() < 0.2: ball_live = false

func _label() -> void:
	info.text = "%s   A/D = camera   1 2 3 = stadium   B = shoot at the goal" % stadium.stadium_id

func _process(dt: float) -> void:
	var move := Input.get_axis(&"ui_left", &"ui_right")
	if absf(move) > 0.0: stadium.focus.y = clampf(stadium.focus.y + move * 40.0 * dt, 0.0, 100.0)

func _unhandled_key_input(ev: InputEvent) -> void:
	if not (ev is InputEventKey and ev.pressed): return
	var k: int = ev.physical_keycode
	var n := {KEY_1: 0, KEY_2: 1, KEY_3: 2}.get(k, -1) as int
	if n >= 0:
		stadium.stadium_id = ids[n]; _label()
	elif k == KEY_B: shoot()
	elif k == KEY_A: stadium.focus.y = clampf(stadium.focus.y - 6.0, 0.0, 100.0)
	elif k == KEY_D: stadium.focus.y = clampf(stadium.focus.y + 6.0, 0.0, 100.0)
