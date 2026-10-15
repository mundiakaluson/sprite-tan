class_name MatchHud
extends CanvasLayer
## Match HUD. It is a real scene (scenes/match/match_hud.tscn, instanced in match.tscn) so you can open it, select any node and move / restyle it in the editor:
## Score, Who (selected player), Orders (the four order buttons, named Order_<id>), CommandBox (the current command), Message (GOAL!, KICK OFF), Controls (help text),
## Hand (the skill cards are added here), TeamTitle / TeamGrid (the stance buttons are added here), Overlay (rings and aim lines over the pitch). This script only fills them in.
## The pitch view is everything above the Strip node (the match scene follows the strip height), so nothing covers the play.
## Layout: every group is a panel with its parts inside (OrdersPanel > Who, Orders; HandPanel > Hand; TeamPanel > TeamTitle, TeamGrid, TeamNote; CommandPanel > title, note). Move or resize any node in the 2D view.
## No pop-ups: orders are buttons in the strip. Cards are the real SkillCard faces; the number on a card is its cooldown in seconds.

signal menu_chosen(id: String)          ## an order button was pressed ("through", "run", "press", "tackle")
signal card_pressed(index: int)         ## a card in the hand was clicked
signal team_command(id: String)         ## a team command button was pressed

## size of the hover tooltip (the card's tooltip image x this)
@export_range(1.0, 4.0, 1.0) var tooltip_scale := 2.0

signal strip_changed(height: float)    ## the Strip node was moved / resized in the scene: the pitch view takes the rest of the screen
## colour of each command kind in the command box and on the highlighted players
const KIND_COLORS := {"pass": Color(1, 1, 1), "through": Color(0.35, 0.9, 1.0), "lob": Color(1.0, 0.9, 0.3), "shoot": Color(1.0, 0.4, 0.35), "run": Color(0.5, 1.0, 0.5),
	"press": Color(1.0, 0.65, 0.3), "tackle": Color(1.0, 0.65, 0.3), "card": Color(0.8, 0.6, 1.0), "team": Color(0.6, 0.75, 1.0)}

@onready var _scorebug: Scorebug = %Scorebug
@onready var _who: PixelLabel = %Who
@onready var _msg: PixelLabel = %Message
@onready var _team_panel: PixelPanel = %TeamPanel
@onready var _cmd_panel: PixelPanel = %CommandPanel
@onready var _hand: HandBar = %Hand
@onready var _strip: Control = %Strip
@onready var _team_grid: StanceGrid = %TeamGrid
@onready var _team_note: PixelLabel = %TeamNote
@onready var _cmd_title: PixelLabel = %CommandTitle
@onready var _hint: PixelLabel = %CommandNote
@onready var _overlay: HudOverlay = %Overlay
@onready var _orders: Container = %Orders

var _hint_base := ""
var _team_accent := PixelUi.STEEL
var _order_buttons := {}
var _cards: Array[SkillCard] = []
var command: MatchCommand
var _team_buttons := {}
var snap_node: Node2D
var snap_kind := ""
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
	_overlay.hud = self
	_strip.resized.connect(_fit_pitch)
	_fit_pitch()
	_msg.text = ""
	# the order buttons are the children of Orders named Order_<id>
	for b in _orders.get_children():
		var button := b as PixelButton
		if button == null: continue
		var id := String(button.name).trim_prefix("Order_")
		button.disabled = true
		button.pressed.connect(func(): menu_chosen.emit(id))
		_order_buttons[id] = button
	_show_command()

## height of the HUD strip: the pitch view is everything above it. Move the Strip node's top edge in the scene to change it.
func strip_height() -> float:
	return _strip.offset_bottom - _strip.offset_top    # the strip is anchored to the bottom, so this is its height at any window size

func _fit_pitch() -> void:
	var h := strip_height()
	_overlay.offset_bottom = -h
	strip_changed.emit(h)

func _process(dt: float) -> void:
	if _msg_t > 0.0:
		_msg_t -= dt
		if _msg_t <= 0.0: _msg.text = ""
	if _toast_t > 0.0:
		_toast_t -= dt
		if _toast_t <= 0.0: _show_command()

## game_seconds = match clock in game seconds (0-5400); reds / added come from the rules when they exist
func set_score(h: int, a: int, game_seconds: float, h_reds := 0, a_reds := 0, added := 0) -> void:
	if _scorebug == null: return
	var m := int(game_seconds / 60.0)
	var per := "1ST HALF" if game_seconds < 2700.0 else "2ND HALF"
	_scorebug.update_state(h, a, h_reds, a_reds, "%d:%02d" % [m, int(game_seconds) % 60], per, added)

## names, ranked flag and stakes of the scoreboard (from MatchSettings)
func setup_scoreboard(s: MatchSettings, home_color: Color, away_color: Color) -> void:
	if _scorebug == null: return
	_scorebug.ranked = s.ranked
	_scorebug.home_name = s.home_name
	_scorebug.away_name = s.away_name
	_scorebug.division = s.division
	_scorebug.win_points = s.win_points
	_scorebug.loss_points = s.loss_points
	_scorebug.home_color = home_color
	_scorebug.away_color = away_color

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
		box.custom_minimum_size = _hand.card_size()
		var card := SkillCard.new_card(String(r["id"]))
		card.scale = Vector2.ONE * _hand.card_scale
		box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
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
		var b := PixelButton.new()
		b.text = String(cmd["label"])
		b.custom_minimum_size = _team_grid.button_size
		b.text_scale = 2
		b.accent = _team_accent
		b.toggle_mode = true
		b.tooltip_text = String(cmd.get("note", ""))
		var id := String(cmd["id"])
		b.pressed.connect(func(): team_command.emit(id))
		_team_grid.add_child(b)
		_team_buttons[id] = b

## the home team's colour tints the score and team panels and the lit stance button
func set_team_colors(home: Color, _away: Color) -> void:
	_team_accent = home
	_team_panel.accent = home
	for k in _team_buttons: _team_buttons[k].accent = home

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
		_cmd_panel.accent = PixelUi.STEEL
		if _toast_t <= 0.0: _hint.text = _hint_base
		return
	var t := command.text
	if command.target != null: t += "  >  " + command.target.display_name()
	elif command.who != null and command.kind in ["run", "press", "tackle", "card"]: t += "  " + command.who.display_name()
	_cmd_title.text = t
	_cmd_title.modulate = KIND_COLORS.get(command.kind, Color.WHITE)
	_cmd_panel.accent = KIND_COLORS.get(command.kind, PixelUi.STEEL)
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

func card_used(i: int) -> void:
	if i < _cards.size(): _cards[i].play("use")
