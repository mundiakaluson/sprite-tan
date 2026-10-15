class_name StateTimed
extends PlayerState
## A state that lasts a set time, then goes to `then_go_to`. Use it for stunned, celebrating, waiting for a card, a short pause and so on:
## add a StateTimed node, set `clip`, `duration` and `then_go_to` in the inspector. No code needed.

@export var duration := 1.0
@export var then_go_to: StringName = &"Idle"
var _t := 0.0

func _on_enter(_msg: Dictionary) -> void:
	_t = 0.0

func _on_update(delta: float) -> void:
	_t += delta
	if _t >= duration: sm.transition_to(then_go_to)
