class_name PlayerStateMachine
extends Node
## Finite state machine for one player. Every child node that is a PlayerState becomes a state, named after the node. Add states in the
## editor (Add Child Node -> PlayerState, or your own script) and pick the start state in `initial_state`. Code can also call add_state().

signal transitioned(from_state: StringName, to_state: StringName)

@export var initial_state: PlayerState
## true = ignore transition requests (cutscenes, stun, ...); transition_to(..., force=true) still works
@export var locked := false

var player                          # the owning Player (untyped on purpose: no circular class references)
var states := {}                    # StringName -> PlayerState
var current: PlayerState
var previous_name: StringName = &""

func _ready() -> void:
	player = get_parent()
	register_children()

## (re)collect the child PlayerState nodes. Called automatically; call again after adding children from code.
func register_children() -> void:
	for c in get_children():
		if c is PlayerState:
			var st := c as PlayerState
			st.sm = self
			st.player = player
			states[st.name] = st

func add_state(state_name: StringName, st: PlayerState) -> PlayerState:
	st.name = state_name
	add_child(st)
	register_children()
	return st

## called by Player.setup() once the sprite is ready
func start(state_name: StringName = &"", msg := {}) -> void:
	if state_name == &"" and initial_state != null: state_name = initial_state.name
	if state_name == &"" and not states.is_empty(): state_name = states.keys()[0]
	if not states.has(state_name):
		push_warning("PlayerStateMachine: no start state '%s'. Add a PlayerState child and set initial_state." % state_name)
		return
	current = states[state_name]
	current.enter(msg)

func current_name() -> StringName:
	return current.name if current != null else &""

func is_in(state_name: StringName) -> bool:
	return current != null and current.name == state_name

func has_state(state_name: StringName) -> bool:
	return states.has(state_name)

func transition_to(state_name: StringName, msg := {}, force := false) -> bool:
	if not states.has(state_name):
		push_warning("PlayerStateMachine: no state '%s' (states: %s)" % [state_name, ", ".join(states.keys())])
		return false
	if current == null:
		start(state_name, msg)
		return true
	if locked and not force: return false
	if current.name == state_name and not msg.get("restart", false): return false
	var from := current.name
	current.exit()
	previous_name = from
	current = states[state_name]
	current.enter(msg)
	transitioned.emit(from, state_name)
	return true

## game events ("move_to", "play_action", "tackled", "ball_received", ...). The current state decides what to do with it.
func send_event(ev: StringName, data := {}) -> void:
	if current != null: current.on_event(ev, data)

func _process(delta: float) -> void:
	if current != null: current.update(delta)

func _physics_process(delta: float) -> void:
	if current != null: current.physics_update(delta)

## called by the Player when a non-looping clip ends
func clip_finished(finished_clip: String) -> void:
	if current != null: current.on_clip_finished(finished_clip)
