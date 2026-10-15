extends Node
## Debug: the TV-view stadium with a few players standing about. A / D (or left / right) move the camera along the pitch, 1 2 3 switch stadium.
## (Keys are plain physical keys here on purpose; the real match view will use Input Map actions.)

@onready var stadium: Stadium = $Stadium
@onready var info: Label = $Hud/Info
var ids := ["ST01", "ST02", "ST03"]
var idx := 0
var ball: Ball
var ball_ids: Array = []
var ball_idx := 0
var kick_ids: Array = []
var kick_idx := 0

func _ready() -> void:
	if not Data.ok:
		info.text = "No exported data. Press EXPORT TO GAME in the manager tool first."
		return
	var rows := Data.table("players")
	var spots := [Vector2(50, 8), Vector2(20, 22), Vector2(78, 25), Vector2(50, 40), Vector2(30, 52), Vector2(70, 60), Vector2(48, 75), Vector2(52, 92)]
	for i in mini(spots.size(), rows.size()):
		var p := Player.create(); stadium.add_actor(p, spots[i]); p.setup(rows[i])
		p.face_vector(Vector2(1, 0))
	for r in Data.table("balls"): ball_ids.append(r["id"])
	for r in Data.table("kick_styles"): kick_ids.append(r["id"])
	ball = Ball.create(ball_ids[0] if not ball_ids.is_empty() else "B01"); stadium.add_ball(ball)
	_label()

func shoot() -> void:
	var goal_x := Stadium.L / 2.0
	var from := Vector3(goal_x - 22.0, 0.3, randf_range(-6.0, 6.0))
	var target := Vector3(goal_x, randf_range(0.3, 2.3), randf_range(-3.4, 3.4))
	var style := Data.row("kick_styles", kick_ids[kick_idx]) if not kick_ids.is_empty() else {}
	ball.kick(from, target - from, String(style.get("id", "K01")), 1.0)
	stadium.focus = Vector2(50, 85)

func next_kick() -> void:
	if kick_ids.is_empty(): return
	kick_idx = (kick_idx + 1) % kick_ids.size()
	_label()

func next_ball() -> void:
	if ball_ids.is_empty(): return
	ball_idx = (ball_idx + 1) % ball_ids.size()
	ball.ball_id = ball_ids[ball_idx]
	_label()

func _label() -> void:
	info.text = "%s   ball %s   A/D = camera   1 2 3 = stadium   B = shoot   N = next ball   K = next kick (%s)" % [stadium.stadium_id, ball.ball_id if ball != null else "-", Data.row("kick_styles", kick_ids[kick_idx]).get("name", "-") if not kick_ids.is_empty() else "-"]

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
	elif k == KEY_N: next_ball()
	elif k == KEY_K: next_kick()
	elif k == KEY_A: stadium.focus.y = clampf(stadium.focus.y - 6.0, 0.0, 100.0)
	elif k == KEY_D: stadium.focus.y = clampf(stadium.focus.y + 6.0, 0.0, 100.0)
