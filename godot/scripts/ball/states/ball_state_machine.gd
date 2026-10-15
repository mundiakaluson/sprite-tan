class_name BallStateMachine
extends Node
## The ball's states (child BallState nodes). Ball code asks for a state by name (go()); other code listens to Ball.state_changed
## (AI can react to a through ball, the keeper to a shot, ...).

@export var initial_state: BallState

var ball                            # the owning Ball (untyped on purpose)
var states := {}                    # StringName -> BallState
var current: BallState

func _ready() -> void:
	ball = get_parent()
	for c in get_children():
		if c is BallState:
			c.sm = self
			c.ball = ball
			states[c.name] = c
	if initial_state != null: current = initial_state

func go(state_name: StringName) -> void:
	if not states.has(state_name):
		push_warning("BallStateMachine: no state '%s'" % state_name)
		return
	var prev: StringName = current.name if current != null else &""
	if current != null: current.exit()
	current = states[state_name]
	current.enter()
	if prev != state_name and ball != null: ball.state_changed.emit(prev, state_name)

func current_name() -> StringName:
	return current.name if current != null else &""

func kick_state(action_id: String) -> BallKick:
	for s in states.values():
		if s is BallKick and s.action_id == action_id: return s
	return null

func update(dt: float) -> void:
	if current != null: current.physics_update(dt)
