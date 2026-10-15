@tool
extends Node
## Autoload "Data": loads every CSV the tool exported into res://data/ and the export manifest.
## Tables are Arrays of Dictionaries (all values Strings, like the CSV). Use num()/inum() to convert.

var tables := {}      # name -> Array[Dictionary]
var by_id := {}       # name -> { id -> row }
var manifest := {}
var anims := {}       # animations.json
var rules := {}       # card_rules.json (layout numbers for player cards)
var ok := false

func _ready() -> void:
	reload()

func reload() -> void:
	tables.clear(); by_id.clear()
	var d := DirAccess.open("res://data")
	if d == null:
		push_warning("res://data is missing. Press EXPORT TO GAME in the manager tool first.")
		ok = false
		return
	for f in d.get_files():
		if f.ends_with(".csv"):
			var tname := f.get_basename()
			tables[tname] = _read_csv("res://data/" + f)
			var idx := {}
			for r in tables[tname]:
				if r.has("id"): idx[r["id"]] = r
			by_id[tname] = idx
	manifest = _read_json("res://data/export_manifest.json")
	anims = _read_json("res://assets/sprites/animations.json")
	rules = _read_json("res://data/card_rules.json")
	ok = tables.has("players")

func _read_csv(path: String) -> Array:
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

func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): return {}
	var v = JSON.parse_string(FileAccess.get_file_as_string(path))
	return v if v is Dictionary else {}

func table(tname: String) -> Array:
	return tables.get(tname, [])

func row(tname: String, id: String) -> Dictionary:
	return by_id.get(tname, {}).get(id, {})

func num(v, d := 0.0) -> float:
	var s := str(v).strip_edges()
	return s.to_float() if s.is_valid_float() else d

func inum(v, d := 0) -> int:
	var s := str(v).strip_edges()
	return int(s.to_float()) if s.is_valid_float() else d

## texture exported by the tool, e.g. Data.tex("cards/SH01.png") or Data.tex("sprites/run_uv_sheet.png")
func tex(rel: String) -> Texture2D:
	var p := "res://assets/" + rel
	return load(p) as Texture2D if ResourceLoader.exists(p) else null
