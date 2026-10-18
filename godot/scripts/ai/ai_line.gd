class_name AiLine
extends Resource
## The line (behaviour catalogue, section 1 "Line: step up or drop", "Offside trap", and the forwards' "On the shoulder" / "Offside to onside").
## Out of possession the back line moves as ONE unit by reading the ball:
##   ball pressured (one of ours goal side and close)  -> hold, or squeeze up when the carrier faces away from our goal
##   carrier free and facing our goal                    -> drop: he can hit it in behind (never deeper than `floor_from_goal`)
##   ball played / carried backwards, or cleared upfield -> squeeze up
##   their carrier shapes to pass forward                -> the line leader (the CB with the best game sense) may spring the offside trap: the whole line steps up together
## The result is AiContext.line_shift (metres, + = towards their goal), which the formation files add to the height of their block, and line_urgent (step at a sprint).
## In possession every forward keeps onside: his spot is held this side of the offside line (second-last defender or the ball), by a margin that shrinks with
## game sense; poor ones lapse now and then and get caught. One stood offside comes back. AiProfile > Line, scenes/ai/line.tres.

@export_group("Defending line")
@export var line_enabled := true
## the carrier counts as pressured when one of ours is this close (m) and goal side of him; free when nobody is within free_dist (m)
@export var pressured_dist := 3.5
@export var free_dist := 7.0
## facing our goal = dot of his facing with the way to our goal above this
@export_range(-1.0, 1.0) var facing_goal := 0.35
## metres the line steps up (squeeze) or drops
@export var squeeze := 4.0
@export var drop := 7.0
## the ball moving away from our goal faster than this (m/s) with nobody on it = a back pass / clearance: squeeze up
@export var back_ball_speed := 5.0
## a long ball towards our goal faster than this (m/s) = drop
@export var long_ball_speed := 12.0
## how fast the line moves (m/s) to where it wants to be; while stepping or dropping fast it runs (line_urgent)
@export var shift_speed := 3.0
@export var urgent_shift_speed := 7.0
@export var urgent_gap := 2.5
## the line never drops deeper than this many metres from our goal line while the ball is further away than that plus floor_ball_gap
@export var floor_from_goal := 17.0
@export var floor_ball_gap := 6.0

@export_group("Offside trap")
@export var trap_enabled := true
## when their carrier shapes to play a forward ball (at least trap_forward m forwards) the leader springs it with chance trap_chance x his game sense / 100
@export var trap_forward := 8.0
@export_range(0.0, 1.0) var trap_chance := 0.45
## the line steps this far up together, for this long
@export var trap_step := 3.5
@export var trap_time := 1.1
## only for a ball aimed within trap_reach (m) in front of our line, or behind it
@export var trap_reach := 4.0
## no trap with the line closer to our goal than this (m)
@export var trap_min_from_goal := 24.0

@export_group("Staying onside")
@export var onside_enabled := true
## a forward keeps this much onside (m): onside_margin_poor at game sense 40, onside_margin_smart at 90
@export var onside_margin_poor := 1.4
@export var onside_margin_smart := 0.25
## lapses: at game sense 40 he forgets the line this often (per second; never at 90) for lapse_time s
@export var lapse_rate := 0.05
@export var lapse_time := 1.6

static var stat_traps := 0
static var stat_drops := 0          ## frames x team the line was dropping
static var stat_squeezes := 0

