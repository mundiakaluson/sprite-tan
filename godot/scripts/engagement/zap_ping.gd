@tool
class_name ZapPing
extends Node2D
## A quick ring on the grass: the scan ping of a skill card (Double Team) and the small flash where the zap lands.
## An actor of the stadium (projected like a player, so sizes are sprite pixels). Animation "ping" (edit it in the Animation panel) grows `radius`
## and fades `alpha`; the node frees itself when it ends. `start()` plays it.

@export var color := Color(0.35, 0.82, 1.0):
	set(v):
		color = v
		queue_redraw()
@export var radius := 6.0:
	set(v):
		radius = v
		queue_redraw()
@export_range(0.0, 1.0) var alpha := 0.5:
	set(v):
		alpha = v
		queue_redraw()
## the ring is squashed like the pitch seen from the camera
@export var squash := 0.45
@export var width := 1.0

func _ready() -> void:
	z_index = -3
	if not Engine.is_editor_hint(): $AnimationPlayer.animation_finished.connect(func(_n): queue_free())

func start(anim := "ping") -> void:
	$AnimationPlayer.play(anim)

func _draw() -> void:
	if alpha <= 0.0: return
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, squash))
	draw_arc(Vector2.ZERO, radius, 0.0, TAU, 32, Color(color, alpha), width)
