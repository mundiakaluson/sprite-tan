class_name AiRole
extends Resource
## Base class of one role's AI (one file per role in scripts/ai/roles/). It is a RESOURCE, so every number below shows in the inspector: open
## scenes/ai/profile_default.tres (an AiProfile), click a role, tune it; edits made while the match runs apply live (Remote tab). Save a copy for a different style of play.
## think() is called every frame for every player of that role and returns an AiIntent. It splits the situation into five cases, each a function you override per role:
##   _with_ball   he is the carrier              _support   his team has the ball
##   _defend      the opponent has the ball      _loose     nobody has it             _receive   a pass is coming to him
## Formations: AiContext carries the formation id / family and its numbers (line height, width, compactness, press, overlap, directness, counter, risk, all 0..1) and
## the player's slot style (data/styles.csv). Use `match c.family:` / `match c.formation_id:` inside a role to react to the formation.
## Where to stand: use the pitch map by name, e.g. _go(c, c.spot("left_half_space_high"), c.s.jog_factor), c.in_zone(f.pos, "opp_box"), c.zone("final_third_left") (data/pitch_zones.csv, pitch_spots.csv).
## Positions in the team shape come from home_spot(): slot + style offset for the phase + the team line + a slide towards the ball. Team-wide numbers are in MatchSettings.

@export_group("Team shape")
## how much of the team line's push he follows (0 = stays back, 1 = goes with it)
@export_range(0.0, 1.0) var push_weight := 0.6
## how far he drifts lengthwise towards the ball (0 = not at all)
@export_range(0.0, 0.5) var ball_follow_x := 0.12

@export_group("Pressing and marking")
## when closing the ball down he stands this far goal-side of the carrier
@export var press_goal_side := 1.0
## containing (stance without pressing): stand this far goal-side of the carrier and jog
@export var contain_distance := 6.0
## marking an attacker: stand this far goal-side of him, and blend this much towards him (1 = right on him)
@export var mark_goal_side := 2.0
@export_range(0.0, 1.0) var mark_blend := 0.6
## chasing a loose ball: aim this many seconds ahead of it
@export var chase_lookahead := 0.3
## receiving a pass: run to where the ball will be in this many seconds
@export var receive_lookahead := 0.6

@export_group("Carrying")
## how willing he is to dribble instead of passing (0..1)
@export_range(0.0, 1.0) var dribble_urge := 0.3
## the carrier runs towards a point this far ahead
@export var carry_distance := 8.0
## an opponent in front closer than this makes him sidestep, by this much sideways
@export var sidestep_range := 7.0
@export_range(0.0, 2.0) var sidestep_weight := 0.9

@export_group("Passing")
## score for each metre of space around the receiver (up to 10 m)
@export var open_weight := 1.2
## score lost per metre the pass differs from the ideal length (MatchSettings.ideal_pass)
@export var length_penalty := 0.3
@export var blocked_penalty := 25.0
@export var keeper_penalty := 8.0
## a receiver deeper than this (0..1 of the pitch) with an opponent closer than risk_open is a risky pass, costing risk_penalty x (1 - the formation's risk)
@export_range(0.0, 1.0) var risk_depth := 0.7
@export var risk_open := 3.0
@export var risk_penalty := 8.0
## best pass scoring below this is not worth it: keep the ball
@export var min_pass_score := -6.0
## forward gain weight = forward_base + forward_directness x the formation's directness - forward_patience x the settings' patience
@export var forward_base := 0.25
@export var forward_directness := 0.5
@export var forward_patience := 0.2

@export_group("Shooting")
## shot taking: multiplies the shoot chance (0 = never shoots)
@export_range(0.0, 2.0) var shoot_bias := 0.5
## a defender nearer than this to the line to goal blocks the shot
@export var lane_width := 1.6
## shot aim varies this far either side of the goal centre (metres)
@export var shot_spread := 2.8
## added to the settings' shoot range for this role
@export var range_bonus := 0.0

