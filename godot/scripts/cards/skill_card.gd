@tool
class_name SkillCard
extends Control
## A skill card: the exported card face (assets/cards/<id>.png) with its animations in the AnimationPlayer child:
## appear, hover_in / hover_out (automatic), ready, unavailable, use (flash, then dim as on cooldown), cooldown_end.
## Edit or add animations in the editor: select the AnimationPlayer node. The hover tooltip is the exported tooltip image.
##   var c := SkillCard.new_card("SH01"); add_child(c); c.play("appear"); ... c.play("use"); ... c.play("cooldown_end")

signal pressed(card_id: String)

const SCENE := "res://scenes/cards/skill_card.tscn"

@export var card_id := "SH01":
	set(v):
		card_id = v
		queue_redraw()
## size multiplier used by the hover / appear / use animations (drawn around the card centre, so the node's own scale is yours to use)
@export var fx_scale := 1.0:
	set(v):
		fx_scale = v
		queue_redraw()
## how big the hover tooltip is drawn (its image pixels x this)
@export_range(1.0, 4.0) var tooltip_scale := 3.0
## cooldown turns left, drawn on the card while > 0
@export var cooldown_left := 0:
	set(v):
		cooldown_left = v
		queue_redraw()

static func new_card(id: String) -> SkillCard:
	var c := (load(SCENE) as PackedScene).instantiate() as SkillCard
	c.card_id = id
	return c

func _init() -> void:
	custom_minimum_size = Vector2(64, 90)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

func _draw() -> void:
	draw_set_transform(Vector2(32, 45) * (1.0 - fx_scale), 0.0, Vector2(fx_scale, fx_scale))
	var t := Data.tex("cards/%s.png" % card_id)
	if t == null:
		draw_rect(Rect2(0, 0, 64, 90), Color(0.1, 0.1, 0.16))
		draw_string(ThemeDB.fallback_font, Vector2(6, 46), "no data", HORIZONTAL_ALIGNMENT_LEFT, 52, 10, Color.WHITE)
		return
	draw_texture_rect(t, Rect2(0, 0, 64, 90), false)
	if cooldown_left > 0:
		var s := str(cooldown_left)
		PixelText.draw(self, Vector2(32 - PixelText.width(s, 3) / 2.0, 36), s, Color.WHITE, 3)

func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_ENTER: play("hover_in")
	elif what == NOTIFICATION_MOUSE_EXIT: play("hover_out")

func _gui_input(ev: InputEvent) -> void:
	var mb := ev as InputEventMouseButton
	if mb != null and mb.pressed and mb.button_index == MOUSE_BUTTON_LEFT: pressed.emit(card_id)

## play one of the card's animations (ignored in the editor and if the name does not exist)
func play(anim_name: String) -> void:
	var ap := get_node_or_null("AnimationPlayer") as AnimationPlayer
	if ap == null or Engine.is_editor_hint() or not ap.has_animation(anim_name): return
	ap.play(anim_name)

func _make_custom_tooltip(_for_text: String) -> Object:
	var t := Data.tex("cards/%s_tip.png" % card_id)
	if t == null: return null
	var r := TextureRect.new()
	r.texture = t
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.custom_minimum_size = t.get_size() * tooltip_scale
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	return r

func _get_tooltip(_at: Vector2) -> String:
	return card_id      # any non-empty text turns the custom tooltip on
