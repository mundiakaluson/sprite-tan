class_name PackLib
## Port of packs/packlib.py. Same rules: odds + pity boost, guarantee_min, hard pity, pools with include/exclude rows.
## The pity counter ("dry") belongs in the player's save, not in the data.

const RARS := ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGEND"]

static func state(pk: Dictionary, now := Time.get_unix_time_from_system()) -> String:
	if not (str(pk.get("active", "1")).strip_edges() in ["1", "true", "True", "yes"]): return "hidden"
	var a := _time(pk.get("start", ""))
	var b := _time(pk.get("end", ""))
	if a == -2 or b == -2: return "hidden"
	if a >= 0 and now < a: return "upcoming"
	if b >= 0 and now > b: return "expired"
	return "live"

## unix time of "YYYY-MM-DD" / "YYYY-MM-DD HH:MM" (local time treated as UTC), -1 if empty, -2 if bad
static func _time(s: String) -> int:
	s = s.strip_edges()
	if s == "": return -1
	var dt := s.replace(" ", "T")
	if dt.length() == 10: dt += "T00:00:00"
	elif dt.length() == 16: dt += ":00"
	var t := Time.get_unix_time_from_datetime_string(dt)
	return t if t > 0 else -2

static func shop(source := "shop", now := Time.get_unix_time_from_system()) -> Array:
	var out := []
	for pk in Data.table("packs"):
		if state(pk, now) == "live" and pk.get("source", "") == source and Data.inum(pk.get("price")) >= 0: out.append(pk)
	out.sort_custom(func(a, b): return Data.inum(a.get("sort"), 999) < Data.inum(b.get("sort"), 999))
	return out

static func pity_on(pk: Dictionary) -> bool:
	return Data.inum(pk.get("pity_hard")) > 0 or Data.num(pk.get("pity_step")) > 0

static func pity_extra(pk: Dictionary, dry: int) -> float:
	if not pity_on(pk) or dry < Data.inum(pk.get("pity_start")): return 0.0
	return Data.num(pk.get("pity_step")) * (dry - Data.inum(pk.get("pity_start")) + 1)

## five rarity weights (sum 100) with the pity boost
static func weights(pk: Dictionary, odds: Dictionary, dry := 0) -> Array:
	var w := []
	var tot := 0.0
	for r in RARS:
		var x: float = max(0.0, Data.num(odds.get(r.to_lower())))
		w.append(x); tot += x
	if tot == 0.0: tot = 1.0
	for i in w.size(): w[i] = w[i] * 100.0 / tot
	var ex := pity_extra(pk, dry)
	if ex > 0.0:
		var r := RARS.find(pk.get("pity_rarity", "RARE") if pk.get("pity_rarity", "") != "" else "RARE")
		var low := 0.0
		for i in r: low += w[i]
		var mv: float = min(ex, low)
		if mv > 0.0 and low > 0.0:
			var hi := 0.0
			for i in range(r, w.size()): hi += w[i]
			for i in w.size():
				if i < r: w[i] = w[i] * (1.0 - mv / low)
				else: w[i] = w[i] + ((mv * w[i] / hi) if hi > 0.0 else (mv if i == r else 0.0))
	return w

static func _match(p: Dictionary, item: Dictionary, kind: String) -> bool:
	var cat: String = p.get("category", "").strip_edges()
	var rar: String = p.get("rarity", "").strip_edges()
	var id: String = p.get("id", "").strip_edges()
	var have: String = item.get("role", "") if kind == "player" else item.get("cat", "")
	return (cat == "" or cat == have) and (rar == "" or rar == item.get("rarity", "")) and (id == "" or id == item.get("id", ""))

