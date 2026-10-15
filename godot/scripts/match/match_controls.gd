class_name MatchControls
extends Node
## Mouse and controller orders. One flow for both, because the controller just drives the mouse pointer.
##   Click a player of yours  -> an order menu opens next to him (with the ball: Pass, Through, Lob, Shoot; without: Run, Press, Tackle).
##   Pass / Through / Lob / Run -> then click a team mate (or a spot on the grass) to say where.
##   Drag from a player to a spot -> he runs there by himself (a run). Dragging from the ball carrier dribbles there.
##   Right click / Esc / Circle   -> cancel. Click a skill card with a player selected to play it.
## Controller: left stick moves the pointer, Cross = click, Triangle held = press and hold (drag), Circle = cancel. The stick moves the real mouse cursor and
## Cross / Triangle send real left-button events, so buttons, cards and the pitch all react exactly like the mouse. Input Map: ptr_left/right/up/down, ptr_click, ptr_grab, ptr_cancel.

@export var cursor_speed := 520.0       ## pixels per second at full stick
@export var drag_threshold := 8.0       ## pixels the pointer must move with the button down before it counts as a drag
@export var pick_radius := 20.0         ## how close to a player's body a click counts as on him

enum Mode { IDLE, MENU, AIMING }

var game: MatchGame
var hud: MatchHud
var mode := Mode.IDLE
var order := ""
var selected: Footballer
var _down: Footballer
var _down_pos := Vector2.ZERO
var _dragging := false

func setup(g: MatchGame, h: MatchHud) -> void:
	game = g
	hud = h
	hud.menu_chosen.connect(_on_menu)

func _process(dt: float) -> void:
	if game == null: return
	var vp := get_viewport()
	var stick := Input.get_vector("ptr_left", "ptr_right", "ptr_up", "ptr_down", 0.2)
	if stick != Vector2.ZERO:
		var to := (vp.get_mouse_position() + stick * cursor_speed * dt).clamp(Vector2.ZERO, vp.get_visible_rect().size - Vector2.ONE)
		vp.warp_mouse(to)
	var p := vp.get_mouse_position()
	if _down != null and not _dragging and p.distance_to(_down_pos) > drag_threshold:
		_dragging = true
		hud.hide_menu()
		_set_selected(_down)
	if _dragging: hud.set_drag(_down.node.position, p)
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
	_down = _pick(p)
	_down_pos = p
	_dragging = false

func _release(p: Vector2) -> void:
	if _down != null and _dragging:
		var spot := _ground(p)
		if spot != Vector2.INF: game.order_run(_down, spot)
		clear()
	elif mode == Mode.AIMING and selected != null:
		_confirm_aim(p)
	elif _down != null:
		_select(_down)
	else:
		clear()
	_down = null
	_dragging = false
	hud.clear_drag()

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
	hud.show_menu(f.node.position, game.menu_for(f))
	hud.set_hint("%s: choose an order, or drag to a spot to make a run" % f.display_name())

func _on_menu(id: String) -> void:
	if selected == null: return
	hud.hide_menu()
	if id == "shoot":
		game.order_shoot(selected)
		clear()
	elif id == "press":
		game.order_press(selected)
		clear()
	elif id == "tackle":
		game.order_tackle(selected)
		clear()
	else:
		order = id
		mode = Mode.AIMING
		hud.set_hint("%s: click a team mate or a spot" % id.capitalize() if id != "run" else "Run: click where to run")

func _confirm_aim(p: Vector2) -> void:
	var mate := _pick(p)
	var spot := _ground(p)
	if mate == null and spot == Vector2.INF: return
	if order == "run":
		if spot != Vector2.INF: game.order_run(selected, spot)
	else:
		game.order_pass(selected, order, mate if mate != selected else null, spot)
	clear()

func clear() -> void:
	mode = Mode.IDLE
	order = ""
	selected = null
	if game != null: game.selected = null
	if hud != null:
		hud.set_selected(null)
		hud.hide_menu()
		hud.clear_drag()
		hud.set_hint("")
	_down = null
	_dragging = false
