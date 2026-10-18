class_name AiBox
extends Resource
## Play around the box when the ball is out wide (behaviour catalogue sections 9-11 "Cross or cut-back", "Attack the zones", "Near post on crosses", batch 4).
## Attacking: with our carrier wide in their final third, runners are given the box zones (near post, far post, penalty spot, the cut-back zone, the edge),
##  as many as the stance allows; they wait just outside their zone and attack it when the delivery is coming (the carrier reaches the delivery line or shapes
##  to cross), timing it so they arrive with the ball. AiCross (a behaviour) picks the delivery: cut-back, early cross or the near-post ball.
## Defending: their carrier wide in our final third -> the nearest CB takes the near-post zone, the rest of the back line marks the men in the box goal side and
##  half-turned (ball and man), the far full back tucks in to the back post, the 6 holds the penalty spot, and two midfielders drop to the edge for second balls.
## Distances are metres from the goal line (along) and from the middle of the goal (across, + = the ball's side). AiProfile > Box, scenes/ai/box.tres.

@export_group("When")
@export var box_enabled := true
## the carrier is "wide in the final third": at least wide_z (m) from the middle and within final_x (m) of their goal line
@export var wide_z := 13.0
@export var final_x := 45.0
## the jobs stay on this long (real s) after the ball leaves the wide area, while we keep it
@export var job_hold := 1.5
## runners go when the carrier is within go_x (m) of the goal line, or shapes to cross
@export var go_x := 19.0

@export_group("Attacking zones")
## zones: [along from the goal line, across (+ = ball side)]
@export var near_post := Vector2(5.0, 3.0)
@export var far_post := Vector2(5.5, -4.0)
@export var penalty_spot := Vector2(11.0, 0.0)
@export var cut_back := Vector2(12.0, 6.5)
@export var edge := Vector2(18.5, -2.0)
## who fills them first (role order per zone)
@export var near_post_roles := PackedStringArray(["ST", "CAM", "LW", "RW"])
@export var far_post_roles := PackedStringArray(["LW", "RW", "ST", "LB", "RB"])
@export var spot_roles := PackedStringArray(["CAM", "ST", "CM"])
@export var cut_back_roles := PackedStringArray(["CM", "CAM"])
@export var edge_roles := PackedStringArray(["CM", "CDM", "CAM"])
## zones filled by stance (the first n of near post, far post, spot, cut-back, edge); others: box_default
@export var box_default := 4
@export var box_by_stance := {"press_high": 5, "push_up": 5, "park_bus": 2, "counter": 3, "mid_block": 4}
## before the delivery a runner waits this far further out than his zone (m), and this much nearer the middle
@export var wait_back := 5.0
## a runner further than this (m) from his waiting spot sprints there
@export var far_sprint := 6.0
@export_range(0.0, 1.0) var wait_central := 0.4

@export_group("Defending the box")
@export var defend_enabled := true
@export var d_near_post := Vector2(3.5, 2.8)
@export var d_back_post := Vector2(4.5, -4.5)
@export var d_spot := Vector2(11.0, 0.0)
@export var d_edge := Vector2(19.0, 5.0)
## a marker stands this far goal side of his man (and this much of the way across to him)
@export var mark_goal_side := 1.0
@export_range(0.0, 1.0) var mark_blend := 0.85
## attackers inside this far from our goal line count as in the box
@export var box_depth := 17.0
@export var box_half_width := 20.0
@export var marker_roles := PackedStringArray(["CB", "LB", "RB", "CDM"])
@export var edge_roles_def := PackedStringArray(["CM", "CAM", "LW", "RW"])

static var stat_attacks := 0          ## crossing situations
static var stat_in_box := []          ## players of ours in the box at each delivery
static var stat_deliveries := {}

## team-frame point for a zone: v.x along from their goal line (attacking) / ours (defending), v.y across with + = the ball's side
func _zone(c: AiContext, v: Vector2, side: float, attacking: bool) -> Vector2:
	var gx := MatchGame.HALF_L - v.x if attacking else -MatchGame.HALF_L + v.x
	return Vector2(gx * c.dir, v.y * side)

## once per team per frame
func compute(c: AiContext, _dt: float) -> void:
	var keep := c.has_ball or (c.carrier == null and c.game.pass_target != null and c.game.pass_target.team == c.team)
	if keep and not c.box_jobs.is_empty() and c.game.clock < c.box_until and c.box_was_attack:
		return                                                                # the runs carry on a moment after the ball comes inside
	c.box_jobs.clear()
	c.box_go = false
	c.box_was_attack = false
	if not box_enabled: return
	var k := c.carrier
	if k == null: return
	var kt := k.pos.x * c.dir
	var side := signf(k.pos.y) if k.pos.y != 0.0 else 1.0
	if k.team == c.team:
		if kt < MatchGame.HALF_L - final_x or absf(k.pos.y) < wide_z:
			c.box_was = false
			return
		if not c.box_was:
			c.box_was = true
			stat_attacks += 1
		var sh := c.game.kicking.shaping(k)
		c.box_go = kt > MatchGame.HALF_L - go_x or (not sh.is_empty() and String(sh["action"]) in ["lob", "pass"] and absf((sh["to"] as Vector2).y) < 12.0)
		_assign_attack(c, k, side)
		c.box_until = c.game.clock + c.game_s(job_hold)
		c.box_was_attack = true
	elif defend_enabled:
		if kt > -MatchGame.HALF_L + final_x or absf(k.pos.y) < wide_z: return       # (kt is their x in our frame: near our goal = very negative)
		_assign_defend(c, k, side)

