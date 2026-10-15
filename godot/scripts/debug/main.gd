extends Control
## Debug view: proves the export loads. Shows the export info, a recoloured player running, a live-built player card and tooltip, a skill card and a pack wrapper.
## Keys are Input Map actions (Project > Project Settings > Input Map): move_order (left click), play_kick (K), open_pack (Space).
## Replace this with the real game.

var rng := RandomNumberGenerator.new()
var info: Label
var player: Player
var dry := 0

func _ready() -> void:
	rng.randomize()
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	info = Label.new(); info.position = Vector2(8, 6); add_child(info)
	if not Data.ok:
		info.text = "No exported data. Open the manager tool and press EXPORT TO GAME, then reopen this project (Godot imports the new files)."
		return
	var m := Data.manifest
	info.text = "exported %s  commit %s   players %d  cards %d  packs %d\nclick = move   K = kick   SPACE = open a pack" % [m.get("exported", "?"), m.get("git", "?"), Data.table("players").size(), Data.table("cards").size(), Data.table("packs").size()]
	var pid: String = Data.table("players")[0]["id"]
	player = Player.create(); player.position = Vector2(80, 200); player.scale = Vector2(4, 4); add_child(player)
	player.setup(Data.row("players", pid))
	player.state_changed.connect(func(a, b): print("state ", a, " -> ", b))
	var pc := PlayerCard.new(); pc.position = Vector2(200, 80); pc.scale = Vector2(2, 2); add_child(pc); pc.show_player(Data.row("players", pid))
	var tip := PlayerTip.new(); tip.position = Vector2(200, 280); tip.scale = Vector2(2, 2); add_child(tip); tip.show_player(Data.row("players", pid))
	var cid: String = Data.table("cards")[0]["id"]
	var sk := SkillCard.new_card(cid); sk.position = Vector2(360, 80); sk.scale = Vector2(2, 2); add_child(sk); sk.play("appear")
	var shop := PackLib.shop()
	if shop.size() > 0: _show(Data.tex("packs/%s.png" % shop[0]["id"]), Vector2(520, 60), 1)

func _show(t: Texture2D, pos: Vector2, s: int) -> void:
	if t == null: return
	var r := TextureRect.new(); r.texture = t; r.position = pos; r.scale = Vector2(s, s)
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST; add_child(r)

func _unhandled_input(ev: InputEvent) -> void:
	if player == null: return
	if ev.is_action_pressed("move_order"):
		player.move_to(get_local_mouse_position())
	elif ev.is_action_pressed("play_kick"):
		player.play_action("kick", Vector2(1, 0))
	elif ev.is_action_pressed("open_pack"):
		var shop := PackLib.shop()
		if shop.is_empty(): print("no live packs"); return
		var pk: Dictionary = shop[0]
		var pull := PackLib.roll(pk["id"], rng, dry)
		dry = PackLib.next_dry(pk, pull, dry)
		var s := []
		for x in pull: s.append("%s %s" % [x["rarity"], x["row"].get("name", x["row"].get("id", "?"))])
		print(pk["name"], " (dry ", dry, "): ", ", ".join(s))
