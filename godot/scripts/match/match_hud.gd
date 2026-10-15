class_name MatchHud
extends CanvasLayer
## Match HUD (built in code, so the scene stays one node). The pitch has its own area (the top 420 px of the 960 x 540 game viewport, a SubViewport in match.tscn);
## the HUD lives in the strip below it so nothing covers the play: score / clock / selected player / hint on the left, the hand of skill cards in the middle,
## the controls on the right. No pop-ups: the order buttons live in the strip (they light up for the selected player). Only short messages (GOAL!, KICK OFF),
## the selection ring and the aim lines are drawn over the pitch.
## Cards are the real SkillCard faces; the number on a card is its cooldown in seconds.

signal menu_chosen(id: String)          ## an order button was pressed ("through", "run", "press", "tackle")
signal card_pressed(index: int)         ## a card in the hand was clicked

## size of the cards in the hand (1 = the full 64 x 90 card)
@export_range(0.4, 1.0) var card_scale := 0.75
## size of the hover tooltip (the card's tooltip image x this)
@export_range(1.0, 4.0) var tooltip_scale := 1.5

signal team_command(id: String)         ## a team command button was pressed

const PITCH_H := 420.0                  ## the pitch view is the top part of the screen, the HUD strip the rest
const CONTROLS := "MOUSE\ndouble click mate: pass\nright click: lob\ndrag from ball carrier: shoot\ndrag from player: run\nclick player: orders\nEsc: cancel\n\nPAD\nstick pointer, Cross click\nSquare lob, hold Triangle drag\nCircle cancel"
## colour of each command kind in the command box and on the highlighted players
const KIND_COLORS := {"pass": Color(1, 1, 1), "through": Color(0.35, 0.9, 1.0), "lob": Color(1.0, 0.9, 0.3), "shoot": Color(1.0, 0.4, 0.35), "run": Color(0.5, 1.0, 0.5),
	"press": Color(1.0, 0.65, 0.3), "tackle": Color(1.0, 0.65, 0.3), "card": Color(0.8, 0.6, 1.0), "team": Color(0.6, 0.75, 1.0)}
const ORDERS := ["through", "run", "press", "tackle"]

var _score: Label
var _msg: Label
var _hint_base := ""
var _order_buttons := {}
var _who: Label
var _hand: HBoxContainer
var _team_grid: GridContainer
var _team_note: Label
var _cards: Array[SkillCard] = []
var _hint: Label
var _cmd_title: Label
var _cmd_box: Panel
var command: MatchCommand
var _team_buttons := {}
var snap_node: Node2D
var snap_kind := ""
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
	grid.position = Vector2(10, PITCH_H + 44)
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(grid)
	for id in ORDERS:
		var b := Button.new()
		b.text = String(id).to_upper()
		b.custom_minimum_size = Vector2(92, 18)
		b.add_theme_font_size_override("font_size", 9)
		b.disabled = true
		b.focus_mode = Control.FOCUS_NONE
		var order_id: String = id
		b.pressed.connect(func(): menu_chosen.emit(order_id))
		grid.add_child(b)
		_order_buttons[id] = b
	# current command box: the one thing you are doing now (pass / through / shoot / run / card / team stance)
	_cmd_box = Panel.new()
	_cmd_box.position = Vector2(10, PITCH_H + 86)
	_cmd_box.size = Vector2(192, 31)
	_cmd_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.1, 0.11, 0.17)
	sb.border_color = Color(0.3, 0.32, 0.4)
	sb.set_border_width_all(1)
	_cmd_box.add_theme_stylebox_override("panel", sb)
	root.add_child(_cmd_box)
	_cmd_title = _label(_cmd_box, 11)
	_cmd_title.position = Vector2(5, 0)
	_hint = _label(_cmd_box, 8)
	_hint.position = Vector2(5, 17)
	_hint.custom_minimum_size = Vector2(182, 0)
	_hint.modulate = Color(1, 1, 1, 0.8)
	_show_command()
	_msg = _label(root, 30)
	_msg.position = Vector2(180, 150)
	_msg.custom_minimum_size = Vector2(600, 0)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	var controls := _label(root, 8)
	controls.position = Vector2(790, PITCH_H + 4)
	controls.text = CONTROLS
	controls.modulate = Color(1, 1, 1, 0.75)
	_hand = HBoxContainer.new()
	_hand.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hand.add_theme_constant_override("separation", 4)
	_hand.position = Vector2(208, PITCH_H + 12)
	root.add_child(_hand)
	# team commands (orders for the whole side): the room is here, the commands come next
	var team_x := 208.0 + 8.0 * 64.0 * card_scale + 7.0 * 4.0 + 14.0
	var team_title := _label(root, 9)
	team_title.text = "TEAM"
	team_title.position = Vector2(team_x, PITCH_H + 4)
	_team_grid = GridContainer.new()
	_team_grid.columns = 2
	_team_grid.position = Vector2(team_x, PITCH_H + 20)
	_team_grid.add_theme_constant_override("h_separation", 4)
	_team_grid.add_theme_constant_override("v_separation", 4)
	_team_grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_team_grid)
	_team_note = _label(root, 8)
	_team_note.text = "no commands yet"
	_team_note.position = Vector2(team_x, PITCH_H + 22)
	_team_note.modulate = Color(1, 1, 1, 0.5)

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
		if _toast_t <= 0.0: _show_command()

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
		var box := Control.new()
		box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.custom_minimum_size = Vector2(64, 90) * card_scale
		var card := SkillCard.new_card(String(r["id"]))
		card.scale = Vector2.ONE * card_scale
		card.tooltip_scale = tooltip_scale
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

