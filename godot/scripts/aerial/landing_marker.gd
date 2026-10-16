class_name LandingMarker
extends Node2D
## The yellow ring on the grass where a ball in the air will land. MatchAerial moves it (stadium.set_actor_pos) and calls `show_at`; it shrinks as the ball comes down.

@export var color := Color(1.0, 0.9, 0.2)
@export var radius := 20.0
## the ring is squashed like the pitch seen from the camera
@export var squash := 0.5
var amount := 1.0          ## 1 = ball just kicked, 0 = about to land (ring shrinks)

func _ready() -> void:
	z_index = -3
	visible = false

func _draw() -> void:
	var r := radius * lerpf(0.55, 1.0, amount)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, squash))
	draw_arc(Vector2.ZERO, r, 0.0, TAU, 28, color, 2.0)
	draw_arc(Vector2.ZERO, r * 0.6, 0.0, TAU, 20, Color(color, 0.5), 1.5)
	draw_circle(Vector2.ZERO, 2.5, color)

func show_at(a: float) -> void:
	amount = a
	visible = true
	queue_redraw()

func hide_marker() -> void:
	visible = false
