class_name StateAction
extends PlayerState
## Plays one skill-card animation (msg {"clip": "kick", "face": Vector2 optional, "next": "idle" optional) and returns to `next` when it ends.

var next_state: StringName = &"idle"

func enter(msg := {}) -> void:
	next_state = msg.get("next", &"idle")
	player.velocity = Vector2.ZERO
	if msg.has("face"): player.face_vector(msg["face"])
	player.play_clip(str(msg.get("clip", "kick")), false)

func on_clip_finished(_clip: String) -> void:
	sm.transition_to(next_state)
