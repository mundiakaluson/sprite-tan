class_name StateRun
extends PlayerState
## Running to player.move_target. Speed comes from the PAC stat. Arrives -> idle.

const CLIP := "run"
const ARRIVE := 2.0

func enter(msg := {}) -> void:
	if msg.has("target"): player.move_target = msg["target"]
	player.play_clip(CLIP, true)

func physics_update(delta: float) -> void:
	var to: Vector2 = player.move_target - player.position
	if to.length() <= ARRIVE:
		sm.transition_to(&"idle")
		return
	player.velocity = to.normalized() * player.move_speed()
	player.face_vector(to)
	player.position += player.velocity * delta

func on_event(ev: StringName, data := {}) -> void:
	match ev:
		&"move_to": player.move_target = data.get("target", player.move_target)
		&"play_action": sm.transition_to(&"action", data)
