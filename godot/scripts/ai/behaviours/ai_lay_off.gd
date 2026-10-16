class_name AiLayOff
extends AiBehaviour
## A striker with his back to goal (or a man tight on him) does not try to turn: he lays it off to a midfielder coming in support and spins in behind
## into the gap in their line only once he has checked it is on (AiRunInBehind: the team mate has time, faces forward, lane open); then AiThroughBall.

@export_group("Lay off and spin")
## back to goal = facing less than this towards the goal (dot), or an opponent within `tight` m
@export_range(-1.0, 1.0) var facing_max := 0.25
@export var tight := 3.0
## pitch depth (0..1) where he does it: not near their box (there he turns, takes his man on or shoots)
@export var min_depth := 0.45
@export var max_depth := 0.74
## the lay-off: a team mate (these roles) 5 to max_dist m away, deeper or level, with nobody within `free` m of him
@export var support_roles := PackedStringArray(["CM", "CAM", "CDM", "LW", "RW"])
@export var max_dist := 18.0
@export var free := 3.5
## the spin: how far beyond their line, how long the run lasts
@export var run_depth := 11.0
@export var run_time := 2.8

static var stat_layoffs := 0

func _init() -> void:
	priority = 2
	roles = PackedStringArray(["ST"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.game.kicking.busy(f) or f.lock > 0.0 or f.hold < 0.15 or f.hold > 1.5: return false
	if c.depth(f.pos) < min_depth or c.depth(f.pos) > max_depth: return false
	var back := f.face.dot((c.goal() - f.pos).normalized()) < facing_max
	if not back or c.pressure(f.pos) > tight * 2.0: return false             # only with his back to goal and someone on him
	return _support(f, c) != null

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	var m := _support(f, c)
	if m == null: return i
	i.action = "pass"
	i.target = m
	i.note = "lay off and spin"
	stat_layoffs += 1
	f.ai["run_cd"] = 0.0                                                   # free to read the next run straight away (AiRunInBehind scans first)
	return i

func _support(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f or not m.role in support_roles: continue
		var d := m.pos.distance_to(f.pos)
		if d < 5.0 or d > max_dist: continue
		if (m.pos.x - f.pos.x) * c.dir > 2.0: continue                         # level or deeper: a lay-off, not a forward pass
		var o := c.nearest_opponent(m.pos)
		var room := o.pos.distance_to(m.pos) if o != null else 20.0
		if room < free or c.lane_blocked(f.pos, m.pos, 1.2): continue
		var score := room - d * 0.2 + m.stat("PAS", 60) * 0.05
		if score > bs:
			bs = score
			best = m
	return best
