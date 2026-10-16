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
@export_group("One on one")
## an opponent with the ball, running at him (at least rush_min_speed m/s), within rush_range m of the goal line and rush_lane m of the middle, with nobody back to deal with it: he goes out to close him down.
## A defender goal-side of the carrier (within cover_width m of his line to goal) means no rush; one right behind him (within catch_up m, at least catch_ratio of his speed, not tired / down) is catching him up: he waits.
@export var rush_range := 32.0
@export var rush_min_speed := 4.5
@export var rush_lane := 24.0
@export var cover_width := 6.0
@export var catch_up := 7.0
@export_range(0.3, 1.5) var catch_ratio := 0.9
## a defender below this stamina, or on the floor (locked in a fall), does not count
@export var chaser_tired := 0.25
## once out, he commits unless a defender gets goal-side
@export var rush_sticky := true
## once started he keeps coming for at least this many seconds
@export var rush_hold := 1.2
## closes in to this many metres, then smothers (MatchSettings > Keeper one on one)
@export var smother_range := 2.8
## when the carrier is this close he stops running at him and holds his ground (m)
@export var rush_stop := 1.4

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
	if c.carrier == f:
		if c.profile != null:                                                    # keeper behaviours with the ball (AiKeeperGesture, ...)
			for b in c.profile.all_behaviours():
				if b != null and b.applies(f, AiBehaviour.WITH_BALL) and b.wants(f, c, self):
					var o := b.act(f, c, self, dt)
					if o != null: return o
		return _with_ball(f, c, dt)
	if (c.carrier == null or c.carrier.team == f.team) and _now() > float(f.ai.get("rush_t", 0.0)): f.ai["rush"] = false
	if c.carrier != null and c.carrier.team != f.team:
		if _breakaway(f, c): return rush(f, c)
		if _now() > float(f.ai.get("rush_t", 0.0)): f.ai["rush"] = false
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
	if f.ai.has("bisect_z"):                                           # his scan: stand on the bisector of the shooter's angle
		z = lerpf(z, clampf(float(f.ai["bisect_z"]), -z_limit, z_limit), c.s.bisect_weight)
	if f.ai.has("scan"):                                               # the ball is on its way: a step across towards where it will cross him, before he dives
		var sc: Dictionary = f.ai["scan"]
		if float(sc["t"]) < c.s.pre_step_time:
			z = lerpf(f.pos.y, float(sc["z"]), c.s.pre_step_k)
			x = f.pos.x
			speed = c.s.sprint_factor
	if absf(f.pos.x - x) > 6.0: speed = maxf(speed, c.s.jog_factor)    # a long way off his spot: hurry back
	return _go(c, Vector2(x, z), speed)

## a pointed-at team mate further than this (m) gets it lofted, nearer ones rolled / passed
@export var long_from := 30.0

@export_group("With the ball: calm")
## after he gets it he takes the heat out: walks back this many metres towards the middle of his goal for calm_back_time s, then scans his options
## (turns to look at the best calm_looks of them, calm_scan_time s in all) before he points / distributes. An opponent within calm_pressure m cuts it short.
@export var calm_back_dist := 3.0
@export var calm_back_time := 1.0
@export var calm_scan_time := 1.4
@export var calm_looks := 3
@export var calm_pressure := 6.0
@export var calm_walk := 0.35
@export var calm_turn_deg := 220.0

## seconds of the calm phase (walk back + scan) still to come for a keeper who has held it `hold` s; 0 = ready to play it
func calm_left(f: Footballer, c: AiContext) -> float:
	if c.pressure(f.pos) < calm_pressure: return 0.0
	return maxf(0.0, calm_back_time + calm_scan_time - f.hold)

