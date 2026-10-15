class_name StateRun
extends PlayerState
## Runs to player.move_target at the player's speed (PAC stat). Arrives -> `arrive_state`. A new "move_to" event just changes the target.

@export var arrive_distance := 2.0
@export var arrive_state: StringName = &"Idle"
## 1.0 = normal; use another Run node with 1.6 for a sprint state, 0.5 for a jog
@export var speed_multiplier := 1.0

func _on_enter(msg: Dictionary) -> void:
	if msg.has("target"): player.move_target = msg["target"]

func _on_physics_update(delta: float) -> void:
	var to: Vector2 = player.move_target - player.position
	if to.length() <= arrive_distance:
		sm.transition_to(arrive_state)
		return
	player.velocity = to.normalized() * player.move_speed() * speed_multiplier
	player.face_vector(to)
	player.position += player.velocity * delta

func _on_event(ev: StringName, data: Dictionary) -> bool:
	if ev == &"move_to":
		player.move_target = data.get("target", player.move_target)
		return true
	return false
