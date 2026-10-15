class_name AiGk
extends AiRole
## Goalkeeper. Stands on his line tracking the ball across the goal, steps up when the team defends high, and distributes after a save:
## short to a centre back when patient, long (lob) towards the forwards when the formation is direct.

func _init() -> void:
	push_weight = 0.0
	shoot_bias = 0.0
	dribble_urge = 0.0

func think(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	if c.carrier == f: return _with_ball(f, c, dt)
	var line_x := c.own_goal().x + c.dir * 1.8
	var z := clampf(c.ball.y * 0.45, -3.3, 3.3)
	var x := line_x
	if c.has_ball and c.depth(c.ball) > 0.5:
		# the team is attacking: sweep a little higher, more so for a high line
		x = line_x + c.dir * (4.0 + 6.0 * c.f("line_height"))
	elif absf(c.ball.x - line_x) < 24.0:
		x = line_x + c.dir * 1.8
	return _go(c, Vector2(x, z), c.s.jog_factor)

func _with_ball(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	if f.hold < c.s.hold_min: return i
	var long := c.game.rng.randf() < c.f("directness") * (1.0 - c.s.patience) + c.f("counter") * 0.2
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f: continue
		var score := 0.0
		if long: score = c.depth(m.pos) * 30.0 + c.pressure(m.pos) * 2.0
		else: score = -m.pos.distance_to(f.pos) * 0.5 + c.pressure(m.pos) * 2.0 + (8.0 if m.role == "CB" else 0.0)
		if c.lane_blocked(f.pos, m.pos, 1.8): score -= 20.0
		if score > bs:
			bs = score
			best = m
	if best != null:
		i.action = "lob" if long else "pass"
		i.target = best
	return i