## { rarity: [ [row, weight], ... ] }. No include rows = everything; exclude always removes; an empty rarity falls back to the whole table.
static func eligible(kind: String, pools: Array, rows: Array) -> Dictionary:
	var inc := []
	var exc := []
	for p in pools:
		if p.get("kind", "") != kind: continue
		if p.get("mode", "") == "exclude": exc.append(p)
		else: inc.append(p)
	var out := {}
	for r in RARS: out[r] = []
	for it in rows:
		if not out.has(it.get("rarity", "")): continue
		var skip := false
		for p in exc:
			if _match(p, it, kind): skip = true; break
		if skip: continue
		if inc.size() > 0:
			var best := 0.0
			var hit := false
			for p in inc:
				if _match(p, it, kind):
					hit = true
					var wt := Data.num(p.get("weight"), 1.0)
					best = max(best, wt if wt != 0.0 else 1.0)
			if not hit: continue
			out[it["rarity"]].append([it, best])
		else:
			out[it["rarity"]].append([it, 1.0])
	for r in RARS:
		if out[r].is_empty():
			for it in rows:
				if it.get("rarity", "") == r: out[r].append([it, 1.0])
	return out

static func _pick(list: Array, rng: RandomNumberGenerator):
	var tot := 0.0
	for e in list: tot += e[1]
	var x := rng.randf() * tot
	for e in list:
		x -= e[1]
		if x <= 0.0: return e[0]
	return list[list.size() - 1][0]

static func _rar(w: Array, rng: RandomNumberGenerator) -> String:
	var x := rng.randf() * 100.0
	for i in w.size():
		x -= w[i]
		if x <= 0.0: return RARS[i]
	return RARS[RARS.size() - 1]

static func bundle(pack_id: String) -> Dictionary:
	var pk := Data.row("packs", pack_id)
	var odds := {}
	for r in Data.table("pack_odds"):
		if r.get("pack", "") == pack_id: odds = r
	var pools := []
	for r in Data.table("pack_pools"):
		if r.get("pack", "") == pack_id: pools.append(r)
	return {"pk": pk, "odds": odds, "pools": pools}

## open one pack. Returns [ {kind, rarity, row}, ... ] worst first, best last. dry = packs since the last pity-rarity pull.
static func roll(pack_id: String, rng: RandomNumberGenerator, dry := 0) -> Array:
	var b := bundle(pack_id)
	var pk: Dictionary = b["pk"]
	if pk.is_empty(): return []
	var players := Data.table("players")
	var cards := Data.table("cards")
	var pp := eligible("player", b["pools"], players)
	var cp := eligible("card", b["pools"], cards)
	var P := Data.inum(pk.get("player_items"))
	var C := Data.inum(pk.get("card_items"))
	var w := weights(pk, b["odds"], dry)
	var items := []
	for i in P: items.append(["player", _rar(w, rng)])
	for i in C: items.append(["card", _rar(w, rng)])
	var need := []
	var gm: String = pk.get("guarantee_min", "").strip_edges().to_upper()
	if gm in RARS: need.append(RARS.find(gm))
	if pity_on(pk) and Data.inum(pk.get("pity_hard")) > 0 and dry >= Data.inum(pk.get("pity_hard")) - 1:
		need.append(RARS.find(pk.get("pity_rarity", "RARE") if pk.get("pity_rarity", "") != "" else "RARE"))
	for n in need:
		var top := -1
		for it in items: top = max(top, RARS.find(it[1]))
		if items.size() > 0 and top < n: items[rng.randi() % items.size()][1] = RARS[n]
	var pull := []
	for it in items:
		var pool: Dictionary = pp if it[0] == "player" else cp
		var list: Array = pool[it[1]]
		if list.is_empty(): continue
		pull.append({"kind": it[0], "rarity": it[1], "row": _pick(list, rng)})
	pull.sort_custom(func(a, b): return RARS.find(a["rarity"]) < RARS.find(b["rarity"]))
	return pull

## new dry-spell counter after a pull
static func next_dry(pk: Dictionary, pull: Array, dry: int) -> int:
	if not pity_on(pk): return 0
	var pr := RARS.find(pk.get("pity_rarity", "RARE") if pk.get("pity_rarity", "") != "" else "RARE")
	for x in pull:
		if RARS.find(x["rarity"]) >= pr: return 0
	return dry + 1
