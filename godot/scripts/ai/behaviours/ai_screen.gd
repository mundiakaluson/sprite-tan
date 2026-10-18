class_name AiScreen
extends AiBehaviour
## The 6 screens the striker (catalogue section 6 "Screen the striker"): with the ball in front of our block he stands in the passing lane from the carrier to
## their most dangerous forward between our lines, a few metres in front of our back line, so the ball into the 9 / 10 is not on and play goes wide.

@export_group("Screen")
## their forward: a ST or CAM within this far in front of our back line
@export var between := 18.0
## he stands this share of the way from the forward towards the carrier, never more than max_ahead (m) in front of our back line
@export_range(0.1, 0.9) var share := 0.3
@export var max_ahead := 9.0
## only while the carrier is at least this far from our goal (closer, the box rules)
@export var min_from_goal := 26.0

static var stat_frames := 0

func _init() -> void:
	priority = 3
	roles = PackedStringArray(["CDM"])
	when = DEFENDING

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var k := c.carrier
	if k == null or f == c.presser or f.lock > 0.0 or c.cover.has(f): return false
	if k.pos.distance_to(c.own_goal()) < min_from_goal: return false
	return _target(f, c) != null

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var t := _target(f, c)
	var i := AiIntent.new()
	var p := t.pos.lerp(c.carrier.pos, share)
	var back := _back_t(c)
	p.x = minf(p.x * c.dir, back + max_ahead) * c.dir
	i.move_to = p
	i.speed = c.s.jog_factor if f.pos.distance_to(p) < 5.0 else c.s.sprint_factor
	i.note = "screen"
	stat_frames += 1
	return i

func _back_t(c: AiContext) -> float:
	var s := 0.0
	var n := 0
	for m in c.team.players:
		if m.role in ["CB", "LB", "RB"]:
			s += m.pos.x * c.dir
			n += 1
	return s / n if n > 0 else -30.0

func _target(f: Footballer, c: AiContext) -> Footballer:
	var back := _back_t(c)
	var best: Footballer = null
	var bd := 1e9
	for o in c.other.players:
		if o == c.carrier or not (o.role in ["ST", "CAM"]): continue
		var ot := o.pos.x * c.dir
		if ot < back - 2.0 or ot > back + between: continue
		var d := o.pos.distance_to(c.carrier.pos)
		if d < bd:
			bd = d
			best = o
	return best
