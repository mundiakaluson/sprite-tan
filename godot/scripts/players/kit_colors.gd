@tool
class_name KitColors
extends Resource
## The colours a team plays in. The player picture is recoloured live from these (shaders/uv_skin.gdshader swaps the kit parts of the look atlas), so a new kit
## is a colour change, not a new image. Edit the colours in the inspector, or pick "Load Preset" to copy a kit from data/kits.csv and tweak it from there.
## (The pattern of a kit - hoops, stripes - is not part of this: shirts are plain.)

## copy a kit from data/kits.csv into the colours below (not saved; just a shortcut)
@export var load_preset := "":
	set(v):
		if v != "" and Engine.is_editor_hint(): apply(v)
	get:
		return ""
@export_group("Shirt")
@export var jersey := Color("d63240")
## collar, sleeve cuffs and the number
@export var trim := Color("f4f4fa")
@export_group("Shorts")
@export var shorts := Color("f0f0f8")
@export var shorts_trim := Color("d63240")
## the side stripes
@export var stripe := Color("d63240")
@export_group("Socks and boots")
@export var socks := Color("d63240")
@export var sock_trim := Color("f4f4fa")
@export var boots := Color("f0f0fa")
@export var accent := Color("24243c")
@export_group("Keeper")
## gloves (only a goalkeeper's hands are recoloured)
@export var glove := Color("e8f03c")

func _validate_property(property: Dictionary) -> void:
	if property.name != "load_preset": return
	if not Data.ok: Data.reload()
	var ids: Array = [""]
	for r in Data.table("kits"): ids.append(str(r.get("id", "")))
	property.hint = PROPERTY_HINT_ENUM
	property.hint_string = ",".join(ids)
	property.usage = PROPERTY_USAGE_EDITOR

## copy a kit row of data/kits.csv
func apply(id: String) -> void:
	if not Data.ok: Data.reload()
	var r := Data.row("kits", id)
	if r.is_empty(): return
	for k in ["jersey", "trim", "shorts", "shorts_trim", "stripe", "socks", "sock_trim", "boots", "accent", "glove"]:
		var v := str(r.get(k, ""))
		if v != "": set(k, Color(v))

static func from_preset(id: String) -> KitColors:
	var k := KitColors.new()
	k.apply(id)
	return k
