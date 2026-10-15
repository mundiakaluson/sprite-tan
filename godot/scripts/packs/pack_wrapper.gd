@tool
class_name PackWrapper
extends Control
## A pack wrapper (assets/packs/<pack_id>.png, drawn from data/packs.csv by the export) with its animations in the AnimationPlayer child:
## appear, hover_in / hover_out (automatic), tremble (charging), open (placeholder punch; the dust disintegration is still to be ported from
## packs/opening.py). Edit them in the editor: select the AnimationPlayer node. Code only calls play().
##   var w := PackWrapper.new_pack("weekly"); add_child(w); w.play("appear"); w.play_open(); await w.opened

signal opened

const SCENE := "res://scenes/packs/pack_wrapper.tscn"

@export var pack_id := "player":
	set(v):
		pack_id = v
		queue_redraw()
## size multiplier used by the animations (drawn around the wrapper centre, so the node's own scale is yours to use)
@export var fx_scale := 1.0:
	set(v):
		fx_scale = v
		queue_redraw()
## sideways shake in pixels (tremble animation)
@export var fx_shake := 0.0:
	set(v):
		fx_shake = v
		queue_redraw()

static func new_pack(id: String) -> PackWrapper:
	var w := (load(SCENE) as PackedScene).instantiate() as PackWrapper
	w.pack_id = id
	return w

func _init() -> void:
	custom_minimum_size = Vector2(64, 96)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func _draw() -> void:
	var dx := sin(Time.get_ticks_msec() * 0.09) * fx_shake
	draw_set_transform(Vector2(32 + dx, 48) - Vector2(32, 48) * fx_scale, 0.0, Vector2(fx_scale, fx_scale))
	var t := Data.tex("packs/%s.png" % pack_id)
	if t == null:
		draw_rect(Rect2(0, 0, 64, 96), Color(0.1, 0.1, 0.16))
		draw_string(ThemeDB.fallback_font, Vector2(6, 50), "no data", HORIZONTAL_ALIGNMENT_LEFT, 52, 10, Color.WHITE)
		return
	draw_texture(t, Vector2.ZERO)

func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_ENTER: play("hover_in")
	elif what == NOTIFICATION_MOUSE_EXIT: play("hover_out")

func play(anim_name: String) -> void:
	var ap := get_node_or_null("AnimationPlayer") as AnimationPlayer
	if ap == null or Engine.is_editor_hint() or not ap.has_animation(anim_name): return
	ap.play(anim_name)

## tremble, then open; emits `opened` at the end so the opening scene can show the cards
func play_open() -> void:
	var ap := get_node_or_null("AnimationPlayer") as AnimationPlayer
	if ap == null: opened.emit(); return
	ap.play("tremble")
	await ap.animation_finished
	ap.play("open")
	await ap.animation_finished
	opened.emit()
