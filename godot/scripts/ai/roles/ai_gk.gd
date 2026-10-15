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

func _init() -> void:
	push_weight = 0.0
	shoot_bias = 0.0
	dribble_urge = 0.0

func think(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	if c.carrier == f: return _with_ball(f, c, dt)
	var line_x := c.own_goal().x + c.dir * line_offset
	var z := clampf(c.ball.y * follow_z, -z_limit, z_limit)
	var x := line_x
	if c.has_ball and c.depth(c.ball) > 0.5:
		x = line_x + c.dir * (sweep_base + sweep_line * c.f("line_height"))
	elif absf(c.ball.x - line_x) < near_range:
		x = line_x + c.dir * line_offset
	return _go(c, Vector2(x, z), c.s.jog_factor)

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
	
