@tool
class_name PlayerSprite
extends Sprite2D
## The recoloured player picture. It does NOT animate itself: the AnimationPlayer / AnimationTree in the player scene sets `sheet`
## and `frame_index` (one Animation per sprite sheet, see godot/animations/). Sheets are frames across x 32 direction rows, 40x40 cells.
## The shader reads sprite pixels as UV lookups into the player's 96x24 look atlas (assets/looks/<id>.png).
## Direction: 8 = screen right, 16 = toward the camera, 0 = away, 24 = left.

signal clip_event(event_name: String)       # "strike", "land", ... fired by the animation's method track

static var _kit_cache := {}
const SHADER := preload("res://shaders/uv_skin.gdshader")

## whose look to use (the Player sets it in game; set it here to preview in the editor)
@export var player_id := "PL242":
	set(v):
		player_id = v
		_apply_skin()
## the colours to play in (a KitColors resource; empty = home kit, or the keeper kit for a goalkeeper). Needs the look atlases from Export to game.
@export var kit: KitColors:
	set(v):
		kit = v
		_apply_skin()
## sprite sheet name = animation name, e.g. "run", "kick", "base_idle". Animated by the AnimationPlayer; pick one here to preview.
@export var sheet := "base_idle":
	set(v):
		sheet = v
		_apply_sheet()
## frame inside the sheet. Animated by the AnimationPlayer.
@export var frame_index := 0:
	set(v):
		frame_index = v
		_apply_region()
@export_range(0, 31) var direction := 16:
	set(v):
		direction = posmod(v, 32)
		_apply_region()

func _init() -> void:
	centered = false
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	region_enabled = true

func _validate_property(property: Dictionary) -> void:
	if property.name == "sheet":
		var names: Array = Data.anims.get("animations", {}).keys()
		if names.is_empty(): return
		names.sort()
		property.hint = PROPERTY_HINT_ENUM
		property.hint_string = ",".join(names)

func _ready() -> void:
	var o: Array = Data.anims.get("origin", [20, 30])
	offset = Vector2(-o[0], -o[1])
	_apply_skin()
	_apply_sheet()

func setup(pid: String) -> void:
	player_id = pid

func face(d: int) -> void:
	direction = d

## called by the animation's method track
func clip_event_fired(event_name: String) -> void:
	clip_event.emit(event_name)

func _apply_skin() -> void:
	if not Data.ok: Data.reload()
	if not Data.ok: return
	var m := material as ShaderMaterial
	if m == null:
		m = ShaderMaterial.new()
		m.shader = SHADER
		material = m
	var k := kit
	if k == null: k = _default_kit()
	var skin := _kit_atlas(player_id, k)
	if skin != null: m.set_shader_parameter("skin", skin)

func _default_kit() -> KitColors:
	var role := str(Data.row("players", player_id).get("role", ""))
	return KitColors.from_preset("keeper" if role == "GK" else "home")

## the player's look atlas with the kit parts (painted in KEY colours by the export, see tool/looks.py KEY_KIT) replaced by the team's colours. Cached per player + colours.
static func _kit_atlas(pid: String, k: KitColors) -> Texture2D:
	var key := "%s|%s" % [pid, k.signature()]
	if _kit_cache.has(key): return _kit_cache[key]
	var img: Image = null
	var path := ProjectSettings.globalize_path("res://assets/looks/%s.png" % pid)
	if FileAccess.file_exists("res://assets/looks/%s.png" % pid): img = Image.load_from_file(path)
	if img == null or img.is_empty():
		var t := Data.tex("looks/%s.png" % pid)
		if t == null: return null
		img = t.get_image()
	img.convert(Image.FORMAT_RGBA8)
	var map := k.key_map()
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			if c.a < 0.5: continue
			var id := Vector3i(roundi(c.r * 255.0), roundi(c.g * 255.0), roundi(c.b * 255.0))
			if map.has(id): img.set_pixel(x, y, map[id])
	var tex := ImageTexture.create_from_image(img)
	_kit_cache[key] = tex
	return tex

## forget the recoloured atlases (after changing a kit colour while the game runs)
static func clear_kit_cache() -> void:
	_kit_cache.clear()

func _apply_sheet() -> void:
	if not Data.ok: Data.reload()
	texture = Data.tex("sprites/%s_uv_sheet.png" % sheet)
	_apply_region()

func _apply_region() -> void:
	var c: Array = Data.anims.get("cell", [40, 40])
	region_rect = Rect2(frame_index * c[0], direction * c[1], c[0], c[1])
