@tool
class_name Data
extends RefCounted
## All exported game data in one static class: no autoload, so it works in the editor (previews) and in game.
## Tables are Arrays of Dictionaries (all values Strings, like the CSV). Use Data.num()/Data.inum() to convert.
##   Data.table("players")          every row          Data.row("cards", "SH01")      one row by id
##   Data.tex("cards/SH01.png")     exported image     Data.rules / Data.anims / Data.manifest
## The data is read the first time the class is touched. Call Data.reload() after a new export (the Export button in the tool).

static var tables: Dictionary = _load_tables()      # name -> Array[Dictionary]
static var by_id: Dictionary = _index(tables)       # name -> { id -> row }
static var manifest: Dictionary = _json("res://data/export_manifest.json")
static var anims: Dictionary = _json("res://assets/sprites/animations.json")
static var rules: Dictionary = _json("res://data/card_rules.json")    # layout numbers for player cards
static var ok: bool = tables.has("players")

static func reload() -> void:
	_tex_cache.clear()
	tables = _load_tables()
	by_id = _index(tables)
	manifest = _json("res://data/export_manifest.json")
	anims = _json("res://assets/sprites/animations.json")
	rules = _json("res://data/card_rules.json")
	ok = tables.has("players")
	if not ok: push_warning("res://data is missing. Press Export to game in the manager tool first.")

static func _load_tables() -> Dictionary:
	var out := {}
	var d := DirAccess.open("res://data")
	if d == null: return out
	for f in d.get_files():
		if f.ends_with(".csv"): out[f.get_basename()] = _read_csv("res://data/" + f)
	return out

static func _index(t: Dictionary) -> Dictionary:
	var out := {}
	for name in t:
		var idx := {}
		for r in t[name]:
			if r.has("id"): idx[r["id"]] = r
		out[name] = idx
	return out

static func _read_csv(path: String) -> Array:
	var rows := []
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null: return rows
	var head := f.get_csv_line()
	if head.size() > 0 and head[0].begins_with("﻿"): head[0] = head[0].substr(1)
	while not f.eof_reached():
		var line := f.get_csv_line()
		if line.size() == 1 and line[0] == "": continue
		var r := {}
		for i in head.size():
			r[head[i]] = line[i] if i < line.size() else ""
		rows.append(r)
	return rows

static func _json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): return {}
	var v = JSON.parse_string(FileAccess.get_file_as_string(path))
	return v if v is Dictionary else {}

static func table(tname: String) -> Array:
	return tables.get(tname, [])

static func row(tname: String, id: String) -> Dictionary:
	return by_id.get(tname, {}).get(id, {})

static func num(v, d := 0.0) -> float:
	var s := str(v).strip_edges()
	return s.to_float() if s.is_valid_float() else d

static func inum(v, d := 0) -> int:
	var s := str(v).strip_edges()
	return int(s.to_float()) if s.is_valid_float() else d

static var _tex_cache: Dictionary = {}

## texture exported by the tool, e.g. Data.tex("cards/SH01.png") or Data.tex("sprites/run_uv_sheet.png").
## Uses Godot's imported copy when it is valid; otherwise reads the PNG straight from disk (so a half-imported or not yet imported
## export never shows as a white box). Returns null when the file does not exist.
static func tex(rel: String) -> Texture2D:
	if _tex_cache.has(rel): return _tex_cache[rel]
	var p := "res://assets/" + rel
	var t: Texture2D = null
	if ResourceLoader.exists(p):
		t = load(p) as Texture2D
		if t != null and t.get_width() <= 0: t = null
	if t == null and FileAccess.file_exists(p):
		var img := Image.load_from_file(ProjectSettings.globalize_path(p))
		if img != null and not img.is_empty(): t = ImageTexture.create_from_image(img)
	if t != null: _tex_cache[rel] = t
	return t

## forget cached textures (call after a new export)
static func clear_tex_cache() -> void:
	_tex_cache.clear()
