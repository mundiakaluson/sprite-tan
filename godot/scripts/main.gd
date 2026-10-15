extends Control
## Debug view: proves the export loads. Shows the export info, a recoloured player running, a skill card, a player card and a pack wrapper.
## SPACE opens the first live shop pack and prints the pull. Left/Right turn the player. Replace this with the real game.

var rng := RandomNumberGenerator.new()
var info: Label
var player: PlayerSprite
var dry := 0

func _ready() -> void:
	rng.randomize()
	info = Label.new(); info.position = Vector2(8, 6); add_child(info)
	if not Data.ok:
		info.text = "No exported data. Open the manager tool and press EXPORT TO GAME, then reopen this project (Godot imports the new files)."
		return
	var m := Data.manifest
	info.text = "exported %s  commit %s   players %d  cards %d  packs %d\nSPACE = open a pack   LEFT/RIGHT = turn" % [m.get("exported", "?"), m.get("git", "?"), Data.table("players").size(), Data.table("cards").size(), Data.table("packs").size()]
	var pid: String = Data.table("players")[0]["id"]
	player = PlayerSprite.new(); player.position = Vector2(80, 200); player.scale = Vector2(4, 4); add_child(player)
	player.setup(pid); player.play("run"); player.face(8)
	_show(Data.tex("players/%s.png" % pid), Vector2(200, 80), 2)
	var cid: String = Data.table("cards")[0]["id"]
	_show(Data.tex("cards/%s.png" % cid), Vector2(360, 80), 2)
	var shop := PackLib.shop()
	if shop.size() > 0: _show(Data.tex("packs/%s.png" % shop[0]["id"]), Vector2(520, 60), 1)

func _show(t: Texture2D, pos: Vector2, s: int) -> void:
	if t == null: return
	var r := TextureRect.new(); r.texture = t; r.position = pos; r.scale = Vector2(s, s)
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST; add_child(r)

func _unhandled_key_input(e: InputEvent) -> void:
	if not (e is InputEventKey) or not e.pressed or player == null: return
	if e.keycode == KEY_LEFT: player.face(player.dir - 1)
	elif e.keycode == KEY_RIGHT: player.face(player.dir + 1)
	elif e.keycode == KEY_SPACE:
		var shop := PackLib.shop()
		if shop.is_empty(): print("no live packs"); return
		var pk: Dictionary = shop[0]
		var pull := PackLib.roll(pk["id"], rng, dry)
		dry = PackLib.next_dry(pk, pull, dry)
		var s := []
		for x in pull: s.append("%s %s" % [x["rarity"], x["row"].get("name", x["row"].get("id", "?"))])
		print(pk["name"], " (dry ", dry, "): ", ", ".join(s))
