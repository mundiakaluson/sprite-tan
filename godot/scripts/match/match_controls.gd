class_name MatchControls
extends Node
## Mouse and controller orders. One flow for both, because the controller just drives the mouse pointer.
##   Double click a team mate        -> the ball carrier passes to him.
##   Right click (a mate or a spot)  -> lob there.
##   Drag from the ball carrier      -> shoot: time slows a little while you drag so you can line it up; let go to hit it where the arrow points.
##   Drag from any other player      -> he runs there by himself (a run); the AI takes over when he arrives.
##   Click a player                  -> his order buttons light up in the HUD strip (Through / Run with the ball; Run / Press / Tackle without). Then click a team mate or a spot.
##   Esc / Circle cancels. Click a skill card with a player selected to play it with him.
## Controller: left stick moves the pointer, Cross = click (twice = double click), Square = right click (lob), Triangle held = press and hold (drag), Circle = cancel.
## The stick moves the real mouse cursor and Cross / Triangle send real left-button events, so buttons, cards and the pitch react exactly like the mouse.
## Input Map: ptr_left/right/up/down, ptr_click, ptr_grab, ptr_lob, ptr_cancel.

@export var cursor_speed := 520.0       ## pixels per second at full stick
@export var drag_threshold := 8.0       ## pixels the pointer must move with the button down before it counts as a drag
@export var pick_radius := 20.0         ## how close to a player's body a click counts as on him
@export var double_click_ms := 350

enum Mode { IDLE, MENU, AIMING }

var game: MatchGame
var hud: MatchHud
var mode := Mode.IDLE
var order := ""
var selected: Footballer
var _down: Footballer
var _down_pos := Vector2.ZERO
var _dragging := false
var _shot_drag := false
var _skip_release := false
var _last_click: Footballer
var _last_click_ms := 0

func setup(g: MatchGame, h: MatchHud) -> void:
	game = g
	hud = h
	hud.menu_chosen.connect(_on_menu)

func _process(dt: float) -> void:
	if game == null: return
	var vp := get_viewport()
	var real_dt := dt / maxf(Engine.time_scale, 0.05)       # the pointer is not slowed by slow motion
	var stick := Input.get_vector("ptr_left", "ptr_right", "ptr_up", "ptr_down", 0.2)
	if stick != Vector2.ZERO:
		vp.warp_mouse((vp.get_mouse_position() + stick * cursor_speed * real_dt).clamp(Vector2.ZERO, vp.get_visible_rect().size - Vector2.ONE))
	var p := vp.get_mouse_position()
	if _down != null and not _dragging and p.distance_to(_down_pos) > drag_threshold:
		_dragging = true
		hud.set_orders([])
		_set_selected(_down)
		_shot_drag = game.carrier == _down
		game.set_slowmo(_shot_drag)
		if _shot_drag: hud.set_hint("Line up the shot, let go to shoot")
	if _dragging: hud.set_drag(_down.node.position, p, _shot_drag)
	hud.set_aim(mode == Mode.AIMING, p)

func _input(ev: InputEvent) -> void:
	# controller buttons become real left-button events at the pointer
	if ev.is_action_pressed("ptr_click"):
		_fake_left(true)
		_fake_left(false)
	elif ev.is_action_pressed("ptr_grab"):
		_fake_left(true)
	elif ev.is_action_released("ptr_grab"):
		_fake_left(false)

func _unhandled_input(ev: InputEvent) -> void:
	if game == null: return
	if ev.is_action_pressed("ptr_cancel"):
		clear()
		return
	if ev.is_action_pressed("ptr_lob"):
		_lob(get_viewport().get_mouse_position())
		return
	var mb := ev as InputEventMouseButton
	if mb == null or mb.button_index != MOUSE_BUTTON_LEFT: return
	if mb.pressed: _press(mb.position)
	else: _release(mb.position)

