class_name AiSetPiece
extends Resource
## Where everybody stands at a restart (behaviour catalogue section 11, batch 5). While play is stopped (MatchGame.Phase.RESTART) AiBrain asks place() for every
## player but the taker; after the whistle the taker plays it (AiSetPieceTaker) and the box behaviours take over.
## Corners: attackers put their best headers on the near post, the far post, the six-yard box and the penalty spot (one screens the keeper), two at the edge, one short,
##   the rest stay back with markers on their forwards. Defenders play the hybrid most teams use: three zonal men across the six-yard box, a front-post man,
##   man-markers goal side on the rest, two at the edge (the nearer one goes to a short corner), one forward left up unless we are parking the bus.
## Free kicks: a wall sized by distance and angle (end man on the line to the near post), the rest hold a line at the edge of the box; attackers line up level with it.
## Goal kicks: short = CBs split to the edges of the box, the 6 drops in front, full backs high and wide; their front men mark the short options when they press.
## Throw-ins: one short up the line, one short back, one inside; markers tight on them. Penalties: everybody outside the box and the arc.
## Positions are metres in the team frame of the side being placed: along = from its own goal line (0) up, across + = the side of the ball. AiProfile > Set pieces.

@export_group("Corners: attacking")
## how many go into the box (best headers first: PHY with DEF for defenders, SHO for the rest), and their spots [along from THEIR goal line, across + = ball side]
@export var corner_box_spots: Array[Vector2] = [Vector2(6.0, 3.0), Vector2(6.0, -4.5), Vector2(7.5, 0.0), Vector2(11.0, -1.0), Vector2(2.0, 0.5)]
@export var corner_edge_spots: Array[Vector2] = [Vector2(19.0, 3.0), Vector2(19.0, -6.0)]
## the short option: this far along the goal line from the flag, this far in
@export var corner_short := Vector2(4.0, 10.0)
## how many stay back (the rest defence), at this distance from our own goal line
@export var corner_rest := 3
@export var corner_rest_along := 45.0

@export_group("Corners: defending")
## zonal men across the six-yard box and the front-post man [along from OUR goal line, across + = ball side]
@export var zonal_spots: Array[Vector2] = [Vector2(5.5, 3.0), Vector2(5.5, 0.0), Vector2(5.5, -3.0)]
@export var front_post := Vector2(1.0, 3.6)
@export var edge_spots_def: Array[Vector2] = [Vector2(17.5, 6.0), Vector2(17.5, -5.0)]
## a forward stays up here unless the stance parks the bus
@export var leave_up := Vector2(42.0, 0.0)
## a marker stands this far goal side of his man
@export var mark_goal_side := 1.0

@export_group("Free kicks")
## wall size by distance (m) from goal: closer than wall_near = wall_n_near men, closer than wall_far = wall_n_far, beyond wall_none = no wall; wide angles (more than
## wide_z across) take one less
@export var wall_near := 20.0
@export var wall_far := 27.0
@export var wall_none := 32.0
@export var wall_n_near := 4
@export var wall_n_far := 3
@export var wide_z := 16.0
@export var wall_gap := 0.7
## the defending line stands this far from our goal line on a wide free kick (the offside line), attackers line up level with it
@export var fk_line := 15.0

@export_group("Goal kicks and throw-ins")
## centre backs split to here [along, across] (a middle one of three stays central)
@export var gk_cb_spots: Array[Vector2] = [Vector2(4.0, 15.0)]
@export var gk_pivot := Vector2(19.0, 0.0)
@export var gk_fullback := Vector2(26.0, 28.0)
## throw-in: short options [along from the throw (+ = towards their goal), in from the touchline]
@export var throw_spots: Array[Vector2] = [Vector2(7.0, 2.5), Vector2(-6.0, 3.0), Vector2(1.0, 10.0)]
@export var throw_mark := 1.6

static var stat_placed := {}

