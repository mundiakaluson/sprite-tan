class_name MatchHud
extends CanvasLayer
## Match HUD (built in code, so the scene stays one node). The pitch has its own area (the top 420 px of the 960 x 540 game viewport, a SubViewport in match.tscn);
## the HUD lives in the strip below it so nothing covers the play: score / clock / selected player / hint on the left, the hand of skill cards in the middle,
## the controls on the right. No pop-ups: the order buttons live in the strip (they light up for the selected player). Only short messages (GOAL!, KICK OFF),
## the selection ring and the aim lines are drawn over the pitch.
## Cards are the real SkillCard faces; the number on a card is its cooldown in seconds.

signal menu_chosen(id: String)          ## an order button was pressed ("through", "run", "press", "tackle")
signal card_pressed(index: int)         ## a card in the hand was clicked

const PITCH_H := 420.0                  ## the pitch view is the top part of the screen, the HUD strip the rest
const CONTROLS := "MOUSE\ndouble click mate: pass\nright click: lob\ndrag from ball carrier: shoot\ndrag from player: run\nclick player: orders\nEsc: cancel\n\nPAD\nstick pointer, Cross click\nSquare lob, hold Triangle drag\nCircle cancel"
const ORDERS := ["through", "run", "press", "tackle"]

var _score: Label
var _msg: Label
var _hint_base := ""
var _order_buttons := {}
var _who: Label
var _hand: HBoxContainer
var _cards: Array[SkillCard] = []
var _hint: Label
var _overlay: Control
var selected_node: Node2D
var drag_from := Vector2.ZERO
var drag_to := Vector2.ZERO
var dragging := false
var drag_shot := false
var aiming := false
var aim_to := Vector2.ZERO
var _msg_t := 0.0
var _toast_t := 0.0

func _ready() -> void:
	var root := Control.new()
	root.size = Vector2(960, 540)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	_overlay = _Overlay.new()
	_overlay.hud = self
	_overlay.size = Vector2(960, PITCH_H)
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_overlay)
	# the strip under the pitch
	var strip := ColorRect.new()
	strip.color = Color(0.07, 0.08, 0.12)
	strip.position = Vector2(0, PITCH_H)
	strip.size = Vector2(960, 540.0 - PITCH_H)
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(strip)
	var line := ColorRect.new()
	line.color = Color(0.3, 0.32, 0.4)
	line.position = Vector2(0, PITCH_H)
	line.size = Vector2(960, 2)
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(line)
	_score = _label(root, 18)
	_score.position = Vector2(10, PITCH_H + 3)
	_who = _label(root, 11)
	_who.position = Vector2(10, PITCH_H + 26)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.position = Vector2(10, PITCH_H + 46)
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(grid)
	for id in ORDERS:
		var b := Button.new()
		b.text = String(id).to_upper()
		b.custom_minimum_size = Vector2(92, 22)
		b.add_theme_font_size_override("font_size", 10)
		b.disabled = true
		b.focus_mode = Control.FOCUS_NONE
		var order_id: String = id
		b.pressed.connect(func(): menu_chosen.emit(order_id))
		grid.add_child(b)
		_order_buttons[id] = b
	_hint = _label(root, 9)
	_hint.position = Vector2(10, PITCH_H + 98)
	_hint.custom_minimum_size = Vector2(190, 0)
	_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_msg = _label(root, 30)
	_msg.position = Vector2(180, 150)
	_msg.custom_minimum_size = Vector2(600, 0)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var controls := _label(root, 8)
	controls.position = Vector2(776, PITCH_H + 4)
	controls.text = CONTROLS
	controls.modulate = Color(1, 1, 1, 0.75)
	_hand = HBoxContainer.new()
	_hand.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hand.add_theme_constant_override("separation", 6)
	_hand.position = Vector2(208, PITCH_H + 12)
	root.add_child(_hand)

func _label(parent: Node, size: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 4)
	parent.add_child(l)
	return l

func _process(dt: float) -> void:
	if _msg_t > 0.0:
		_msg_t -= dt
		if _msg_t <= 0.0: _msg.text = ""
	if _toast_t > 0.0:
		_toast_t -= dt
		if _toast_t <= 0.0: _hint.text = _hint_base

func set_score(h: int, a: int, minute: int) -> void:
	if _score != null: _score.text = "HOME %d - %d AWAY   %d'" % [h, a, minute]

func set_controlled(who: String) -> void:
	if _who != null: _who.text = who

func message(text: String, seconds := 2.0) -> void:
	if _msg == null: return
	_msg.text = text
	_msg_t = seconds

func toast(text: String, seconds := 1.6) -> void:
	if _hint == null: return
	_hint.text = text
	_toast_t = seconds

func set_hand(rows: Array) -> void:
	for c in _cards: c.queue_free()
	_cards.clear()
	var i := 1
	for r in rows:
		var box := VBoxContainer.new()
		box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var card := SkillCard.new_card(String(r["id"]))
		box.add_child(card)
		_hand.add_child(box)
		_cards.append(card)
		var idx := i - 1
		card.pressed.connect(func(_id): card_pressed.emit(idx))
		card.play("appear")
		i += 1

func set_cooldowns(cd: Dictionary) -> void:
	for i in _cards.size():
		var left := int(ceil(float(cd.get(_cards[i].card_id, 0.0))))
		if _cards[i].cooldown_left != left:
			_cards[i].cooldown_left = left
			if left == 0: _cards[i].play("cooldown_end")

# ---- orders: menu, hint, selection ring, drag and aim lines
## light up the order buttons that make sense for the selected player (an empty list greys them all)
func set_orders(options: Array) -> void:
	for id in _order_buttons:
		_order_buttons[id].disabled = not (id in options)

func set_hint(text: String) -> void:
	_hint_base = text
	if _hint != null and _toast_t <= 0.0: _hint.text = text

func set_selected(n: Node2D) -> void:
	selected_node = n

func set_drag(from: Vector2, to: Vector2, shot := false) -> void:
	dragging = true
	drag_shot = shot
	drag_from = from
	drag_to = to

func clear_drag() -> void:
	dragging = false

func set_aim(on: bool, to: Vector2) -> void:
	aiming = on
	aim_to = to

class _Overlay extends Control:
	var hud

	func _process(_dt: float) -> void:
		queue_redraw()

	func _draw() -> void:
		if hud == null: return
		var n: Node2D = hud.selected_node
		if n != null and is_instance_valid(n):
			var sc := n.scale.x
			draw_set_transform(n.position, 0.0, Vector2(1.0, 0.45))
			draw_arc(Vector2.ZERO, 12.0 * sc, 0.0, TAU, 32, Color(1.0, 0.9, 0.2), 2.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
			if hud.aiming:
				draw_line(n.position, hud.aim_to, Color(1.0, 0.9, 0.3, 0.8), 1.5)
				draw_circle(hud.aim_to, 4.0, Color(1.0, 0.9, 0.3, 0.9))
		if hud.dragging:
			var d: Vector2 = hud.drag_to - hud.drag_from
			var col := Color(1.0, 0.35, 0.3, 0.95) if hud.drag_shot else Color(1, 1, 1, 0.95)
			draw_line(hud.drag_from, hud.drag_to, col, 2.0)
			if d.length() > 6.0:
				var u := d.normalized()
				var side := Vector2(-u.y, u.x)
				draw_colored_polygon(PackedVector2Array([hud.drag_to, hud.drag_to - u * 9.0 + side * 5.0, hud.drag_to - u * 9.0 - side * 5.0]), col)

func card_used(i: int) -> void:
	if i < _cards.size(): _cards[i].play("use")