func _with_ball(f: Footballer, c: AiContext, dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	if f.hold < 0.05: f.ai["calm_from"] = f.pos                           # where he got it
	if calm_left(f, c) > 0.0:
		if f.hold < calm_back_time:                                       # walk back a few steps towards the middle of his goal, no hurry
			var goal := c.own_goal()
			var from: Vector2 = f.ai.get("calm_from", f.pos)
			var back := from + (goal - from).normalized() * calm_back_dist
			back.x = clampf(back.x, -MatchGame.HALF_L + 1.0, MatchGame.HALF_L - 1.0)
			i.move_to = back
			i.speed = calm_walk
		else:                                                             # stand and look round: his best options, one after the other
			var opts := _options(f, c)
			if not opts.is_empty():
				var n := mini(calm_looks, opts.size())
				var k := clampi(int((f.hold - calm_back_time) / maxf(calm_scan_time / n, 0.05)), 0, n - 1)
				var to: Vector2 = (opts[k] as Footballer).pos - f.pos
				if to.length() > 0.5:
					var step := deg_to_rad(calm_turn_deg) * dt
					f.face = f.face.rotated(clampf(f.face.angle_to(to), -step, step)).normalized()
		return i
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
	var pointed: Footballer = f.ai.get("gk_target", null)                 # he pointed at somebody (AiKeeperGesture): that is who gets it
	if pointed != null and pointed.team == f.team:
		best = pointed
		long = pointed.pos.distance_to(f.pos) > long_from
	if best != null:
		i.action = "lob" if long else "pass"
		i.target = best
		f.ai.erase("gk_target")
	return i
	

## his team mates by how good an option they are (free, forward), best first
func _options(f: Footballer, c: AiContext) -> Array:
	var scored: Array = []
	for m in c.team.players:
		if m == f: continue
		var sc := c.depth(m.pos) * 12.0 + c.pressure(m.pos) * 2.0 - (20.0 if c.lane_blocked(f.pos, m.pos, pass_lane) else 0.0)
		scored.append([sc, m])
	scored.sort_custom(func(a, b): return a[0] > b[0])
	return scored.map(func(x): return x[1])

# ---------------------------------------------------------------- one on one
## the carrier is through on goal and nobody can stop it but the keeper (see the exports above)
func _breakaway(f: Footballer, c: AiContext) -> bool:
	var k := c.carrier
	var goal := c.own_goal()
	var committed: bool = f.ai.get("rush", false) and rush_sticky
	var line := absf(k.pos.x - goal.x)
	if line > rush_range * (1.3 if committed else 1.0) or absf(k.pos.y) > rush_lane * (1.3 if committed else 1.0): return false
	var to_goal := goal - k.pos
	if k.vel.length() < rush_min_speed * (0.5 if committed else 1.0) or k.vel.dot(to_goal) <= 0.0: return false
	var dirk := to_goal.normalized()
	for m in c.team.players:
		if m == f or m.is_keeper(): continue
		var down: bool = m.lock > 0.0 or m.stamina < chaser_tired                       # on the floor or out of legs: not a defender now
		if down: continue
		var rel := m.pos - k.pos
		var along := rel.dot(dirk)                                                    # > 0: between the carrier and the goal
		var across := absf(rel.x * dirk.y - rel.y * dirk.x)
		if along > 0.0 and across < cover_width: return false                         # goal-side cover
		if not committed and along < 0.0 and -along < catch_up and across < cover_width and m.vel.length() >= catch_ratio * k.vel.length(): return false    # catching him up: wait
	if not committed: f.ai["rush_t"] = _now() + rush_hold            # a rush lasts at least this long, no flicker
	f.ai["rush"] = true
	return true

## close the carrier down: run at his line to goal, then smother. `forced` = the human's Rush order (no conditions).
func rush(f: Footballer, c: AiContext) -> AiIntent:
	var k := c.carrier
	var i := AiIntent.new()
	var goal := c.own_goal()
	var d := f.pos.distance_to(k.pos)
	var ahead := k.pos + k.vel * 0.3
	i.move_to = c.clamp_pitch(ahead, 0.5)
	i.speed = c.s.sprint_factor
	i.note = "rush"
	if d < smother_range and f.lock <= 0.0:
		i.action = "smother"
		i.target = k
	elif d < rush_stop:
		i.move_to = f.pos
	if f.pos.distance_to(goal) > 30.0: i.move_to = c.clamp_pitch(goal + (k.pos - goal).normalized() * 25.0, 0.5)
	return i

func _now() -> float:
	return Engine.get_physics_frames() / float(Engine.physics_ticks_per_second)