## the spot for f at the restart in force (Vector2.INF = he plays as normal: his role decides)
func place(f: Footballer, c: AiContext) -> Vector2:
	var r := c.game.rules
	if r.kind == "" or f == r.taker or f.is_keeper() and r.kind != "penalty": return _keeper(f, c) if f.is_keeper() else Vector2.INF
	var attacking := r.team == c.team
	var memo: Dictionary = c.team.ai.get("sp_plan", {})
	if memo.get("key", "") != _key(r):
		memo = {"key": _key(r), "spots": _plan(c, attacking)}
		c.team.ai["sp_plan"] = memo
		stat_placed[r.kind] = int(stat_placed.get(r.kind, 0)) + 1
	return (memo["spots"] as Dictionary).get(f, Vector2.INF)

func _key(r: MatchRules) -> String:
	return "%s %d %.1f %.1f" % [r.kind, int(r.stat.get(r.kind, 0)), r.spot.x, r.spot.y]

## world point for a team-frame spot: along from own goal line, across (+ = ball side)
func _w(c: AiContext, along: float, across: float, side: float) -> Vector2:
	return c.clamp_pitch(Vector2((-MatchGame.HALF_L + along) * c.dir, across * side), 0.6)

func _plan(c: AiContext, attacking: bool) -> Dictionary:
	var r := c.game.rules
	var side := signf(r.spot.y) if absf(r.spot.y) > 0.5 else 1.0
	match r.kind:
		"corner": return _corner_att(c, side) if attacking else _corner_def(c, side)
		"free_kick": return _fk(c, attacking, side)
		"goal_kick": return _goal_kick(c, attacking)
		"throw_in": return _throw(c, attacking, side)
		"penalty": return _penalty(c)
	return {}

func _header_score(f: Footballer) -> float:
	return f.stat("PHY", 60) * 0.6 + (f.stat("DEF", 60) if f.role in ["CB", "LB", "RB", "CDM"] else f.stat("SHO", 60)) * 0.4

func _outfield(c: AiContext) -> Array:
	var out: Array = []
	for m in c.team.players:
		if not m.is_keeper() and m != c.game.rules.taker: out.append(m)
	return out

func _corner_att(c: AiContext, side: float) -> Dictionary:
	var spots := {}
	var pool := _outfield(c)
	var L := 2.0 * MatchGame.HALF_L
	# the rest defence first: the least useful in the air among CB/FB/CDM
	pool.sort_custom(func(a, b): return _header_score(a) > _header_score(b))
	var box := pool.slice(0, corner_box_spots.size())
	var others := pool.slice(corner_box_spots.size())
	for i in box.size():
		var v: Vector2 = corner_box_spots[i]
		spots[box[i]] = _w(c, L - v.x, v.y, side)
	others.sort_custom(func(a, b): return a.stat("SHO", 60) > b.stat("SHO", 60))
	var e := 0
	var rest_left := corner_rest
	var leftover: Array = []
	for m in others:
		if e < corner_edge_spots.size() and m.role in ["CM", "CAM", "LW", "RW", "ST", "CDM"]:
			spots[m] = _w(c, L - corner_edge_spots[e].x, corner_edge_spots[e].y, side)
			e += 1
		else: leftover.append(m)
	var short_done := false
	for m in leftover:
		if not short_done and m.role in ["LW", "RW", "CM", "CAM", "LB", "RB"]:
			spots[m] = _w(c, L - corner_short.x, MatchGame.HALF_W - corner_short.y, side)
			short_done = true
		elif rest_left > 0:
			spots[m] = _w(c, corner_rest_along, (rest_left - 2) * 9.0, 1.0)
			rest_left -= 1
		else:
			spots[m] = _w(c, L - 22.0, -side * 10.0, side)
	return spots

