class_name AiSetBack
extends AiBehaviour
## Received with a man tight on his back (AiScan marked f.ai.setback at the first touch): he does not try to turn into him. He protects it and sets it back
## first time to a free team mate level or behind (the bounce pass that beats a press), then goes again. Strikers have their own version (AiLayOff).

@export_group("Set back")
## within this long (s) of getting it
@export var window := 0.7
## a team mate 4 to max_dist m away, not more than ahead_max m further forward, with nobody within `free` m of him and an open lane
@export var max_dist := 16.0
@export var ahead_max := 1.0
@export var free := 3.0
@export var lane := 1.1

static var stat_setbacks := 0

func _init() -> void:
	priority = 1
	roles = PackedStringArray(["CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if not f.ai.get("setback", false): return false
	if f.hold > window or c.game.kicking.busy(f) or f.lock > 0.0:
		if f.hold > window: f.ai.erase("setback")
		return false
	return f.hold > 0.08 and _mate(f, c) != null

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	var m := _mate(f, c)
	f.ai.erase("setback")
	if m == null: return i
	i.action = "pass"
	i.target = m
	i.note = "set back"
	stat_setbacks += 1
	return i

func _mate(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f or m.is_keeper(): continue
		var d := m.pos.distance_to(f.pos)
		if d < 4.0 or d > max_dist: continue
		if (m.pos.x - f.pos.x) * c.dir > ahead_max: continue
		var room := c.pressure(m.pos)
		if room < free or c.lane_blocked(f.pos, m.pos, lane): continue
		var sc := room - d * 0.25 + (m.pos.x - f.pos.x) * c.dir * 0.2
		if sc > bs:
			bs = sc
			best = m
	return best
