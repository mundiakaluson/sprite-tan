class_name AiTransition
extends Resource
## The moments the ball changes hands (behaviour catalogue section 2, batch 2). Runs after the roles decided, like AiInteract:
##  Counter-press: we just lost it and have men near the ball -> the nearest `cp_pressers` sprint at the carrier, the next `cp_cutters` stand in the passing lanes
##   to his nearest team mates (forward ones first); after `cp_time` s, or when the ball escapes / we are outnumbered, we give up.
##  Recovery runs: for `recover_time` s after a loss everyone who is ahead of the ball and far from his spot sprints back (goal side), instead of jogging.
##  Rest defence: while we attack, the `rest_count` most defensive outfield players (by stance) stay behind the ball in two lines; the deepest ones keep goal side
##   of any of their forwards who stays up (the counter threat).
##  Counter-attack: we just won it with space ahead or numbers up -> for `counter_time` s the forwards sprint ahead (wide men wide and high, the striker in behind,
##   one midfielder joins) and the carrier looks forward first (AiRole._pick_pass reads c.countering). No space: we keep it (the normal game).
## Times are real seconds. AiProfile > Transition, scenes/ai/transition.tres.

@export_group("Counter-press")
@export var cp_enabled := true
@export var cp_time := 5.0
## we need at least cp_min_near players within cp_near (m) of the ball when it is lost
@export var cp_near := 12.0
@export var cp_min_near := 2
## not outnumbered: their players within cp_count_radius of the ball may be at most ours + cp_outnumber
@export var cp_count_radius := 15.0
@export var cp_outnumber := 1
## no counter-press with the ball this close to our goal (0..1 depth of the pitch in our frame); deeper we just get back
@export_range(0.0, 1.0) var cp_min_depth := 0.3
## the pressers and the lane cutters
@export var cp_pressers := 2
@export var cp_cutters := 2
## a cutter stands this share of the way from the carrier to the team mate he cuts off
@export_range(0.1, 0.9) var cp_lane_share := 0.4
## the ball escapes: a pass to a team mate further than this (m) from where it was lost
@export var cp_escape := 22.0

@export_group("Recovery runs")
@export var recover_time := 4.0
## sprints back when he is more than this many metres ahead of the ball and further than recover_far (m) from his spot
@export var recover_ahead := 5.0
@export var recover_far := 6.0

@export_group("Rest defence")
@export var rest_enabled := true
## outfield players who stay back while we attack, by stance id (anything else: rest_default)
@export var rest_default := 4
@export var rest_by_stance := {"press_high": 3, "push_up": 3, "mid_block": 4, "park_bus": 5, "counter": 5}
## only once the ball is past this depth (0..1)
@export_range(0.0, 1.0) var rest_from_depth := 0.45
## the deep line stays this far behind the ball (m), between rest_back_min and rest_back_max (team frame metres from the centre)
@export var rest_back_gap := 30.0
@export var rest_back_min := -22.0
@export var rest_back_max := 12.0
## the front line (the 6, a full back who tucks in) stays this far behind the ball
@export var rest_front_gap := 13.0
## a deep rest defender keeps this far goal side (m) of their forward who stays up, blending this much towards his line across
@export var rest_mark_goal_side := 4.0
@export_range(0.0, 1.0) var rest_mark_blend := 0.6
## who goes first into the rest defence (lower = more defensive)
@export var rest_order := {"CB": 0, "CDM": 1, "LB": 2, "RB": 2, "CM": 3, "CAM": 5, "LW": 6, "RW": 6, "ST": 7}

@export_group("Counter-attack")
@export var counter_enabled := true
@export var counter_time := 4.0
## the counter is on when, ahead of the ball, they have no more than ours + counter_numbers players, or the carrier has nobody within counter_space (m) in front
@export var counter_numbers := 1
@export var counter_space := 8.0
## roles that break forward, and how far ahead of the ball they aim (m)
@export var counter_roles := PackedStringArray(["ST", "LW", "RW", "CAM"])
@export var counter_ahead := 16.0
@export var counter_wide_z := 25.0
## one central midfielder joins
@export var counter_join_cm := true
## pass scoring while countering: each metre forward is worth this much more (AiRole._pick_pass)
@export var counter_forward_bonus := 0.6

static var stat_cp := 0
static var stat_cp_regain := 0
static var stat_counters := 0
static var stat_counter_shots := 0
static var stat_recover_frames := 0

