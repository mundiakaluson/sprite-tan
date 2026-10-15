class_name AiRole
extends RefCounted
## Base class of one role's AI (one file per role in scripts/ai/roles/). think() is called every frame for every player of that role and returns an AiIntent.
## It splits the situation into five cases, each a function you override per role:
##   _with_ball   he is the carrier              _support   his team has the ball
##   _defend      the opponent has the ball      _loose     nobody has it             _receive   a pass is coming to him
## Formations: AiContext carries the formation id / family and its numbers (line height, width, compactness, press, overlap, directness, counter, risk, all 0..1) and
## the player's slot style (data/styles.csv). Use `match c.family:` / `match c.formation_id:` inside a role to react to the formation.
## Positions in the team shape come from home_spot(): slot + style offset for the phase + the team line + a slide towards the ball. Everything tweakable is in MatchSettings.

## how much of the team line's push he follows (0 = stays back, 1 = goes with it)
var push_weight := 0.6
## carry-the-ball urge: how willing he is to dribble instead of passing (0..1)
var dribble_urge := 0.3
## shot taking: multiplies the shoot chance (0 = never shoots)
var shoot_bias := 0.5

func think(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	if c.game.pass_target == f and c.carrier == null: return _receive(f, c)
	if c.carrier == f: return _with_ball(f, c, dt)
	if c.has_ball: return _support(f, c)
	if c.carrier == null: return _loose(f, c)
	return _defend(f, c)

# ---------------------------------------------------------------- shape
func home_spot(f: Footballer, c: AiContext) -> Vector2:
	var s := c.s
	var push := 0.0
	var key := "defend"
	match c.phase:
		AiBrain.Phase.BUILD_UP:
			push = s.push_build_up
			key = "build"
		AiBrain.Phase.PROGRESS:
			push = s.push_progress
			key = "attack"
		AiBrain.Phase.FINAL_THIRD:
			push = s.push_final
			key = "attack"
		AiBrain.Phase.TRANSITION: push = 0.0
		_: push = s.push_defend
	var st := AiContext.style_row(f.style)
	var along := Data.num(st.get(key + "_dy"), 0.0) / 100.0 * Stadium.L * c.dir
	var across := Data.num(st.get(key + "_dx"), 0.0) / 100.0 * Stadium.W * c.dir
	var spot := f.slot + Vector2(along + c.dir * push * push_weight * (0.5 + c.f("line_height")), across)
	spot.y *= c.f("width") / 0.6
	spot.y += (c.ball.y - spot.y) * s.shift_to_ball * c.f("compactness")
	spot.x += (c.ball.x - spot.x) * 0.12
	return c.clamp_pitch(spot, 2.0)

func _go(c: AiContext, spot: Vector2, speed: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = spot
	i.speed = speed
	return i

# ---------------------------------------------------------------- the five cases
func _support(f: Footballer, c: AiContext) -> AiIntent:
	return _go(c, home_spot(f, c), c.s.jog_factor)

func _defend(f: Footballer, c: AiContext) -> AiIntent:
	if c.presser == f:
		var carrier := c.carrier
		var goal_side := carrier.pos + (c.own_goal() - carrier.pos).normalized() * 1.0
		var far := f.pos.distance_to(carrier.pos) > c.s.press_distance * (0.5 + c.f("press"))
		return _go(c, goal_side, c.s.jog_factor if far else c.s.sprint_factor)
	var spot := home_spot(f, c)
	# pick up an attacker in his zone: stand goal side of him
	var mark: Footballer = null
	var bd := c.s.marking_distance
	for o in c.other.players:
		if o == c.carrier: continue
		var d := o.pos.distance_to(spot)
		if d < bd:
			bd = d
			mark = o
	if mark != null: spot = spot.lerp(mark.pos + (c.own_goal() - mark.pos).normalized() * 2.0, 0.6)
	return _go(c, spot, c.s.jog_factor)

func _loose(f: Footballer, c: AiContext) -> AiIntent:
	if c.presser == f: return _go(c, c.ball + c.ball_vel * 0.3, c.s.sprint_factor)
	return _go(c, home_spot(f, c), c.s.jog_factor)

func _receive(f: Footballer, c: AiContext) -> AiIntent:
	var spot := c.ball + c.ball_vel * 0.6
	return _go(c, spot, c.s.sprint_factor if f.pos.distance_to(spot) > 3.0 else c.s.jog_factor)

func _with_ball(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	var s := c.s
	var i := _go(c, _carry_to(f, c), s.carry_factor)
	f.think -= dt
	if f.think > 0.0: return i
	f.think = s.think_interval
	var rng := c.game.rng
	if _wants_shot(f, c):
		i.action = "shoot"
		i.aim = Vector2(c.goal().x + c.dir * 1.5, rng.randf_range(-2.8, 2.8))
		return i
	var pressed := c.pressure(f.pos) < s.pressure_radius
	var forced := pressed or f.hold > s.hold_max or f.carried > s.max_carry
	if forced or (f.hold > s.hold_min and rng.randf() > dribble_urge):
		var o := _pick_pass(f, c)
		if not o.is_empty():
			i.action = o["action"]
			i.target = o["mate"]
	return i

# ---------------------------------------------------------------- carrying, shooting, passing (override the small ones)
func _carry_to(f: Footballer, c: AiContext) -> Vector2:
	var dirv := (c.goal() - f.pos).normalized()
	var opp := c.nearest_opponent(f.pos)
	if opp != null:
		var d := opp.pos - f.pos
		if d.length() < 7.0 and d.dot(dirv) > 0.0:
			var side := Vector2(-dirv.y, dirv.x)
			if side.dot(d) > 0.0: side = -side
			dirv = (dirv + side * 0.9).normalized()
	return c.clamp_pitch(f.pos + dirv * 8.0, 0.5)

func _wants_shot(f: Footballer, c: AiContext) -> bool:
	if f.pos.distance_to(c.goal()) > c.s.shoot_range: return false
	if c.lane_blocked(f.pos, c.goal(), 1.6): return false
	return c.game.rng.randf() < c.s.shoot_chance * shoot_bias * (0.5 + f.stat("SHO", 60) / 100.0)

## the best pass: {mate, action} or {} when nothing is worth it. Scores forward gain, space around the receiver, the length the settings like, blocked lanes and risk.
func _pick_pass(f: Footballer, c: AiContext) -> Dictionary:
	var s := c.s
	var forward_w := 0.25 + 0.5 * c.f("directness") - s.patience * 0.2
	var best := {}
	var bs := -1e9
	for o in c.pass_options(f):
		var m: Footballer = o["mate"]
		var score: float = o["forward"] * forward_w + minf(o["open"], 10.0) * 1.2 - absf(o["dist"] - s.ideal_pass) * 0.3
		if o["blocked"]: score -= 25.0
		if m.is_keeper(): score -= 8.0
		if c.depth(m.pos) > 0.7 and o["open"] < 3.0: score -= (1.0 - c.f("risk")) * 8.0
		score += _pass_bias(f, m, c)
		if score > bs:
			bs = score
			best = {"mate": m, "action": "pass"}
	if not best.is_empty() and bs < -6.0: return {}
	return best

## role-specific taste: add or subtract from a pass option's score
func _pass_bias(_f: Footballer, _m: Footballer, _c: AiContext) -> float:
	return 0.0
