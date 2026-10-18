class_name AiBlockShot
extends AiBehaviour
## Blocking the shot (behaviour catalogue: centre back "Block the shot"). Their carrier within shooting range of our goal and facing it (or shaping a shot): the
## nearest defender who is not already closing him down steps across into the line of the shot, a couple of metres from the shooter, side-on.
## The ball then hits him (MatchPossession deflects a fast ball off a body).

@export_group("Block")
@export var range_m := 26.0
## the carrier faces our goal (dot above this)
@export_range(-1.0, 1.0) var facing := 0.4
## the blocker: within this far (m) of the shooter, and he stands this far from him on the line to the middle of the goal
@export var reach := 8.0
@export var block_dist := 2.2

static var stat_blocks_set := 0

func _init() -> void:
	priority = -4
	roles = PackedStringArray(["CB", "LB", "RB", "CDM", "CM"])
	when = DEFENDING

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var k := c.carrier
	if k == null or f == c.presser or f.lock > 0.0: return false
	var goal := c.own_goal()
	if k.pos.distance_to(goal) > range_m: return false
	var sh := c.game.kicking.shaping(k)
	var shooting := not sh.is_empty() and String(sh["action"]) == "shot"
	if not shooting and k.face.dot((goal - k.pos).normalized()) < facing: return false
	if f.pos.distance_to(k.pos) > reach: return false
	# only the nearest such defender
	for m in c.team.players:
		if m == f or m == c.presser or m.is_keeper() or not (m.role in roles): continue
		if m.pos.distance_to(k.pos) < f.pos.distance_to(k.pos): return false
	return true

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var k := c.carrier
	var i := AiIntent.new()
	var at := k.pos + (c.own_goal() - k.pos).normalized() * block_dist
	i.move_to = at
	i.speed = c.s.sprint_factor
	i.note = "block"
	if f.pos.distance_to(at) < 0.8:
		stat_blocks_set += 1
		f.ai["look"] = (k.pos - f.pos).normalized()
		f.ai["look_until"] = c.game.clock + c.game_s(0.2)
	return i