## once per team per frame (AiBrain): the offside line our forwards respect, and our own back line
func compute(c: AiContext, dt: float) -> void:
	c.offside_t = maxf(c.game.offside.second_last(c.team), maxf(c.ball.x * c.dir, 0.0))
	c.line_floor_t = -MatchGame.HALF_L + floor_from_goal
	if c.ball.x * c.dir < c.line_floor_t + floor_ball_gap: c.line_floor_t = -MatchGame.HALF_L + 3.0
	if not line_enabled or c.has_ball:
		c.line_target = 0.0
		c.line_mode = "attack" if c.has_ball else "off"
		c.line_shift = move_toward(c.line_shift, 0.0, shift_speed * dt)
		c.line_urgent = false
		return
	var now := c.game.clock
	var target := 0.0
	var mode := "hold"
	var k := c.carrier
	var own := c.own_goal()
	if k == null:
		var away_v := c.ball_vel.x * c.dir                                   # + = moving towards their goal
		if away_v > back_ball_speed:
			target = squeeze
			mode = "squeeze"
		elif away_v < -long_ball_speed:
			target = -drop
			mode = "drop"
	else:
		var to_goal := (own - k.pos).normalized()
		var facing := k.face.dot(to_goal) > facing_goal
		var pressed := false
		var near := 1e9
		for m in c.team.players:
			if m.is_keeper(): continue
			var d := m.pos.distance_to(k.pos)
			near = minf(near, d)
			if d < pressured_dist and m.pos.x * c.dir <= k.pos.x * c.dir + 0.5: pressed = true
		var going_back := k.vel.dot(to_goal) < -2.0
		if pressed and not facing:
			target = squeeze
			mode = "squeeze"
		elif going_back:
			target = squeeze * 0.6
			mode = "squeeze"
		elif near > free_dist and facing:
			target = -drop
			mode = "drop"
		if trap_enabled: _trap(c, k, now)
	if now < c.trap_until:
		target = maxf(target, c.line_shift_base + trap_step)
		mode = "trap"
	else:
		c.line_shift_base = c.line_shift
	c.line_target = target
	c.line_mode = mode
	var gap := absf(target - c.line_shift)
	c.line_urgent = gap > urgent_gap or mode == "trap"
	c.line_shift = move_toward(c.line_shift, target, (urgent_shift_speed if c.line_urgent else shift_speed) * dt)
	if mode == "drop": stat_drops += 1
	elif mode == "squeeze": stat_squeezes += 1

func _trap(c: AiContext, k: Footballer, now: float) -> void:
	var sh := c.game.kicking.shaping(k)
	if sh.is_empty() or not (String(sh["action"]) in ["pass", "through", "lob"]): return
	var to: Vector2 = sh["to"]
	if (k.pos.x - to.x) * c.dir < trap_forward: return                    # not a forward ball towards our goal
	var key := "%d" % k.get_instance_id()
	if c.team.ai.get("trap_read", "") == key + str(int(now / 3.0)): return  # one read per kick
	c.team.ai["trap_read"] = key + str(int(now / 3.0))
	var line_t := _back_t(c)
	if line_t < -MatchGame.HALF_L + trap_min_from_goal: return
	if to.x * c.dir > line_t + trap_reach: return                          # only a ball aimed at (or behind) our line: a pass to feet in midfield is no trap moment
	var leader := leader_of(c)
	var sense := 60.0 if leader == null else (leader.stat("PAS", 60) + leader.stat("DRI", 60) + 2.0 * leader.stat("DEF", 60)) * 0.25
	if c.game.rng.randf() < trap_chance * sense / 100.0:
		c.trap_until = now + trap_time * 5400.0 / (c.s.match_minutes * 60.0)
		c.line_shift_base = c.line_shift
		stat_traps += 1

## the centre back who runs the line: best reading of the game (DEF counts double)
func leader_of(c: AiContext) -> Footballer:
	var best: Footballer = null
	var bs := -1.0
	for m in c.team.players:
		if m.role != "CB": continue
		var sc := m.stat("PAS", 60) + m.stat("DRI", 60) + 2.0 * m.stat("DEF", 60)
		if sc > bs:
			bs = sc
			best = m
	return best

## team-frame x of our back line (average of CB / LB / RB)
func _back_t(c: AiContext) -> float:
	var sum := 0.0
	var n := 0
	for m in c.team.players:
		if m.role in ["CB", "LB", "RB"]:
			sum += m.pos.x * c.dir
			n += 1
	return sum / n if n > 0 else 0.0

## per player after his role decided: forwards of the side with the ball keep onside
func post(f: Footballer, i: AiIntent, c: AiContext) -> void:
	if not onside_enabled or i == null or i.move_to == Vector2.INF or i.action != "": return
	if not c.has_ball or f.is_keeper() or c.carrier == f or not f.order.is_empty(): return
	if c.game.pass_target == f and c.carrier == null: return
	var sense := (f.stat("PAS", 60) + f.stat("DRI", 60)) * 0.5
	var smart := clampf((sense - 40.0) / 50.0, 0.0, 1.0)
	var now := c.game.clock
	if float(f.ai.get("lapse_until", -1.0)) > now: return                  # not watching the line just now
	var dt := c.game.get_physics_process_delta_time()
	if c.game.rng.randf() < lapse_rate * (1.0 - smart) * dt:
		f.ai["lapse_until"] = now + lapse_time * 5400.0 / (c.s.match_minutes * 60.0)
		return
	var line := c.offside_t - lerpf(onside_margin_poor, onside_margin_smart, smart)
	if i.move_to.x * c.dir > line: i.move_to.x = line * c.dir