func think(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	var fx := c.profile.formation_for(c.formation_id) if c.profile != null else null
	if fx != null:
		var o := fx.think(f, c, self, dt)
		if o != null: return o
	if c.profile != null:
		var sit := AiBehaviour.situation_of(f, c)
		for b in c.profile.all_behaviours():
			if b != null and b.applies(f, sit) and b.wants(f, c, self):
				var o2 := b.act(f, c, self, dt)
				if o2 != null: return o2
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
	var spot := f.slot + Vector2(along + c.dir * push * c.stance.push_scale * push_weight * (0.5 + c.f("line_height")), across)
	spot.y *= c.f("width") / 0.6
	spot.y += (c.ball.y - spot.y) * s.shift_to_ball * c.f("compactness")
	spot.x += (c.ball.x - spot.x) * ball_follow_x
	return c.clamp_pitch(spot, 2.0)

func _go(_c: AiContext, spot: Vector2, speed: float) -> AiIntent:
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
		if c.stance.press_never: return _go(c, carrier.pos + (c.own_goal() - carrier.pos).normalized() * contain_distance, c.s.jog_factor)
		var goal_side := carrier.pos + (c.own_goal() - carrier.pos).normalized() * press_goal_side
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
	if mark != null: spot = spot.lerp(mark.pos + (c.own_goal() - mark.pos).normalized() * mark_goal_side, mark_blend)
	return _go(c, spot, c.s.jog_factor)

func _loose(f: Footballer, c: AiContext) -> AiIntent:
	if c.presser == f: return _go(c, c.ball + c.ball_vel * chase_lookahead, c.s.sprint_factor)
	return _go(c, home_spot(f, c), c.s.jog_factor)

func _receive(f: Footballer, c: AiContext) -> AiIntent:
	var spot := c.ball + c.ball_vel * receive_lookahead
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
		i.aim = Vector2(c.goal().x + c.dir * 1.5, rng.randf_range(-shot_spread, shot_spread))
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
		if d.length() < sidestep_range and d.dot(dirv) > 0.0:
			var side := Vector2(-dirv.y, dirv.x)
			if side.dot(d) > 0.0: side = -side
			dirv = (dirv + side * sidestep_weight).normalized()
	return c.clamp_pitch(f.pos + dirv * carry_distance, 0.5)

func _wants_shot(f: Footballer, c: AiContext) -> bool:
	if f.pos.distance_to(c.goal()) > c.s.shoot_range + range_bonus: return false
	if c.lane_blocked(f.pos, c.goal(), lane_width): return false
	return c.game.rng.randf() < c.s.shoot_chance * shoot_bias * (0.5 + f.stat("SHO", 60) / 100.0)

## an attacker (ST / winger / CAM set this): near their box he does not pass backwards unless there is nothing else on;
## each metre a pass goes backwards costs final_back_per_m once he is past final_depth (pitch depth 0..1)
@export var attacker := false
@export var final_depth := 0.72
@export var final_back_per_m := 1.6

## the best pass: {mate, action} or {} when nothing is worth it. Scores forward gain, space around the receiver, the length the settings like, blocked lanes and risk.
func _pick_pass(f: Footballer, c: AiContext) -> Dictionary:
	var s := c.s
	var forward_w := forward_base + forward_directness * c.f("directness") - s.patience * forward_patience
	var best := {}
	var bs := -1e9
	for o in c.pass_options(f):
		var m: Footballer = o["mate"]
		var score: float = o["forward"] * forward_w + minf(o["open"], 10.0) * open_weight - absf(o["dist"] - s.ideal_pass) * length_penalty
		if o["blocked"]: score -= blocked_penalty
		if m.is_keeper(): score -= keeper_penalty
		if c.depth(m.pos) > risk_depth and o["open"] < risk_open: score -= (1.0 - c.f("risk")) * risk_penalty
		score += _pass_bias(f, m, c)
		if attacker and c.depth(f.pos) > final_depth and o["forward"] < 0.0: score += o["forward"] * final_back_per_m      # going backwards near their box: last resort
		if score > bs:
			bs = score
			best = {"mate": m, "action": "pass"}
	if not best.is_empty() and bs < min_pass_score: return {}
	return best

## role-specific taste: add or subtract from a pass option's score
func _pass_bias(_f: Footballer, _m: Footballer, _c: AiContext) -> float:
	return 0.0
