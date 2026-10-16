class_name AiGk
extends AiRole
## Goalkeeper. Stands on his line tracking the ball across the goal, steps up when the team defends high, and distributes after a save:
## short to a centre back when patient, long (lob) towards the forwards when the formation is direct.

@export_group("Goalkeeper")
## he stands this far in front of the goal line
@export var line_offset := 1.8
## he follows the ball across the goal by this fraction, never further than z_limit metres from the centre
@export_range(0.0, 1.0) var follow_z := 0.45
@export var z_limit := 3.3
## when the ball is within this distance of his line he comes out a little (line_offset again)
@export var near_range := 24.0
## sweeping when the team attacks: base distance + sweep_line x the formation's line height
@export var sweep_base := 4.0
@export var sweep_line := 6.0
## distribution: chance of a long ball = directness x (1 - patience) + counter x long_counter
@export_range(0.0, 1.0) var long_counter := 0.2
## short distribution: extra score for a centre back, lane width that counts as blocked
@export var cb_bonus := 8.0
@export var pass_lane := 1.8
## a slow loose ball in his box (zone own_box, speed below this): he comes out and takes it if no team mate is clearly nearer
@export var claim_speed := 14.0
@export_group("Reading the game")
## play is up the pitch (ball past the halfway line): he pushes up as the ball goes, smoothly from sweep_from to sweep_to of the pitch depth, to sweep_base + sweep_line x line height
@export_range(0.0, 1.0) var sweep_from := 0.45
@export_range(0.0, 1.0) var sweep_to := 0.85
## the ball is near his goal: he narrows the angle, coming out up to this far (m) as it gets closer than near_range
@export var narrow_max := 3.5
## a loose ball outside the box, this close to his line (m), slower than sweep_ball_speed and heading his way: he sweeps it up if he is the nearest
@export var sweep_range := 22.0
@export var sweep_ball_speed := 16.0
## walking pace (fraction of top speed) while the play is far from his goal; alert pace is the usual jog
@export var relax_speed := 0.4
## he follows the ball across more the closer it is (extra fraction at the line)
@export var follow_close := 0.25

func _init() -> void:
	push_weight = 0.0
	shoot_bias = 0.0
	dribble_urge = 0.0

func think(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	if c.carrier == f: return _with_ball(f, c, dt)
	var goal_x := c.own_goal().x
	var bd := absf(c.ball.x - goal_x)
	if c.carrier == null:
		var heading_in := c.ball_vel.x * c.dir < -1.0
		var box_claim := c.in_zone(c.ball, "own_box") and c.ball_vel.length() < claim_speed
		var sweep := bd < sweep_range and heading_in and c.ball_vel.length() < sweep_ball_speed
		if box_claim or sweep:
			var mine := f.pos.distance_to(c.ball)
			var nearest := true
			for m in c.team.players:
				if m != f and m.pos.distance_to(c.ball) < mine - 1.0: nearest = false
			if nearest: return _go(c, c.ball + c.ball_vel * 0.3, c.s.sprint_factor)
	var line_x := goal_x + c.dir * line_offset
	var depth := c.depth(c.ball)
	var x := line_x
	var speed := c.s.jog_factor
	if depth > sweep_from:                                              # the play is up the pitch: he goes with it
		x = line_x + c.dir * (sweep_base + sweep_line * c.f("line_height")) * smoothstep(sweep_from, sweep_to, depth)
		if not c.has_ball or depth > sweep_to: speed = relax_speed
	elif bd < near_range:                                              # the ball is close: narrow the angle
		x = line_x + c.dir * narrow_max * (1.0 - bd / near_range)
	var close := 1.0 - clampf(bd / near_range, 0.0, 1.0)
	var z := clampf(c.ball.y * (follow_z + follow_close * close), -z_limit, z_limit)
	if absf(f.pos.x - x) > 6.0: speed = maxf(speed, c.s.jog_factor)    # a long way off his spot: hurry back
	return _go(c, Vector2(x, z), speed)

func _with_ball(f: Footballer, c: AiContext, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	if f.hold < c.s.hold_min: return i
	var long := c.game.rng.randf() < c.f("directness") * (1.0 - c.s.patience) + c.f("counter") * long_counter
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f: continue
		var score := 0.0
		if long: score = c.depth(m.pos) * 30.0 + c.pressure(m.pos) * 2.0
		else: score = -m.pos.distance_to(f.pos) * 0.5 + c.pressure(m.pos) * 2.0 + (cb_bonus if m.role == "CB" else 0.0)
		if c.lane_blocked(f.pos, m.pos, pass_lane): score -= 20.0
		if score > bs:
			bs = score
			best = m
	if best != null:
		i.action = "lob" if long else "pass"
		i.target = best
	return i
	
