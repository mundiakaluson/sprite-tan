class_name Team
extends RefCounted
## A side in the match: 11 footballers picked from players.csv for a formation (data/formations*.csv).

var label := "HOME"
var dir := 1.0                  ## +1 attacks towards +x (right of the screen), -1 towards -x
var human := false
var score := 0
var color := Color.WHITE
var ai := {}                    ## team-level AI memory (one-two cooldown, ...)
var stance_id := "auto"        ## the team command in force (TeamStance.id); "auto" = the formation as designed
var kit: KitColors              ## the colours he plays in
var formation_id := "F01"
var players: Array[Footballer] = []

## picks a keeper plus one player per formation slot (best rated of the role, with some variety); `used` stops a player appearing twice
func build(formation: String, used: Dictionary, rng: RandomNumberGenerator) -> void:
	formation_id = formation
	players.clear()
	var slots: Array = [{"role": "GK", "x": 50.0, "y": 4.0, "style": ""}]
	var lay := MatchSettings.layout(formation)
	if lay != null:
		for sl in lay.slots:
			if sl != null: slots.append({"role": sl.role, "x": sl.x, "y": sl.y, "style": sl.style})
		if lay.slots.size() != 10: push_warning("Formation %s has %d slots, it needs 10 outfield players" % [lay.layout_name, lay.slots.size()])
	else:
		for s in Data.table("formation_slots"):
			if s["formation"] == formation:
				slots.append({"role": s["role"], "x": Data.num(s["x"], 50.0), "y": Data.num(s["y"], 50.0), "style": s.get("style", "")})
	var pool := Data.table("players")
	for s in slots:
		var cands: Array = []
		for p in pool:
			if not used.has(p["id"]) and p["role"] == s["role"]: cands.append(p)
		if cands.is_empty():
			for p in pool:
				if not used.has(p["id"]) and (p["role"] == "GK") == (s["role"] == "GK"): cands.append(p)
		if cands.is_empty(): continue
		cands.sort_custom(func(a, b): return Data.inum(a["rating"]) > Data.inum(b["rating"]))
		var pick: Dictionary = cands[rng.randi() % mini(cands.size(), 8)]
		used[pick["id"]] = true
		var f := Footballer.new()
		f.row = pick
		f.team = self
		f.role = String(s["role"])
		f.style = String(s["style"])
		var along: float = (float(s["y"]) / 100.0 - 0.5) * Stadium.L
		var across: float = (float(s["x"]) / 100.0 - 0.5) * Stadium.W
		f.slot = Vector2(along * dir, across * dir)
		f.pos = f.slot
		f.face = Vector2(dir, 0.0)
		players.append(f)
