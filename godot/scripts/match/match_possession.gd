class_name MatchPossession
extends RefCounted
## Who has the ball: carrying it at the feet, picking up a loose ball, keeper saves, tackles and the kick itself (through the ball's own states).

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

func take(f: Footballer) -> void:
	g.carrier = f
	g.last_touch = f
	g.pass_target = null
	f.hold = 0.0
	f.carried = 0.0
	f.think = g.rng.randf_range(0.2, 0.5)
	g.ball.hold()

## every physics frame
func update(dt: float) -> void:
	if g.carrier != null:
		_carry()
		if g.phase == MatchGame.Phase.PLAY:
			g.carrier.hold += dt
			_auto_tackles(dt)
		return
	if g.phase == MatchGame.Phase.PLAY: _loose(dt)

func _carry() -> void:
	var c := g.carrier
	var spot := c.pos + c.face * (g.settings.touch_ahead + 0.06 * c.vel.length())
	var b := g.ball
	b.phys.pos = Vector3(spot.x, b.phys.rad, spot.y)
	var v3 := Vector3(c.vel.x, 0.0, c.vel.y)
	b.phys.vel = v3
	b.live = false
	b.preview_spin = v3.cross(Vector3.UP) / b.phys.rad if v3.length() > 0.1 else Vector3.ZERO
	g.last_touch = c

func _loose(_dt: float) -> void:
	var s := g.settings
	var b := g.ball
	var bp := b.phys.pos
	var b2 := Vector2(bp.x, bp.z)
	var speed := b.phys.vel.length()
	var best: Footballer = null
	var bd := 1.0
	for f in g.all:
		if f.no_touch > 0.0: continue
		var reach := s.pickup_reach
		var max_h := 1.3
		if f.is_keeper():
			reach = s.keeper_reach + f.stat("REF", 60) * 0.012
			max_h = 2.5
		if f == g.pass_target: reach *= 1.25
		if bp.y > max_h: continue
		var d := f.pos.distance_to(b2) / reach
		if d < bd:
			bd = d
			best = f
	if best == null: return
	if best.is_keeper():
		if speed <= 14.0 + best.stat("HAN", 60) * 0.25:
			take(best)
		else:
			b.phys.vel = Vector3(-b.phys.vel.x * 0.3, b.phys.vel.y * 0.5 + 2.0, b.phys.vel.z + g.rng.randf_range(-5.0, 5.0))
			best.no_touch = 0.5
			g.last_touch = best
		return
	var limit := (s.control_speed_base + best.stat("DRI", 60) * s.control_per_dri) * b.touch() * (1.3 if best == g.pass_target else 1.0)
	if speed <= limit:
		take(best)
	else:
		b.phys.vel *= 0.45
		best.no_touch = 0.4
		g.last_touch = best

# ---------------------------------------------------------------- kicks
## The kick animation, then the ball state does the kick (Ball.play_action: Pass / Through / Lob / Shot, numbers in data/ball_actions.csv).
## `over` may replace style / speed / noise. `receiver` is who the pass is meant for (he runs onto it and controls it more easily).
func kick_action(f: Footballer, action: String, to: Vector2, to_vel := Vector2.ZERO, over := {}, receiver: Footballer = null) -> void:
	g.motion.act(f, "kick", 0.35, func(): launch(f, action, to, to_vel, over, receiver))

func launch(f: Footballer, action: String, to: Vector2, to_vel: Vector2, over: Dictionary, receiver: Footballer = null) -> void:
	if g.carrier != f: return
	g.carrier = null
	g.ball.preview_spin = Vector3.ZERO
	g.ball.play_action(action, to, f.row, to_vel, over)
	f.no_touch = g.settings.no_touch_after_kick
	g.last_touch = f
	g.pass_target = receiver

# ---------------------------------------------------------------- tackles
func try_tackle(f: Footballer) -> void:
	var target := g.carrier
	if target == null or target.team == f.team or f.lock > 0.0 or f.no_touch > 0.0: return
	if f.pos.distance_to(target.pos) > 3.0: return
	f.vel = (target.pos - f.pos).normalized() * 6.0
	g.motion.act(f, "df01_stand_tackle", 0.45, func(): resolve_tackle(f, target, 0.0))

func resolve_tackle(f: Footballer, target: Footballer, bonus: float) -> void:
	if g.carrier != target or f.pos.distance_to(target.pos) > 2.4:
		f.lock = maxf(f.lock, 0.4)
		return
	if target.shield > 0.0: return
	var chance := 0.5 + (f.stat("DEF", 60) - target.stat("DRI", 60)) * 0.01 + bonus
	if g.rng.randf() < chance: steal(f, target)
	else: f.lock = maxf(f.lock, 0.6)

func steal(thief: Footballer, victim: Footballer) -> void:
	victim.no_touch = g.settings.lose_ball_pause
	victim.pending = Callable()
	thief.no_touch = 0.0
	take(thief)

## defenders on the carrier win the ball now and then (the human's players too)
func _auto_tackles(dt: float) -> void:
	var c := g.carrier
	if c.shield > 0.0: return
	var s := g.settings
	var other := g.away if c.team == g.home else g.home
	for o in other.players:
		if o.no_touch > 0.0 or o.lock > 0.0 or o.is_keeper(): continue
		if o.pos.distance_to(c.pos) > s.tackle_reach: continue
		var rate := s.tackle_rate * (o.stat("DEF", 60) + 30.0) / (c.stat("DRI", 60) + 30.0) * (1.0 if o.team.human else lerpf(0.6, 1.0, s.ai_level))
		if g.rng.randf() < rate * dt:
			steal(o, c)
			return
