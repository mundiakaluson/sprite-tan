class_name PlayerState
extends Node
## One state of a player's state machine. It is a NODE: add it under the Player's StateMachine in the scene tree and edit it in the inspector.
## Add the node "PlayerState" as it is for a no-code state (play a clip, and wire events / clip end to other states with the exports below),
## or attach a script that extends PlayerState when it needs logic. The node's NAME is the state's name ("Idle", "Run", ...).
## Inside code: `player` is the Player, `sm` the PlayerStateMachine. Override the _on_* functions, not enter()/exit().

@export_group("Animation")
## animation to play when the state starts: any name in the AnimationPlayer (a sprite sheet, e.g. "run", "kick", "base_idle"). Empty = play nothing.
## Arrows in the flow graph (data/animation_flow.csv) can continue it by themselves.
@export var clip := ""
@export_group("Movement")
## true = the player stops moving when the state starts
@export var stop_movement := true
@export_group("Wiring")
## event name -> state name. e.g. {"move_to": "Run", "play_action": "Action"}. Events come from Player.send_event / move_to / play_action
@export var event_transitions: Dictionary = {}
## state to go to when a non-looping clip ends (empty = stay)
@export var go_to_when_clip_ends: StringName = &""

var player
var sm

func enter(msg := {}) -> void:
	if stop_movement: player.velocity = Vector2.ZERO
	if clip != "": player.play_clip(clip)
	_on_enter(msg)

func exit() -> void:
	_on_exit()

func update(delta: float) -> void:
	_on_update(delta)

func physics_update(delta: float) -> void:
	_on_physics_update(delta)

func on_event(ev: StringName, data := {}) -> void:
	if not _on_event(ev, data):
		var to := str(event_transitions.get(str(ev), ""))
		if to != "": sm.transition_to(StringName(to), data)

func on_clip_finished(finished_clip: String) -> void:
	if not _on_clip_finished(finished_clip) and go_to_when_clip_ends != &"":
		sm.transition_to(go_to_when_clip_ends)

# ---- override these in your own state script ----
func _on_enter(_msg: Dictionary) -> void: pass
func _on_exit() -> void: pass
func _on_update(_delta: float) -> void: pass
func _on_physics_update(_delta: float) -> void: pass
## return true when you handled the event yourself (then event_transitions is skipped)
func _on_event(_ev: StringName, _data: Dictionary) -> bool: return false
## return true when you handled it yourself (then go_to_when_clip_ends is skipped)
func _on_clip_finished(_finished_clip: String) -> bool: return false
