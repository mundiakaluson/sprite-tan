class_name StateIdle
extends PlayerState
## Standing still. Leaves on a move order or an action.

const CLIP := "base_idle"

func enter(_msg := {}) -> void:
	player.velocity = Vector2.ZERO
	player.play_clip(CLIP, true, "run")

func on_event(ev: StringName, data := {}) -> void:
	match ev:
		&"move_to": sm.transition_to(&"run", data)
		&"play_action": sm.transition_to(&"action", data)
