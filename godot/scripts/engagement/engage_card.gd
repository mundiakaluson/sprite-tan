class_name EngageCard
extends RefCounted
## Reading a skill card (a row of data/cards.csv) for an engagement: which engagement types it fits (`engage` column), what it does in the sim
## (`effect` column, "key=value key=value", e.g. "move=skill strand=1.4"), the weighted stat behind it (`stats`, main stat 70 %, minor 30 %).
## An empty Dictionary is the free default: no card, nothing spent.

const BALL_CATS := ["DRIBBLE", "SHOT", "PASS"]
const CHALLENGE_CATS := ["DEFEND", "KEEPER"]

## can this card be played by `f` on this side ("ball" / "challenge") of an engagement of this type ("duel", ...)?
static func fits(c: Dictionary, type: String, side: String, f: Footballer) -> bool:
	if String(c.get("timing", "")) != "ENGAGEMENT": return false
	if not (type in String(c.get("engage", "")).split(" ", false)): return false
	var cat := String(c.get("cat", ""))
	if cat == "KEEPER" and not f.is_keeper(): return false
	if cat != "KEEPER" and cat != "TITAN" and f.is_keeper() and side == "challenge": return false
	if side == "ball": return cat in BALL_CATS or cat == "TITAN"
	return cat in CHALLENGE_CATS or cat == "TITAN"

## the card's effect column as a Dictionary of strings
static func effect(c: Dictionary) -> Dictionary:
	var out := {}
	for kv in String(c.get("effect", "")).split(" ", false):
		var p := kv.split("=", true, 1)
		if p.size() == 2: out[p[0]] = p[1]
	return out

static func effect_num(c: Dictionary, key: String, d := 1.0) -> float:
	var e := effect(c)
	return Data.num(e[key], d) if e.has(key) else d

static func effect_str(c: Dictionary, key: String, d := "") -> String:
	return String(effect(c).get(key, d))

## the player's stat for this card: main stat 70 %, minor 30 % (`fallback` when no card or no stats)
static func stat(f: Footballer, c: Dictionary, fallback: String) -> float:
	var keys := String(c.get("stats", "")).split("+", false) if not c.is_empty() else PackedStringArray()
	if keys.is_empty(): keys = PackedStringArray([fallback])
	if keys.size() == 1: return float(f.stat(keys[0], 60))
	return 0.7 * f.stat(keys[0], 60) + 0.3 * f.stat(keys[1], 60)

## the clip named after the card (id + name, e.g. dr08_elastico) when he has it baked, else ""
static func clip(f: Footballer, c: Dictionary) -> String:
	if c.is_empty(): return ""
	var s := ""
	for ch in String(c["name"]).to_lower():
		s += ch if (ch >= "a" and ch <= "z") or (ch >= "0" and ch <= "9") else "_"
	var n := "%s_%s" % [String(c["id"]).to_lower(), s]
	return n if f.node != null and f.node.has_clip(n) else ""

static func label(c: Dictionary, default_label: String) -> String:
	return default_label if c.is_empty() else String(c["name"]).to_upper()
