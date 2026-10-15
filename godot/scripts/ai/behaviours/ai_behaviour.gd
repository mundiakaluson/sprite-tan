class_name AiBehaviour
extends Resource
## One thing a player can decide to do, as its own small script. To add one: copy ai_jockey.gd in this folder, rename it and its class_name, set `roles` and `when` in `_init()`, write
## `wants()` (when) and `act()` (what). That is all: every script in scripts/ai/behaviours/ that extends AiBehaviour is found at run time and given to every AI profile, no .tres, no list.
## AiRole.think tries them for every player whose role and situation match, after the formation file and BEFORE the role's own five cases; the first `wants()` that says yes decides what the
## player does this frame (lowest `priority` first, then file name).
## Tuning the exports without code: save a resource of your script as scenes/ai/behaviours/<file name without "ai_" and ".gd">.tres (ai_jockey.gd -> jockey.tres) and that one is used instead.
## Switch one off: `enabled = false` there (or in the script). Extra copies per team: AiProfile > Behaviours (an entry replaces the found one of the same script).

const RECEIVING := 1       ## he is the intended target of a pass and the ball is on its way
const WITH_BALL := 2       ## he has the ball
const SUPPORT := 4         ## his team has the ball (someone else carries it)
const LOOSE := 8           ## nobody has the ball
const DEFENDING := 16      ## the other team has the ball

@export var enabled := true
## lower runs first when several behaviours want the same player
@export var priority := 0
## role ids this applies to (GK CB LB RB CDM CM CAM LW RW ST); empty = every role
@export var roles := PackedStringArray()
## which situations it is asked about (so `wants()` need not check them)
@export_flags("Receiving:1", "With ball:2", "Support:4", "Loose:8", "Defending:16") var when := 16

## yes = this behaviour decides for him now. f = the player, c = what his team sees (c.carrier, c.ball, c.other, c.own_goal(), c.nearest_opponent(pos), c.s = settings ...), role = his role resource
func wants(_f: Footballer, _c: AiContext, _role: AiRole) -> bool:
	return false

## what he does (move_to / speed / action, see AiIntent); only called when wants() said yes
func act(_f: Footballer, _c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	return null

# ---------------------------------------------------------------- used by AiRole.think
func applies(f: Footballer, situation: int) -> bool:
	if not enabled or (when & situation) == 0: return false
	return roles.is_empty() or f.role in roles

static func situation_of(f: Footballer, c: AiContext) -> int:
	if c.game.pass_target == f and c.carrier == null: return RECEIVING
	if c.carrier == f: return WITH_BALL
	if c.has_ball: return SUPPORT
	if c.carrier == null: return LOOSE
	return DEFENDING

# ---------------------------------------------------------------- finding them
const FOLDER := "res://scripts/ai/behaviours/"
const OVERRIDES := "res://scenes/ai/behaviours/"
static var _found: Array[AiBehaviour] = []
static var _scanned := false

## every behaviour script in FOLDER, as an instance (the .tres override when there is one), sorted by priority then name
static func discover() -> Array[AiBehaviour]:
	if _scanned: return _found
	_scanned = true
	var names := PackedStringArray()
	var d := DirAccess.open(FOLDER)
	if d == null: return _found
	for raw in d.get_files():
		var n := raw.trim_suffix(".remap")
		if n.ends_with(".gd") and n != "ai_behaviour.gd" and not names.has(n): names.append(n)
	names.sort()
	for n in names:
		var sc = load(FOLDER + n)
		if sc == null or not sc is Script or not sc.can_instantiate(): continue
		var res := OVERRIDES + n.trim_suffix(".gd").trim_prefix("ai_") + ".tres"
		var inst = load(res) if ResourceLoader.exists(res) else sc.new()
		if inst is AiBehaviour: _found.append(inst)
	_found.sort_custom(AiBehaviour.before)
	return _found

## priority, then file name (a stable order: Godot's sort is not)
static func before(a: AiBehaviour, b: AiBehaviour) -> bool:
	if a.priority != b.priority: return a.priority < b.priority
	return String(a.get_script().resource_path) < String(b.get_script().resource_path)
