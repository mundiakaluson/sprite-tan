class_name PlayerSprite
extends Sprite2D
## One animated, recoloured player. Sheets are frames across x direction rows (32 dirs, 40x40 cells). The shader reads the
## sprite pixels as UV lookups into the player's 96x24 look atlas.
## usage: var p := PlayerSprite.new(); add_child(p); p.setup("PL242"); p.play("run"); p.face(8)   # dir 8 = screen right, 16 = toward the camera

const SHADER := preload("res://shaders/uv_skin.gdshader")
var anim := "run"
var dir := 16
var fidx := 0
var t := 0.0
var fps_mult := 1.0
var _meta := {}

func _init() -> void:
	centered = false
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	region_enabled = true

func setup(player_id: String) -> void:
	var m := ShaderMaterial.new()
	m.shader = SHADER
	var skin := Data.tex("looks/%s.png" % player_id)
	if skin != null: m.set_shader_parameter("skin", skin)
	material = m
	var o: Array = Data.anims.get("origin", [20, 30])
	offset = Vector2(-o[0], -o[1])
	play(anim)

func play(clip: String) -> void:
	anim = clip
	fidx = 0
	t = 0.0
	texture = Data.tex("sprites/%s_uv_sheet.png" % clip)
	_meta = Data.anims.get("animations", {}).get(clip, {})
	_apply()

func face(d: int) -> void:
	dir = posmod(d, 32)
	_apply()

func finished() -> bool:
	return not _meta.get("loop", true) and fidx >= int(_meta.get("frames", 1)) - 1

func _process(delta: float) -> void:
	if _meta.is_empty(): return
	var n := int(_meta.get("frames", 1))
	var ms := float(_meta.get("ms_per_frame", 60)) / maxf(fps_mult, 0.01)
	t += delta * 1000.0
	while t >= ms:
		t -= ms
		if fidx < n - 1: fidx += 1
		elif _meta.get("loop", true): fidx = 0
	_apply()

func _apply() -> void:
	var c: Array = Data.anims.get("cell", [40, 40])
	region_rect = Rect2(fidx * c[0], dir * c[1], c[0], c[1])
