@tool
class_name PlayerSprite
extends Sprite2D
## One animated, recoloured player. Sheets are frames across x direction rows (32 dirs, 40x40 cells). The shader reads the
## sprite pixels as UV lookups into the player's 96x24 look atlas.
## usage: var p := PlayerSprite.new(); add_child(p); p.setup("PL242"); p.play("run"); p.face(8)   # dir 8 = screen right, 16 = toward the camera

const SHADER := preload("res://shaders/uv_skin.gdshader")
@export_group("Editor preview")
## player whose look is shown (in game the Player sets this itself)
@export var player_id := "PL242":
	set(v):
		player_id = v
		_preview()
## any baked clip; the dropdown lists them all
@export var preview_clip := "base_idle":
	set(v):
		preview_clip = v
		_preview()
@export_range(0, 31) var preview_dir := 16:
	set(v):
		preview_dir = v
		_preview()
@export_group("")

var anim := "run"
var dir := 16
var fidx := 0
var t := 0.0
var fps_mult := 1.0
var loop_override := -1       # -1 = use the sheet's setting, 0 = play once, 1 = loop
var paused := false          # true = hold frame 0 (used as a stand-in idle until the idle clip is baked)
var _done := false
var _meta := {}

signal finished(clip: String)

func _init() -> void:
	centered = false
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	region_enabled = true

func _validate_property(property: Dictionary) -> void:
	if property.name == "preview_clip":
		var names: Array = Data.anims.get("animations", {}).keys()
		if names.is_empty(): return
		names.sort()
		property.hint = PROPERTY_HINT_ENUM
		property.hint_string = ",".join(names)

func _ready() -> void:
	_preview()

## editor only: show the chosen player doing the chosen clip so the scene is not blank
func _preview() -> void:
	if not Engine.is_editor_hint() or not is_inside_tree(): return
	if not Data.ok: Data.reload()
	if not Data.ok: return
	setup(player_id)
	play(preview_clip)
	face(preview_dir)

func setup(pid: String) -> void:
	var m := ShaderMaterial.new()
	m.shader = SHADER
	var skin := Data.tex("looks/%s.png" % pid)
	if skin != null: m.set_shader_parameter("skin", skin)
	material = m
	var o: Array = Data.anims.get("origin", [20, 30])
	offset = Vector2(-o[0], -o[1])
	play(anim)

func play(clip: String) -> void:
	anim = clip
	fidx = 0
	t = 0.0
	_done = false
	paused = false
	loop_override = -1
	texture = Data.tex("sprites/%s_uv_sheet.png" % clip)
	_meta = Data.anims.get("animations", {}).get(clip, {})
	_apply()

func face(d: int) -> void:
	dir = posmod(d, 32)
	_apply()

func is_done() -> bool:
	return _done

func has_clip(clip: String) -> bool:
	return Data.anims.get("animations", {}).has(clip) and ResourceLoader.exists("res://assets/sprites/%s_uv_sheet.png" % clip)

func _loops() -> bool:
	if loop_override >= 0: return loop_override == 1
	return bool(_meta.get("loop", true))

func _process(delta: float) -> void:
	if _meta.is_empty() or paused: return
	var n := int(_meta.get("frames", 1))
	var ms := float(_meta.get("ms_per_frame", 60)) / maxf(fps_mult, 0.01)
	t += delta * 1000.0
	while t >= ms:
		t -= ms
		if fidx < n - 1: fidx += 1
		elif _loops(): fidx = 0
		elif not _done:
			_done = true
			finished.emit(anim)
	_apply()

func _apply() -> void:
	var c: Array = Data.anims.get("cell", [40, 40])
	region_rect = Rect2(fidx * c[0], dir * c[1], c[0], c[1])
