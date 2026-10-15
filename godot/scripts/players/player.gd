class_name Player
extends Node2D
## One player on the pitch: the recoloured sprite, the data row, and a state machine (idle / run / action). Add new states by writing a
## PlayerState script in scripts/players/states/ and registering it in _build_states().
##   var p := Player.new(); add_child(p); p.setup(Data.row("players", "PL242")); p.move_to(Vector2(300, 200)); p.play_action("kick")

signal state_changed(from_state: StringName, to_state: StringName)

const BASE_SPEED := 30.0        # pixels per second at PAC 0 (placeholder numbers, tune with the match view)
const SPEED_PER_PAC := 0.6

var row := {}
var sprite: PlayerSprite
var sm: PlayerStateMachine
var velocity := Vector2.ZERO
var move_target := Vector2.ZERO
var facing := 16                # 0..31, 8 = screen right, 16 = toward the camera

func setup(r: Dictionary) -> void:
	row = r
	sprite = PlayerSprite.new()
	add_child(sprite)
	sprite.setup(str(r.get("id", "")))
	sprite.finished.connect(_on_sprite_finished)
	sm = PlayerStateMachine.new()
	sm.player = self
	add_child(sm)
	_build_states()
	sm.transitioned.connect(func(a, b): state_changed.emit(a, b))
	sm.start(&"idle")

func _build_states() -> void:
	sm.add_state(&"idle", StateIdle.new())
	sm.add_state(&"run", StateRun.new())
	sm.add_state(&"action", StateAction.new())

# ---- orders (the AI and the player's cards call these)
func move_to(pos: Vector2) -> void:
	sm.send_event(&"move_to", {"target": pos})

func play_action(clip: String, face_toward := Vector2.ZERO, next := &"idle") -> void:
	var d := {"clip": clip, "next": next}
	if face_toward != Vector2.ZERO: d["face"] = face_toward
	sm.send_event(&"play_action", d)

# ---- helpers for states
func move_speed() -> float:
	var pac := Data.inum(row.get("PAC"), 50)
	return (BASE_SPEED + pac * SPEED_PER_PAC) * 1.0

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
	elif stand_in != "" and sprite.has_clip(stand_in):
		sprite.play(stand_in)
		sprite.paused = true

func _on_sprite_finished(clip: String) -> void:
	sm.clip_finished(clip)