func _corner_def(c: AiContext, side: float) -> Dictionary:
	var spots := {}
	var pool := _outfield(c)
	var used := {}
	# one forward stays up (not when parking the bus)
	if not c.stance.press_never:
		var fw: Footballer = null
		for m in pool:
			if m.role == "ST" and (fw == null or m.stat("PAC", 60) > fw.stat("PAC", 60)): fw = m
		if fw != null:
			used[fw] = true
			spots[fw] = _w(c, leave_up.x, leave_up.y, side)
	# zonal men: the best headers among the defenders
	var heads := pool.duplicate()
	heads.sort_custom(func(a, b): return _header_score(a) > _header_score(b))
	var z := 0
	for m in heads:
		if z >= zonal_spots.size(): break
		if used.has(m): continue
		used[m] = true
		spots[m] = _w(c, zonal_spots[z].x, zonal_spots[z].y, side)
		z += 1
	# front post
	for m in heads:
		if not used.has(m) and m.role in ["LB", "RB", "CM", "LW", "RW", "CDM"]:
			used[m] = true
			spots[m] = _w(c, front_post.x, front_post.y, side)
			break
	# edge
	var e := 0
	for m in pool:
		if e >= edge_spots_def.size(): break
		if not used.has(m) and m.role in ["CM", "CAM", "LW", "RW", "ST"]:
			used[m] = true
			spots[m] = _w(c, edge_spots_def[e].x, edge_spots_def[e].y, side)
			e += 1
	# man-markers on their men in the box, goal side
	var goal := c.own_goal()
	var theirs: Array = []
	for o in c.other.players:
		if o.is_keeper() or o == c.game.rules.taker: continue
		if o.pos.x * c.dir < -MatchGame.HALF_L + 20.0: theirs.append(o)
	for m in pool:
		if used.has(m): continue
		var best: Footballer = null
		var bd := 1e9
		for o in theirs:
			if spots.values().has(o): continue
			var d: float = m.pos.distance_to(o.pos)
			if d < bd:
				bd = d
				best = o
		used[m] = true
		if best != null:
			theirs.erase(best)
			spots[m] = best.pos + (goal - best.pos).normalized() * mark_goal_side
		else:
			spots[m] = _w(c, 11.0, -side * 2.0, side)
	return spots

func _fk(c: AiContext, attacking: bool, side: float) -> Dictionary:
	var spots := {}
	var r := c.game.rules
	var pool := _outfield(c)
	if attacking:
		var bt := r.spot.x * c.dir
		if bt < 15.0: return {}                                                # a free kick in our own half: play on as normal
		var along := 2.0 * MatchGame.HALF_L - fk_line - 0.8                    # level with their line, just onside
		pool.sort_custom(func(a, b): return _header_score(a) > _header_score(b))
		var n := 0
		for m in pool:
			if n < 5:
				spots[m] = _w(c, along, (n - 2) * 3.2 - 2.0, side)
				n += 1
			elif m.role in ["CB", "LB", "RB", "CDM"]:
				spots[m] = Vector2(-5.0 * c.dir, clampf(m.slot.y * 0.4, -12.0, 12.0))
		return spots
	# defending: the wall, then a line at the edge of the box
	var goal := c.own_goal()
	var d: float = r.spot.distance_to(goal)
	var n_wall := 0
	if d < wall_near: n_wall = wall_n_near
	elif d < wall_far: n_wall = wall_n_far
	elif d < wall_none: n_wall = 2
	if absf(r.spot.y) > wide_z: n_wall = maxi(n_wall - 2, 1 if d < wall_none else 0)
	var near_post := Vector2(goal.x, signf(r.spot.y if r.spot.y != 0.0 else 1.0) * MatchGame.GOAL_HALF)
	var to_np := (near_post - r.spot).normalized()
	var across := Vector2(-to_np.y, to_np.x)
	if across.dot(Vector2(0.0, -signf(r.spot.y if r.spot.y != 0.0 else 1.0))) < 0.0: across = -across   # the wall builds from the near post across the goal
	var end := r.spot + to_np * c.s.restart_distance
	pool.sort_custom(func(a, b): return a.pos.distance_to(end) < b.pos.distance_to(end))
	var used := {}
	for i in mini(n_wall, pool.size()):
		var m: Footballer = pool[i]
		used[m] = true
		spots[m] = end + across * (wall_gap * i)
	for m in pool:
		if used.has(m): continue
		if m.role == "ST" and not c.stance.press_never:
			spots[m] = _w(c, leave_up.x, 0.0, side)
			continue
		var y := clampf(m.slot.y * 0.55, -18.0, 18.0)
		var line_along := clampf(r.spot.x * c.dir + MatchGame.HALF_L - 12.0, fk_line, 35.0)    # the line: at the edge of the box, higher for a free kick further out
		spots[m] = Vector2((-MatchGame.HALF_L + line_along) * c.dir, y)
	return spots

