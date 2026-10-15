class_name PlayerStateMachine
extends Node
## Generic finite state machine for one player. States are PlayerState nodes added with add_state(); the machine owns the current one
## and forwards update / physics / events to it. States ask for a change with sm.transition_to("run", {"target": pos}).

signal transitioned(from_state: StringName, to_state: StringName)

var player                          # the owning Player (untyped on purpose: no circular class references)
var states := {}                    # StringName -> PlayerState
var current: PlayerState
var previous_name: StringName = &""
var locked := false                 # true = ignore transition requests (cutscenes, stunned and so on); force=true still works

func add_state(state_name: StringName, st: PlayerState) -> PlayerState:
	st.name = state_name
	st.sm = self
	st.player = player
	states[state_name] = st
	add_child(st)
	return st

func start(state_name: StringName, msg := {}) -> void:
	assert(states.has(state_name), "unknown state %s" % state_name)
	current = states[state_name]
	current.enter(msg)

func current_name() -> StringName:
	return current.name if current != null else &""

func is_in(state_name: StringName) -> bool:
	return current != null and current.name == state_name

func transition_to(state_name: StringName, msg := {}, force := false) -> bool:
	if not states.has(state_name):
		push_warning("PlayerStateMachine: no state '%s'" % state_name)
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
func clip_finished(clip: String) -> void:
	if current != null: current.on_clip_finished(clip)
