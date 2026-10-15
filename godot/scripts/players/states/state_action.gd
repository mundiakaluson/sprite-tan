class_name StateAction
extends PlayerState
## Plays the skill-card clip named in the order (Player.play_action("kick")), then goes to the order's "next" state or `go_to_when_clip_ends`.
## Leave `clip` empty on this node: the clip comes from the order.

var _next: StringName = &""

func _on_enter(msg: Dictionary) -> void:
	_next = msg.get("next", go_to_when_clip_ends)
	if msg.has("face"): player.face_vector(msg["face"])
	player.play_clip(str(msg.get("clip", "kick")), false)

func _on_clip_finished(_finished_clip: String) -> bool:
	if _next != &"": sm.transition_to(_next)
	return true