func _goal_kick(c: AiContext, attacking: bool) -> Dictionary:
	var spots := {}
	var pool := _outfield(c)
	if attacking:
		var cbs: Array = []
		for m in pool: if m.role == "CB": cbs.append(m)
		for m in cbs:
			var wide := absf(m.slot.y) > 3.0
			var v: Vector2 = gk_cb_spots[0]
			spots[m] = Vector2((-MatchGame.HALF_L + (v.x if wide else 2.0)) * c.dir, signf(m.slot.y) * absf(v.y) if wide else 0.0)
		for m in pool:
			if m.role == "CDM":
				spots[m] = Vector2((-MatchGame.HALF_L + gk_pivot.x) * c.dir, gk_pivot.y)
				break
		for m in pool:
			if m.role == "LB" or m.role == "RB":
				spots[m] = Vector2((-MatchGame.HALF_L + gk_fullback.x) * c.dir, signf(m.slot.y if m.slot.y != 0.0 else 1.0) * gk_fullback.y)
		return spots
	# their goal kick: when we press high, our front men stand on their centre backs
	if c.f("press") < c.s.press_line and not c.stance.press_always: return {}
	var their_cbs: Array = []
	for o in c.other.players:
		if o.role == "CB": their_cbs.append(o)
	var fronts: Array = []
	for m in pool:
		if m.role in ["ST", "LW", "RW", "CAM"]: fronts.append(m)
	for i in mini(their_cbs.size(), fronts.size()):
		var o: Footballer = their_cbs[i]
		spots[fronts[i]] = o.pos + (c.own_goal() - o.pos).normalized() * 2.0
	return spots

func _throw(c: AiContext, attacking: bool, side: float) -> Dictionary:
	var spots := {}
	var r := c.game.rules
	var pool := _outfield(c)
	if attacking:
		pool.sort_custom(func(a, b): return a.pos.distance_to(r.spot) < b.pos.distance_to(r.spot))
		for i in mini(throw_spots.size(), pool.size()):
			var v: Vector2 = throw_spots[i]
			spots[pool[i]] = c.clamp_pitch(r.spot + Vector2(v.x * c.dir, -side * v.y), 0.6)
		return spots
	# defending: the nearest three take the nearest options, tight and goal side
	var opts: Array = []
	for o in c.other.players:
		if o != r.taker and not o.is_keeper() and o.pos.distance_to(r.spot) < 18.0: opts.append(o)
	opts.sort_custom(func(a, b): return a.pos.distance_to(r.spot) < b.pos.distance_to(r.spot))
	var used := {}
	var goal := c.own_goal()
	for o in opts.slice(0, 3):
		var best: Footballer = null
		var bd := 1e9
		for m in pool:
			if used.has(m): continue
			var d: float = m.pos.distance_to(o.pos)
			if d < bd:
				bd = d
				best = m
		if best == null: break
		used[best] = true
		spots[best] = o.pos + (goal - o.pos).normalized() * throw_mark
	return spots

func _penalty(c: AiContext) -> Dictionary:
	var spots := {}
	var pool := _outfield(c)
	var r := c.game.rules
	var gsign := signf(r.spot.x)
	var i := 0
	for m in pool:
		var y := -15.0 + (i % 10) * 3.3
		spots[m] = Vector2(gsign * (MatchGame.HALF_L - 19.5 - (i / 10) * 1.5), y)
		i += 1
	return spots

func _keeper(f: Footballer, c: AiContext) -> Vector2:
	var r := c.game.rules
	if r.kind == "penalty" and r.team != c.team: return Vector2(c.own_goal().x + c.dir * 0.2, 0.0)
	if r.kind == "corner" and r.team != c.team: return Vector2(c.own_goal().x + c.dir * 0.8, -signf(r.spot.y) * 0.6)
	if r.kind == "free_kick" and r.team != c.team and r.spot.distance_to(c.own_goal()) < wall_none:
		return Vector2(c.own_goal().x + c.dir * 1.2, -signf(r.spot.y if r.spot.y != 0.0 else 1.0) * 1.0)
	return Vector2.INF
