class_name AiCross
extends AiBehaviour
## The end product from wide (behaviour catalogue: winger "Cross or cut-back", full back "Overlap" ends in a cross). With the ball wide in their final third:
##  cut-back: near the byline with a team mate free at the penalty spot / cut-back zone and the lane open -> a firm pass back along the grass;
##  near-post ball: a runner attacking the near post ahead of his man -> a driven ball across the six-yard box;
##  cross: runners in the box (AiBox) -> a lofted cross to the zone with our man and the fewest defenders (the far post when it is free).
## He waits for the runners to go (AiBox.go) unless a defender is about to block him. Per 100 balls into the box, cut-backs score about 2.5x more than crosses,
## so a free cut-back is always taken first.

@export_group("Delivery")
## chances per second to deliver once something is on (x (PAS + 40) / 100)
@export var rate := 2.2
## wide in the final third (as AiBox): this far from the middle, within this of the goal line
@export var wide_z := 12.0
@export var final_x := 30.0
## cut-back: carrier within this of the byline; mate free by cut_free (m), between 6 and 20 m from goal line, with an open lane
@export var cut_x := 12.0
@export var cut_free := 2.2
@export var cut_lane := 1.0
## near-post ball: the runner is nearer the near post than any defender, by this much (m)
@export var near_post_lead := 1.0
## cross: count defenders within this of a zone spot; a zone needs our man within reach_m of it
@export var crowd_radius := 3.0
## an early cross goes to a box runner still this far (m) from his zone, running
@export var early_reach := 16.0
## a cross needs a runner within this far of the goal line (he attacks the ball as it comes)
@export var cross_depth := 20.0
@export var reach_m := 6.0
## a defender closer than this (m) in front of him: deliver now (before the block), whatever is on
@export var block_close := 2.2
## with time he waits until this many team mates are in the box
@export var min_in_box := 2
## before the runners go he drives on towards the byline while nobody is within this (m)
@export var drive_free := 3.5

static var stat := {}

func _init() -> void:
	priority = -6
	roles = PackedStringArray(["LW", "RW", "LB", "RB", "CM", "CAM"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.game.kicking.busy(f) or f.lock > 0.0 or f.hold < 0.2: return false
	var t := f.pos.x * c.dir
	if t < MatchGame.HALF_L - final_x or absf(f.pos.y) < wide_z: return false
	if _blocked_soon(f, c): return not _plan(f, c).is_empty()                 # deliver before the block, if anything is on
	if c.box_go: return not _plan(f, c).is_empty() or c.pressure(f.pos) > drive_free
	return c.pressure(f.pos) > drive_free                                      # nothing on yet: drive on towards the byline while the runners get there

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.speed = c.s.carry_factor
	i.move_to = c.clamp_pitch(Vector2((MatchGame.HALF_L - 4.0) * c.dir, f.pos.y * 0.92), 1.0)
	i.note = "drive to the byline"
	var at_line := f.pos.x * c.dir > MatchGame.HALF_L - 5.0
	var now := _blocked_soon(f, c) or at_line or (c.box_go and _in_box(f, c) >= min_in_box and c.game.rng.randf() < rate * (f.stat("PAS", 60) + 40.0) / 100.0 * c.game.get_physics_process_delta_time())
	if not now: return i
	var p := _plan(f, c)
	if p.is_empty(): return i
	i.move_to = f.pos + f.face * 2.0
	i.action = p["action"]
	i.target = p["mate"]
	i.note = p["kind"]
	var key := "%d %d" % [f.get_instance_id(), int(c.game.clock - c.game_s(f.hold))]     # count each delivery once (the kick may wait a frame or two)
	if f.ai.get("cross_key", "") != key:
		f.ai["cross_key"] = key
		stat[p["kind"]] = int(stat.get(p["kind"], 0)) + 1
		AiBox.on_delivery(c, p["kind"])
	return i

func _in_box(f: Footballer, c: AiContext) -> int:
	var n := 0
	for m in c.team.players:
		if m != f and not m.is_keeper() and m.pos.x * c.dir > MatchGame.HALF_L - 16.5 and absf(m.pos.y) < 20.16: n += 1
	return n

func _blocked_soon(f: Footballer, c: AiContext) -> bool:
	for o in c.other.players:
		if o.is_keeper(): continue
		var d := o.pos - f.pos
		if d.length() < block_close and d.dot(f.face) > 0.0: return true
	return false

## {kind, action, mate} or {}
func _plan(f: Footballer, c: AiContext) -> Dictionary:
	var t := f.pos.x * c.dir
	var side := signf(f.pos.y) if f.pos.y != 0.0 else 1.0
	# cut-back
	if t > MatchGame.HALF_L - cut_x:
		var best: Footballer = null
		var bs := -1e9
		for m in c.team.players:
			if m == f or m.is_keeper(): continue
			var mt := MatchGame.HALF_L - m.pos.x * c.dir
			if mt < 6.0 or mt > 20.0 or absf(m.pos.y) > 12.0: continue
			var room := c.pressure(m.pos)
			if room < cut_free or c.lane_blocked(f.pos, m.pos, cut_lane, 1.5, 1.0): continue
			var sc := room - absf(m.pos.y) * 0.2 - absf(mt - 11.0) * 0.3
			if sc > bs:
				bs = sc
				best = m
		if best != null: return {"kind": "cut-back", "action": "pass", "mate": best}
	# near post: our runner ahead of every defender to it
	var np := Vector2((MatchGame.HALF_L - 5.0) * c.dir, side * 3.0)
	var runner: Footballer = null
	var rd := 1e9
	for m in c.team.players:
		if m == f or m.is_keeper(): continue
		var d := m.pos.distance_to(np)
		if d < reach_m and d < rd:
			rd = d
			runner = m
	if runner != null:
		var dd := 1e9
		for o in c.other.players:
			if not o.is_keeper(): dd = minf(dd, o.pos.distance_to(np))
		if rd + near_post_lead < dd: return {"kind": "near-post ball", "action": "pass", "mate": runner}
	# cross: the zone with our man and the fewest of theirs
	var bestz: Footballer = null
	var bz := 1e9
	for m in c.team.players:
		if m == f or m.is_keeper(): continue
		var mt := MatchGame.HALF_L - m.pos.x * c.dir
		if mt > cross_depth or absf(m.pos.y) > 14.0: continue
		var crowd := 0
		for o in c.other.players:
			if o.pos.distance_to(m.pos) < crowd_radius: crowd += 1
		var far_bonus := -0.5 if signf(m.pos.y) == -side else 0.0
		var sc := crowd + far_bonus + mt * 0.03
		if sc < bz:
			bz = sc
			bestz = m
	if bestz != null: return {"kind": "cross", "action": "lob", "mate": bestz}
	# an early cross: into the path of a box runner who is on his way to the near post / far post / spot
	var run: Footballer = null
	var rbest := 1e9
	for m in c.box_jobs:
		var j: Dictionary = c.box_jobs[m]
		if int(j.get("zone", 9)) > 2 or m == f: continue
		var d: float = m.pos.distance_to(j["spot"])
		if d < rbest and m.vel.length() > 3.0:
			rbest = d
			run = m
	if run != null and (c.box_go or _blocked_soon(f, c)) and rbest < early_reach: return {"kind": "early cross", "action": "lob", "mate": run}
	return {}
