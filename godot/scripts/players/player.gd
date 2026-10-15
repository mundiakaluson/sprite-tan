class_name Player
extends Node2D
## One player on the pitch. Instance scenes/players/player.tscn (Player.create() does it), then setup(row).
## The scene holds: Sprite (recoloured sheet player) and StateMachine with its states as child nodes. Edit the states in the inspector.
##   var p := Player.create(); add_child(p); p.setup(Data.row("players", "PL242")); p.move_to(Vector2(300, 200)); p.play_action("kick")

signal state_changed(from_state: StringName, to_state: StringName)

const SCENE := "res://scenes/players/player.tscn"
const BASE_SPEED := 30.0        # pixels per second at PAC 0 (placeholder numbers, tune with the match view)
const SPEED_PER_PAC := 0.6

@onready var sprite: PlayerSprite = $Sprite
@onready var sm: PlayerStateMachine = $StateMachine

var row := {}
var velocity := Vector2.ZERO
var move_target := Vector2.ZERO
var facing := 16                # 0..31, 8 = screen right, 16 = toward the camera

static func create() -> Player:
	return (load(SCENE) as PackedScene).instantiate() as Player

func setup(r: Dictionary) -> void:
	row = r
	sprite.setup(str(r.get("id", "")))
	if not sprite.finished.is_connected(_on_sprite_finished): sprite.finished.connect(_on_sprite_finished)
	if not sm.transitioned.is_connected(_on_transitioned): sm.transitioned.connect(_on_transitioned)
	sm.start()

# ---- orders (the AI and the player's cards call these)
func send_event(ev: StringName, data := {}) -> void:
	sm.send_event(ev, data)

func move_to(pos: Vector2) -> void:
	sm.send_event(&"move_to", {"target": pos})

func play_action(clip: String, face_toward := Vector2.ZERO, next := &"") -> void:
	var d := {"clip": clip}
	if next != &"": d["next"] = next
	if face_toward != Vector2.ZERO: d["face"] = face_toward
	sm.send_event(&"play_action", d)

# ---- helpers for states
func move_speed() -> float:
	var pac := Data.inum(row.get("PAC"), 50)
	return BASE_SPEED + pac * SPEED_PER_PAC

func face_vector(v: Vector2) -> void:
	if v.length() < 0.001: return
	var deg := rad_to_deg(atan2(v.x, -v.y))          # up = 0, right = 90, down = 180, left = 270
	facing = posmod(int(round(deg / 11.25)), 32)
	sprite.face(facing)

## starts a clip. A clip that is not baked yet is skipped quietly so states can name future animations; `stand_in` (e.g. "run") is
## shown frozen on its first frame instead, so a missing idle looks like standing still.
func play_clip(clip: String, loop: bool, stand_in := "") -> void:
	if sprite.has_clip(clip):
		sprite.play(clip)
		sprite.loop_override = 1 if loop else 0
		sprite.face(facing)
	elif stand_in != "" and sprite.has_clip(stand_in):
		sprite.play(stand_in)
		sprite.paused = true
		sprite.face(facing)

func _on_sprite_finished(clip: String) -> void:
	sm.clip_finished(clip)

func _on_transitioned(a: StringName, b: StringName) -> void:
	state_changed.emit(a, b)
