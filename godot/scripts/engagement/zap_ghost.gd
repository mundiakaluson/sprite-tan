@tool
class_name ZapGhost
extends Node2D
## One afterimage of a zap: a flat cyan silhouette of the player's current frame that fades out (Celeste-style dash ghost).
## An actor of the stadium. `copy_from(player)` takes his frame; animation "fade" (edit it in the Animation panel) runs `fade` down; the node frees itself after.

@export var tint := Color(0.35, 0.82, 1.0):
	set(v):
		tint = v
		_push()
@export_range(0.0, 1.0) var fade := 0.35:
	set(v):
		fade = v
		_push()

func _ready() -> void:
	_push()
	if not Engine.is_editor_hint(): $AnimationPlayer.animation_finished.connect(func(_n): queue_free())

## take the player's current picture (sheet, frame, direction, mirror)
func copy_from(p: Player) -> void:
	var src: Sprite2D = p.sprite
	var s: Sprite2D = $Sprite
	s.texture = src.texture
	s.region_enabled = src.region_enabled
	s.region_rect = src.region_rect
	s.centered = src.centered
	s.offset = src.offset
	s.position = src.position
	s.scale = src.scale
	s.flip_h = src.flip_h

func start() -> void:
	$AnimationPlayer.play("fade")

func _push() -> void:
	var s := get_node_or_null("Sprite") as Sprite2D
	if s == null: return
	var m := s.material as ShaderMaterial
	if m == null: return
	m.set_shader_parameter("tint", tint)
	m.set_shader_parameter("alpha", fade)
