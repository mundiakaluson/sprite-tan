class_name AiTrackRunner
extends AiBehaviour
## A defender sees a forward making a run in behind (his f.ai["run_behind"], or anyone sprinting past the line) and goes with him, goal side,
## instead of watching the ball. The nearest back-line player (not the one pressing the ball) takes him.

@export_group("Track runner")
## a run this close (m) to him is his to pick up
@export var track_range := 20.0
## he gets this far (m) goal side of the runner, and aims where the runner will be `lead` s on
@export var goal_side := 1.3
@export var lead := 0.45
## anyone running at least this fast (m/s) towards our goal behind our line counts as a runner too
@export var sprint_speed := 6.0

static var stat_tracks := 0

func _init() -> void:
	priority = -7
	roles = PackedStringArray(["CB", "LB", "RB", "CDM"])
	when = DEFENDING | LOOSE

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if f.lock > 0.0 or c.presser == f: return false
	var r := _runner(f, c)
	if r == null: return false
	for m in c.team.players:                                               # the nearest of us takes him
		if m != f and m.role in roles and m != c.presser and m.lock <= 0.0 and m.pos.distance_to(r.pos) < f.pos.distance_to(r.pos): return false
	return true

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var r := _runner(f, c)
	var i := AiIntent.new()
	if r == null: return null
	if not f.ai.get("tracking", false): stat_tracks += 1
	f.ai["tracking"] = true
	var p := r.pos + r.vel * lead
	i.move_to = p + (c.own_goal() - p).normalized() * goal_side
	i.speed = c.s.sprint_factor
	i.note = "track the runner"
	return i

func _runner(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bd := track_range
	for o in c.other.players:
		if o.is_keeper() or o == c.carrier: continue
		var running := o.ai.has("run_behind") or (o.vel.dot((c.own_goal() - o.pos).normalized()) > sprint_speed)
		if not running: continue
		var d := o.pos.distance_to(f.pos)
		if d < bd:
			bd = d
			best = o
	if best == null: f.ai["tracking"] = false
	return best
