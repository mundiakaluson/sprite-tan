class_name BallState
extends Node
## One state of the ball: a NODE under the Ball's StateMachine (scenes/ball/ball.tscn), the node name is the state name.
## Free = loose on the pitch, Held = at a player's feet, then the kick states Pass, Through, Lob, Shot (BallKick nodes, numbers in data/ball_actions.csv).
## Add a state by adding a node (or a script extending BallState / BallKick). `ball` is the owning Ball, `sm` the BallStateMachine.

@export_multiline var description := ""
## state to go to once the ball has come to rest (empty = stay). The kick states use Free.
@export var go_to_when_stopped: StringName = &""

var ball
var sm

func enter() -> void:
	_on_enter()

func exit() -> void:
	_on_exit()

func physics_update(dt: float) -> void:
	_on_physics_update(dt)

func _on_enter() -> void:
	pass

func _on_exit() -> void:
	pass

func _on_physics_update(_dt: float) -> void:
	if go_to_when_stopped != &"" and not ball.live: sm.go(go_to_when_stopped)