func _assign_attack(c: AiContext, k: Footballer, side: float) -> void:
	var n := int(box_by_stance.get(c.stance.id, box_default))
	var zones := [[near_post, near_post_roles], [far_post, far_post_roles], [penalty_spot, spot_roles], [cut_back, cut_back_roles], [edge, edge_roles]]
	var rest: Array = c.profile.transition.rest_players(c) if c.profile != null and c.profile.transition.rest_enabled else []
	var used := {}
	for zi in mini(n, zones.size()):
		var z: Vector2 = zones[zi][0]
		var roles: PackedStringArray = zones[zi][1]
		var spot := _zone(c, z, side, true)
		var best: Footballer = null
		var bs := 1e9
		for m in c.team.players:
			if m == k or m.is_keeper() or used.has(m) or rest.has(m) or not m.order.is_empty(): continue
			var ri := roles.find(m.role)
			if ri < 0: continue
			var sc := ri * 8.0 + m.pos.distance_to(spot)
			if sc < bs:
				bs = sc
				best = m
		if best == null: continue
		used[best] = true
		var wait := spot + Vector2(-c.dir * wait_back, -spot.y * wait_central)
		c.box_jobs[best] = {"spot": spot, "wait": wait, "zone": zi}

func _assign_defend(c: AiContext, k: Footballer, side: float) -> void:
	var used := {}
	var near := _zone(c, d_near_post, side, false)
	var cb := _nearest(c, near, PackedStringArray(["CB"]), used)
	if cb != null:
		used[cb] = true
		c.box_jobs[cb] = {"spot": near, "look": true}
	# their men in the box: a marker each, goal side
	var goal := c.own_goal()
	for o in c.other.players:
		if o == k or o.is_keeper(): continue
		var ot := o.pos.x * c.dir
		if ot > -MatchGame.HALF_L + box_depth or absf(o.pos.y) > box_half_width: continue
		var m := _nearest(c, o.pos, marker_roles, used)
		if m == null: break
		used[m] = true
		var at := o.pos + (goal - o.pos).normalized() * mark_goal_side
		c.box_jobs[m] = {"spot": at, "man": o, "look": true}
	var bp := _zone(c, d_back_post, side, false)
	var fb := _nearest(c, bp, PackedStringArray(["LB", "RB"]), used)
	if fb != null and signf(fb.slot.y) != side:
		used[fb] = true
		c.box_jobs[fb] = {"spot": bp, "look": true}
	var spot := _zone(c, d_spot, side, false)
	var six := _nearest(c, spot, PackedStringArray(["CDM", "CM"]), used)
	if six != null:
		used[six] = true
		c.box_jobs[six] = {"spot": spot, "look": true}
	for sgn in [1.0, -1.0]:
		var e := _zone(c, Vector2(d_edge.x, d_edge.y * sgn), side, false)
		var mm := _nearest(c, e, edge_roles_def, used)
		if mm != null:
			used[mm] = true
			c.box_jobs[mm] = {"spot": e}

func _nearest(c: AiContext, p: Vector2, roles: PackedStringArray, used: Dictionary) -> Footballer:
	var best: Footballer = null
	var bd := 1e9
	for m in c.team.players:
		if m.is_keeper() or used.has(m) or not m.order.is_empty() or m.lock > 0.0 or not (m.role in roles): continue
		if m == c.presser: continue
		var d := m.pos.distance_to(p)
		if d < bd:
			bd = d
			best = m
	return best

## per player after his role decided (before AiLine keeps attackers onside)
func post(f: Footballer, i: AiIntent, c: AiContext) -> void:
	if i == null or i.move_to == Vector2.INF or i.action != "" or not c.box_jobs.has(f): return
	if c.carrier == f or (c.game.pass_target == f and c.carrier == null): return
	var j: Dictionary = c.box_jobs[f]
	if c.has_ball:
		i.move_to = j["spot"] if c.box_go else j["wait"]
		i.speed = c.s.sprint_factor if c.box_go or f.pos.distance_to(i.move_to) > far_sprint else c.s.jog_factor
		i.note = "box run" if c.box_go else "box wait"
		return
	i.move_to = c.clamp_pitch(j["spot"], 0.5)
	i.speed = c.s.sprint_factor if f.pos.distance_to(i.move_to) > 4.0 else c.s.jog_factor
	i.note = "defend box"
	if j.get("look", false):                                                  # half-turned: between the ball and his man / the goal mouth
		var man: Footballer = j.get("man", null)
		var a := (c.ball - f.pos).normalized()
		var b := ((man.pos if man != null else c.own_goal()) - f.pos).normalized()
		f.ai["look"] = (a + b).normalized() if (a + b).length() > 0.1 else a
		f.ai["look_until"] = c.game.clock + c.game_s(0.2)

## count our players in the box when a cross / cut-back is played (MatchKicking via AiBrain)
static func on_delivery(c: AiContext, kind: String) -> void:
	var n := 0
	for m in c.team.players:
		if m.is_keeper(): continue
		if m.pos.x * c.dir > MatchGame.HALF_L - 16.5 and absf(m.pos.y) < 20.16: n += 1
	stat_in_box.append(n)
	stat_deliveries[kind] = int(stat_deliveries.get(kind, 0)) + 1
