extends Control
## Animation viewer (the Godot version of the tool's Animations preview): pick a player and any clip, play it, and ROTATE while it plays.
## Run this scene alone with F6. Rotate: Left/Right or A/D (Input Map: rotate_left / rotate_right), drag with the left mouse button,
## the Direction slider, or tick Spin. Also: filter the clip list, speed slider, Repeat, Pause. Direction 8 = screen right, 16 = camera.

@onready var player: Player = $Player
@onready var picker: OptionButton = %PlayerPicker
@onready var filter: LineEdit = %Filter
@onready var clip_list: ItemList = %Clips
@onready var direction_slider: HSlider = %Direction
@onready var spin: CheckButton = %Spin
@onready var spin_speed: HSlider = %SpinSpeed
@onready var speed: HSlider = %Speed
@onready var repeat: CheckButton = %Repeat
@onready var pause: CheckButton = %Pause
@onready var info: Label = %Info

var _angle := 16.0
var _clip := ""
var _shown: Array = []          # clip names in the list (after filtering)
const DRAG_STEP := 0.08         # directions per pixel of mouse drag

func _ready() -> void:
	if not Data.ok:
		info.text = "No exported data. Press Export to game in the manager tool first."
		return
	var rows := Data.table("players")
	for r in rows: picker.add_item("%s  %s" % [r["id"], r.get("name", "")])
	player.setup(rows[0])
	player.anim_tree.active = false          # the viewer drives the AnimationPlayer directly
	player.sm.locked = true
	picker.item_selected.connect(_on_player_picked)
	filter.text_changed.connect(func(_t): _fill_list())
	clip_list.item_selected.connect(_on_clip_picked)
	direction_slider.value_changed.connect(func(v): _set_angle(v))
	speed.value_changed.connect(func(_v): _apply_speed())
	pause.toggled.connect(func(_b): _apply_speed())
	player.anim_player.animation_finished.connect(_on_finished)
	_fill_list()
	_play("base_idle" if Data.anims.get("animations", {}).has("base_idle") else _shown[0])
	_set_angle(_angle)

func _fill_list() -> void:
	var q := filter.text.strip_edges().to_lower()
	var names: Array = Data.anims.get("animations", {}).keys()
	names.sort()
	_shown = names.filter(func(n): return q == "" or q in String(n).to_lower())
	clip_list.clear()
	for n in _shown: clip_list.add_item(n)
	var i := _shown.find(_clip)
	if i >= 0: clip_list.select(i)

func _on_player_picked(i: int) -> void:
	var r: Dictionary = Data.table("players")[i]
	player.row = r
	player.sprite.player_id = r["id"]

func _on_clip_picked(i: int) -> void:
	_play(_shown[i])

func _play(clip: String) -> void:
	_clip = clip
	player.anim_player.play(clip)
	_apply_speed()
	var m: Dictionary = Data.anims.get("animations", {}).get(clip, {})
	info.text = "%s\n%d frames, %d ms each, %s\nevents: %s" % [clip, int(m.get("frames", 0)), int(m.get("ms_per_frame", 0)), "loops" if m.get("loop", false) else "plays once", str(m.get("events", {}))]

func _on_finished(_name: StringName) -> void:
	if repeat.button_pressed and _clip != "": _play(_clip)

func _apply_speed() -> void:
	player.anim_player.speed_scale = 0.0 if pause.button_pressed else speed.value

func _set_angle(a: float) -> void:
	_angle = fposmod(a, 32.0)
	player.sprite.direction = int(round(_angle)) % 32
	direction_slider.set_value_no_signal(float(player.sprite.direction))

func _process(delta: float) -> void:
	if spin.button_pressed: _set_angle(_angle + spin_speed.value * delta)
	if Input.is_action_pressed("rotate_left"): _set_angle(_angle - 12.0 * delta)
	if Input.is_action_pressed("rotate_right"): _set_angle(_angle + 12.0 * delta)

func _unhandled_input(ev: InputEvent) -> void:
	var mm := ev as InputEventMouseMotion
	if mm != null and (mm.button_mask & MOUSE_BUTTON_MASK_LEFT) != 0:
		_set_angle(_angle + mm.relative.x * DRAG_STEP)