## once per team per frame (AiBrain), after AiInteract and AiLine
func compute(c: AiContext, dt: float) -> void:
	var g := c.game
	var now := g.clock
	var k := g.carrier
	var poss_team: Team = k.team if k != null else c.team.ai.get("poss_team", null)
	var prev: Team = c.team.ai.get("poss_team", null)
	if k != null and prev != null and k.team != prev:
		if prev == c.team: _lost(c, now)
		else: _won(c, now)
	if k != null: c.team.ai["poss_team"] = k.team
	elif poss_team != null: c.team.ai["poss_team"] = poss_team
	c.cp_players.clear()
	# ---- counter-press
	if c.counter_press:
		var over := now - c.lost_t > c.game_s(cp_time) or (k != null and k.team == c.team)
		if not over and k != null and k.pos.distance_to(c.lost_at) > cp_escape: over = true
		if not over and _outnumbered(c): over = true
		if over: c.counter_press = false
		elif k != null: _assign_cp(c)
	# ---- counter-attack
	if c.countering and (now - c.won_t > c.game_s(counter_time) or (k != null and k.team != c.team)): c.countering = false

func _lost(c: AiContext, now: float) -> void:
	c.lost_t = now
	c.lost_at = c.game.carrier.pos
	c.countering = false
	if not cp_enabled or c.stance.press_never: return
	if c.depth(c.lost_at) < cp_min_depth: return
	var near := 0
	for m in c.team.players:
		if not m.is_keeper() and m.pos.distance_to(c.lost_at) < cp_near: near += 1
	if near < cp_min_near or _outnumbered(c): return
	c.counter_press = true
	stat_cp += 1

func _won(c: AiContext, now: float) -> void:
	c.won_t = now
	if c.counter_press: stat_cp_regain += 1                                   # won back while counter-pressing
	c.counter_press = false
	if not counter_enabled: return
	var k := c.game.carrier
	var bt := k.pos.x * c.dir
	var theirs := 0
	var ours := 0
	var in_front := 99.0
	for o in c.other.players:
		if o.is_keeper(): continue
		if o.pos.x * c.dir > bt: theirs += 1
		var d := o.pos - k.pos
		if d.x * c.dir > 0.0: in_front = minf(in_front, d.length())
	for m in c.team.players:
		if not m.is_keeper() and m != k and m.pos.x * c.dir > bt - 2.0: ours += 1
	if in_front > counter_space or (theirs <= ours + counter_numbers and in_front > counter_space * 0.5):
		c.countering = true
		stat_counters += 1

func _outnumbered(c: AiContext) -> bool:
	var b := c.ball
	var ours := 0
	var theirs := 0
	for m in c.team.players:
		if not m.is_keeper() and m.pos.distance_to(b) < cp_count_radius: ours += 1
	for o in c.other.players:
		if not o.is_keeper() and o.pos.distance_to(b) < cp_count_radius: theirs += 1
	return theirs > ours + cp_outnumber

## who presses the carrier, who cuts which lane
func _assign_cp(c: AiContext) -> void:
	var k := c.game.carrier
	var mine: Array = []
	for m in c.team.players:
		if m.is_keeper() or m.lock > 0.0 or not m.order.is_empty() or c.cover.has(m): continue
		mine.append(m)
	mine.sort_custom(func(a, b): return a.pos.distance_to(k.pos) < b.pos.distance_to(k.pos))
	var n := 0
	var goal := c.own_goal()
	for i in mini(cp_pressers, mine.size()):
		var m: Footballer = mine[i]
		var at := k.pos + (goal - k.pos).normalized() * 1.0 if i == 0 else k.pos + (k.pos - goal).normalized() * 0.8 + Vector2(0.0, signf(m.pos.y - k.pos.y) * 1.2)
		c.cp_players[m] = at
		n += 1
	# lanes: their players nearest to the carrier, forward ones (towards our goal) first
	var opts: Array = []
	for o in c.other.players:
		if o == k or o.is_keeper(): continue
		var fwd := (k.pos.x - o.pos.x) * c.dir                        # + = closer to our goal than the carrier
		opts.append({"o": o, "score": o.pos.distance_to(k.pos) - fwd * 0.5})
	opts.sort_custom(func(a, b): return a["score"] < b["score"])
	var used := 0
	for i in range(n, mine.size()):
		if used >= cp_cutters or used >= opts.size(): break
		var o: Footballer = opts[used]["o"]
		c.cp_players[mine[i]] = k.pos.lerp(o.pos, cp_lane_share)
		used += 1