func _fake_left(down: bool) -> void:
	var ev := InputEventMouseButton.new()
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = down
	ev.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
	ev.position = get_viewport().get_mouse_position()
	ev.global_position = ev.position
	Input.parse_input_event(ev)

# ---------------------------------------------------------------- pointer
func _press(p: Vector2) -> void:
	_skip_release = false
	_down = _pick(p)
	_down_pos = p
	_dragging = false
	_shot_drag = false
	var now := Time.get_ticks_msec()
	if _down != null and _down == _last_click and now - _last_click_ms < double_click_ms:
		# double click on a team mate: the carrier passes to him
		_last_click = null
		_skip_release = true
		var passer := game.carrier
		if passer != null and passer.team == game.home and passer != _down:
			game.orders.pass_to(passer, "pass", _down, Vector2.INF)
		clear()

func _release(p: Vector2) -> void:
	if _skip_release:
		_skip_release = false
		_down = null
		return
	if _down != null and _dragging:
		var spot := _ground(p)
		if spot != Vector2.INF:
			if _shot_drag: game.orders.shoot_at(_down, spot)
			else: game.orders.run(_down, spot)
		clear()
	elif mode == Mode.AIMING and selected != null:
		_confirm_aim(p)
	elif _down != null:
		_select(_down)
		_last_click = _down
		_last_click_ms = Time.get_ticks_msec()
	else:
		clear()
	_down = null
	_dragging = false
	_shot_drag = false
	game.set_slowmo(false)
	hud.clear_drag()

func _lob(p: Vector2) -> void:
	var lober := game.carrier
	if lober == null or lober.team != game.home:
		hud.toast("Right click lobs: your team needs the ball")
		return
	var mate := _pick(p)
	game.orders.pass_to(lober, "lob", mate if mate != lober else null, _ground(p))
	clear()

func _pick(p: Vector2) -> Footballer:
	var best: Footballer = null
	var bd := 1e9
	for f in game.home.players:
		if not f.node.visible: continue
		var sc := f.node.scale.y
		var body := f.node.position + Vector2(0.0, -13.0 * sc)
		var d := body.distance_to(p)
		if d < maxf(pick_radius, 11.0 * sc) and d < bd:
			bd = d
			best = f
	return best

func _ground(p: Vector2) -> Vector2:
	var g := game.stadium.ground_at(p)
	if g == Vector3.INF: return Vector2.INF
	return Vector2(g.x, g.z)

# ---------------------------------------------------------------- selection and orders
func _set_selected(f: Footballer) -> void:
	selected = f
	game.selected = f
	hud.set_selected(f.node if f != null else null)

func _select(f: Footballer) -> void:
	_set_selected(f)
	mode = Mode.MENU
	order = ""
	hud.set_orders(game.orders.menu_for(f))
	hud.set_hint("%s: pick an order below, or drag to a spot" % f.display_name())

func _on_menu(id: String) -> void:
	if selected == null: return
	hud.set_orders([])
	if id == "press":
		game.orders.press(selected)
		clear()
	elif id == "tackle":
		game.orders.tackle(selected)
		clear()
	else:
		order = id
		mode = Mode.AIMING
		hud.set_hint("Through ball: click a team mate or a spot" if id == "through" else "Run: click where to run")

func _confirm_aim(p: Vector2) -> void:
	var mate := _pick(p)
	var spot := _ground(p)
	if mate == null and spot == Vector2.INF: return
	if order == "run":
		if spot != Vector2.INF: game.orders.run(selected, spot)
	else:
		game.orders.pass_to(selected, order, mate if mate != selected else null, spot)
	clear()

func clear() -> void:
	mode = Mode.IDLE
	order = ""
	selected = null
	_down = null
	_dragging = false
	_shot_drag = false
	if game != null:
		game.selected = null
		game.set_slowmo(false)
	if hud != null:
		hud.set_selected(null)
		hud.set_orders([])
		hud.clear_drag()
		hud.set_hint("")