## the team command buttons: [{"id": "press_high", "label": "PRESS HIGH"}, ...]. Pressing one emits team_command(id). An empty list shows "no commands yet".
func set_team_commands(commands: Array) -> void:
	for c in _team_grid.get_children(): c.queue_free()
	_team_buttons.clear()
	_team_note.visible = commands.is_empty()
	for cmd in commands:
		var b := Button.new()
		b.text = String(cmd["label"])
		b.custom_minimum_size = Vector2(64, 20)
		b.add_theme_font_size_override("font_size", 8)
		b.focus_mode = Control.FOCUS_NONE
		b.toggle_mode = true
		b.tooltip_text = String(cmd.get("note", ""))
		var id := String(cmd["id"])
		b.pressed.connect(func(): team_command.emit(id))
		_team_grid.add_child(b)
		_team_buttons[id] = b

## light the button of the stance in force
func set_team_active(id: String) -> void:
	for k in _team_buttons: _team_buttons[k].set_pressed_no_signal(k == id)

# ---- orders: menu, hint, selection ring, drag and aim lines
## light up the order buttons that make sense for the selected player (an empty list greys them all)
func set_orders(options: Array) -> void:
	for id in _order_buttons:
		_order_buttons[id].disabled = not (id in options)

func set_hint(text: String) -> void:
	_hint_base = text
	_show_command()

## the HUD box follows this store (MatchCommand); it can be any other command source
func bind_command(cmd: MatchCommand) -> void:
	command = cmd
	cmd.changed.connect(_show_command)
	_show_command()

func _show_command() -> void:
	if _cmd_title == null: return
	if command == null or command.kind == "":
		_cmd_title.text = "COMMAND: -"
		_cmd_title.modulate = Color(1, 1, 1, 0.5)
		if _toast_t <= 0.0: _hint.text = _hint_base
		return
	var t := command.text
	if command.target != null: t += "  >  " + command.target.display_name()
	elif command.who != null and command.kind in ["run", "press", "tackle", "card"]: t += "  " + command.who.display_name()
	_cmd_title.text = t
	_cmd_title.modulate = KIND_COLORS.get(command.kind, Color.WHITE)
	if _toast_t <= 0.0: _hint.text = command.note if command.note != "" else _hint_base

## the team mate a drag is snapping to (ringed on the pitch; a through ball marks him as the runner)
func set_snap(n: Node2D, kind: String) -> void:
	snap_node = n
	snap_kind = kind

func set_selected(n: Node2D) -> void:
	selected_node = n

func set_drag(from: Vector2, to: Vector2, shot := false) -> void:
	dragging = true
	drag_shot = shot
	drag_from = from
	drag_to = to

func clear_drag() -> void:
	dragging = false
	snap_node = null
	snap_kind = ""

func set_aim(on: bool, to: Vector2) -> void:
	aiming = on
	aim_to = to

class _Overlay extends Control:
	var hud

	func _process(_dt: float) -> void:
		queue_redraw()

	func _ring(n: Node2D, col: Color, radius: float, text: String) -> void:
		var sc := n.scale.x
		draw_set_transform(n.position, 0.0, Vector2(1.0, 0.45))
		draw_arc(Vector2.ZERO, radius * sc, 0.0, TAU, 32, col, 2.0)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		if text != "": draw_string(ThemeDB.fallback_font, n.position + Vector2(-9.0, -30.0 * sc), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, col)

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
		var cmd: MatchCommand = hud.command
		if cmd != null and cmd.target != null and cmd.target.node != null:
			_ring(cmd.target.node, MatchHud.KIND_COLORS.get(cmd.kind, Color.WHITE), 15.0, "RUN" if cmd.kind == "through" else "")
		if hud.snap_node != null and is_instance_valid(hud.snap_node):
			_ring(hud.snap_node, MatchHud.KIND_COLORS.get(hud.snap_kind, Color.WHITE), 17.0, "RUN" if hud.snap_kind == "through" else "")
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
