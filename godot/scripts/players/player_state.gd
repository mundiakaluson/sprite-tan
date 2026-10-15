class_name PlayerState
extends Node
## Base class for one player state. Override what you need. Use `player` (the Player) and `sm` (the PlayerStateMachine).
## Rules of thumb: enter() starts the animation, update() watches for reasons to leave, exit() cleans up; never change state from exit().

var player
var sm

## msg carries anything the previous state or the caller wants to pass in ({"clip": "...", "target": Vector2, ...})
func enter(_msg := {}) -> void: pass
func exit() -> void: pass
func update(_delta: float) -> void: pass
func physics_update(_delta: float) -> void: pass
func on_event(_ev: StringName, _data := {}) -> void: pass
func on_clip_finished(_clip: String) -> void: pass