## per player, after AiInteract.post
func post(f: Footballer, i: AiIntent, c: AiContext) -> void:
	if i == null or i.move_to == Vector2.INF or i.action != "" or f.is_keeper() or not f.order.is_empty(): return
	if c.carrier == f or (c.game.pass_target == f and c.carrier == null): return
	var now := c.game.clock
	if not c.has_ball:
		if c.cp_players.has(f):
			i.move_to = c.cp_players[f]
			i.speed = c.s.sprint_factor
			i.note = "counter-press"
			return
		if now - c.lost_t < c.game_s(recover_time) and (f.pos.x - c.ball.x) * c.dir > recover_ahead and f.pos.distance_to(i.move_to) > recover_far:
			i.speed = c.s.sprint_factor                                      # recovery run: sprint back, head up
			stat_recover_frames += 1
		return
	if c.countering and counter_enabled:
		_counter_run(f, i, c)
		return
	if rest_enabled: _rest(f, i, c)

func _counter_run(f: Footballer, i: AiIntent, c: AiContext) -> void:
	var bt := c.ball.x * c.dir
	var runs := f.role in counter_roles
	if not runs and counter_join_cm and f.role == "CM":
		var cms: Array = []
		for m in c.team.players:
			if m.role == "CM": cms.append(m)
		cms.sort_custom(func(a, b): return a.pos.distance_to(c.ball) < b.pos.distance_to(c.ball))
		runs = not cms.is_empty() and cms[0] == f
	if not runs: return
	var x := maxf(i.move_to.x * c.dir, minf(bt + counter_ahead, MatchGame.HALF_L - 8.0))
	var y := i.move_to.y
	if f.role == "LW" or f.role == "RW": y = signf(f.slot.y if f.slot.y != 0.0 else 1.0) * counter_wide_z
	i.move_to = Vector2(x * c.dir, y)
	i.speed = c.s.sprint_factor
	i.note = "counter"

func _rest(f: Footballer, i: AiIntent, c: AiContext) -> void:
	if c.depth(c.ball) < rest_from_depth: return
	var list := rest_players(c)
	var idx := list.find(f)
	if idx < 0: return
	var bt := c.ball.x * c.dir
	var deep := idx < 2 or f.role == "CB"
	var line := clampf(bt - rest_back_gap, rest_back_min, rest_back_max) if deep else bt - rest_front_gap
	if i.move_to.x * c.dir > line: i.move_to.x = line * c.dir
	if deep:                                                                  # their forward who stays up: goal side of him
		var threat: Footballer = null
		var bd := 18.0
		for o in c.other.players:
			if o.is_keeper(): continue
			var ot := o.pos.x * c.dir
			if ot > line + 6.0: continue
			var d := o.pos.distance_to(f.pos)
			if d < bd and not _taken(c, o, f):
				bd = d
				threat = o
		if threat != null:
			c.rest_marks[f] = threat
			var at := Vector2(minf(threat.pos.x * c.dir - rest_mark_goal_side, line) * c.dir, lerpf(i.move_to.y, threat.pos.y, rest_mark_blend))
			i.move_to = at
	i.note = "rest defence"

func _taken(c: AiContext, o: Footballer, me: Footballer) -> bool:
	for m in c.rest_marks:
		if m != me and c.rest_marks[m] == o: return true
	return false

## the rest defence right now: the most defensive outfield players (rest_order, then deepest), as many as the stance asks
func rest_players(c: AiContext) -> Array:
	var frame := Engine.get_physics_frames()
	if c.rest_frame == frame: return c.rest_list
	c.rest_frame = frame
	c.rest_marks.clear()
	var n := int(rest_by_stance.get(c.stance.id, rest_default))
	var cand: Array = []
	for m in c.team.players:
		if m.is_keeper() or m == c.carrier: continue
		cand.append(m)
	var near_side := signf(c.ball.y)
	cand.sort_custom(func(a, b):
		var ra := float(rest_order.get(a.role, 4)) + (0.6 if (a.role == "LB" or a.role == "RB") and signf(a.slot.y) == near_side else 0.0)
		var rb := float(rest_order.get(b.role, 4)) + (0.6 if (b.role == "LB" or b.role == "RB") and signf(b.slot.y) == near_side else 0.0)
		if ra != rb: return ra < rb
		return a.pos.x * c.dir < b.pos.x * c.dir)
	c.rest_list = cand.slice(0, n)
	return c.rest_list
