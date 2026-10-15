class_name MatchHud
extends CanvasLayer
## Match HUD (built in code, so the scene stays one node): score and clock on top, the hand of skill cards along the bottom, the player you control bottom left,
## messages (GOAL!, KICK OFF) in the middle and short toasts under the score. Cards are the real SkillCard faces; the number on a card is its cooldown in seconds.
## Laid out for the 960 x 540 game viewport (project settings).

const CONTROLS := "WASD / arrows move    Shift sprint    J pass (tackle without the ball)    L lob    K shoot    Q switch player    1-8 skill cards"

var _score: Label
var _msg: Label
var _toast: Label
var _who: Label
var _hand: HBoxContainer
var _cards: Array[SkillCard] = []
var _msg_t := 0.0
var _toast_t := 0.0

func _ready() -> void:
	var root := Control.new()
	root.size = Vector2(960, 540)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	var bar := PanelContainer.new()
	bar.position = Vector2(360, 6)
	root.add_child(bar)
	_score = _label(bar, 18)
	_score.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_score.custom_minimum_size = Vector2(240, 0)
	_toast = _label(root, 11)
	_toast.position = Vector2(330, 52)
	_toast.custom_minimum_size = Vector2(300, 0)
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg = _label(root, 30)
	_msg.position = Vector2(180, 190)
	_msg.custom_minimum_size = Vector2(600, 0)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_who = _label(root, 12)
	_who.position = Vector2(10, 396)
	var controls := _label(root, 9)
	controls.position = Vector2(10, 522)
	controls.text = CONTROLS
	controls.modulate = Color(1, 1, 1, 0.7)
	_hand = HBoxContainer.new()
	_hand.add_theme_constant_override("separation", 6)
	_hand.position = Vector2(203, 414)
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
		if _toast_t <= 0.0: _toast.text = ""

func set_score(h: int, a: int, minute: int) -> void:
	if _score != null: _score.text = "HOME %d - %d AWAY    %d'" % [h, a, minute]

func set_controlled(who: String) -> void:
	if _who != null: _who.text = who

func message(text: String, seconds := 2.0) -> void:
	if _msg == null: return
	_msg.text = text
	_msg_t = seconds

func toast(text: String, seconds := 1.6) -> void:
	if _toast == null: return
	_toast.text = text
	_toast_t = seconds

func set_hand(rows: Array) -> void:
	for c in _cards: c.queue_free()
	_cards.clear()
	var i := 1
	for r in rows:
		var box := VBoxContainer.new()
		var card := SkillCard.new_card(String(r["id"]))
		box.add_child(card)
		var k := Label.new()
		k.text = str(i)
		k.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		box.add_child(k)
		_hand.add_child(box)
		_cards.append(card)
		card.play("appear")
		i += 1

func set_cooldowns(cd: Dictionary) -> void:
	for i in _cards.size():
		var left := int(ceil(float(cd.get(_cards[i].card_id, 0.0))))
		if _cards[i].cooldown_left != left:
			_cards[i].cooldown_left = left
			if left == 0: _cards[i].play("cooldown_end")

func card_used(i: int) -> void:
	if i < _cards.size(): _cards[i].play("use")
