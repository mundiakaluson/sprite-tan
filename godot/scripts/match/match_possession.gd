class_name MatchPossession
extends RefCounted
## Who has the ball: carrying it at the feet, picking up a loose ball, keeper saves, tackles and the kick itself (through the ball's own states).

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

func take(f: Footballer) -> void:
	if g.offside.touched(f): return                         # he was offside when it was played: free kick given instead
	var prev := g.last_touch
	g.carrier = f
	g.last_touch = f
	g.pass_target = null
	f.hold = 0.0
	f.carried = 0.0
	f.think = g.rng.randf_range(0.2, 0.5)
	f.settle = g.settings.settle_time                       # the ball rolls to his feet (a damped spring, MatchSettings > Ball and first touch)
	f.ball_rel = ((g.ball.phys.vel - Vector3(f.vel.x, 0.0, f.vel.y)) * (1.0 - g.settings.control_cushion)).limit_length(g.settings.settle_max_speed)
	if not f.is_keeper(): f.vel *= 1.0 - g.settings.control_cushion   # the first touch is a trap
	if Vector2(g.ball.phys.pos.x, g.ball.phys.pos.z).distance_to(f.pos) > g.settings.settle_snap:        # a restart / a ball from far away: place it, no flying across the pitch
		var at := f.pos + f.face * g.settings.touch_ahead
		g.ball.phys.pos = Vector3(at.x, g.ball.phys.rad, at.y)
		f.ball_rel = Vector3.ZERO
	g.ball.hold()
	if g.brain != null: g.brain.received(f, prev)              # first touch: scanned players turn / protect it (AiScan)

## every physics frame
func update(dt: float) -> void:
	if g.carrier != null:
		_carry(dt)
		if g.phase == MatchGame.Phase.PLAY:
			g.carrier.hold += dt
			_auto_tackles(dt)
		return
	if g.phase == MatchGame.Phase.PLAY: _loose(dt)

func _carry(dt: float) -> void:
	var s := g.settings
	var c := g.carrier
	var spd := c.vel.length()
	var pulse := s.touch_pulse * clampf(spd / 6.0, 0.0, 1.0) * (0.5 + 0.5 * sin(TAU * c.carried / s.touch_stride))     # a touch every stride: the ball runs ahead, then he catches up
	var spot := c.pos + c.face * (s.touch_ahead + s.touch_speed * spd + pulse)
	var b := g.ball
	var target := Vector3(spot.x, b.phys.rad, spot.y)
	if c.is_keeper():                                                                   # a keeper holds it in his hands, not at his feet
		var hands := c.pos + c.face * g.settings.keeper_hold_ahead
		target = Vector3(hands.x, g.settings.keeper_hold_height, hands.y)
		var tracked := g.motion.clip_ball(c)                                            # during a catch / gesture clip: exactly where the clip has it
		if tracked != Vector3.INF:
			target = tracked
			c.settle = 0.0
	var cv := Vector3(c.vel.x, 0.0, c.vel.y)
	if c.settle > 0.0:
		c.settle -= dt
		var w := s.settle_omega
		c.ball_rel += (-w * w * (b.phys.pos - target) - 2.0 * w * c.ball_rel) * dt         # critically damped: no overshoot, no snap, keeps the pass's momentum
		c.ball_rel = c.ball_rel.limit_length(s.settle_max_speed)
		b.phys.pos += (c.ball_rel + cv) * dt
		b.phys.vel = c.ball_rel + cv
		if c.settle <= 0.0: c.ball_rel = Vector3.ZERO
	else:
		b.phys.pos = target
		b.phys.vel = cv
	b.live = false
	var v3 := Vector3(c.vel.x, 0.0, c.vel.y)
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
		if f.no_touch > 0.0 or (f.is_keeper() and (f.lock > 0.0 or g.keeper.busy(f))): continue
		if g.offside.aware(f): continue                                   # he knows he was offside: he leaves it
		var reach := s.pickup_reach
		var max_h := s.reach_height
		if f.is_keeper():
			reach = s.keeper_ground_reach if bp.y < s.scoop_max_height else s.keeper_reach + f.stat("REF", 60) * s.keeper_ref_reach     # a ball on the grass: he has to get to it
			max_h = s.keeper_reach_height
		if f == g.pass_target: reach *= s.receiver_reach_k
		if bp.y > max_h: continue
		var d := f.pos.distance_to(b2) / reach
		if d < bd:
			bd = d
			best = f
	if best == null: return
	if best.is_keeper():
		if speed <= s.save_speed_base + best.stat("HAN", 60) * s.save_speed_per_han:
			var ground := bp.y < s.scoop_max_height
			take(best)
			if ground and best.node.has_clip(s.clip_keeper_scoop):                # off the grass: he runs in, bends and scoops it up into his hands
				g.motion.act(best, s.clip_keeper_scoop, 1.0, func(): pass, 0.0, s.scoop_time, true)
		else:
			if g.offside.touched(best): return
			b.phys.vel = Vector3(-b.phys.vel.x * 0.3, b.phys.vel.y * 0.5 + 2.0, b.phys.vel.z + g.rng.randf_range(-5.0, 5.0))
			best.no_touch = 0.5
			g.last_touch = best
		return
	var limit := (s.control_speed_base + best.stat("DRI", 60) * s.control_per_dri) * b.touch() * (s.receiver_control_k if best == g.pass_target else 1.0)
	if speed <= limit:
		take(best)
	else:
		if g.offside.touched(best): return
		if speed > s.deflect_speed and best != g.pass_target:                # it hits him and flies off (a block, a deflection)
			var v := Vector2(b.phys.vel.x, b.phys.vel.z).rotated(deg_to_rad(g.rng.randf_range(-s.deflect_deg, s.deflect_deg))) * s.deflect_keep
			b.phys.vel = Vector3(v.x, absf(b.phys.vel.y) * 0.3 + g.rng.randf_range(0.0, s.deflect_up), v.y)
			stat_deflections += 1
		else: b.phys.vel *= s.bounce_off
		best.no_touch = 0.4
		g.last_touch = best

# ---------------------------------------------------------------- kicks
## The kick animation, then the ball state does the kick (Ball.play_action: Pass / Through / Lob / Shot, numbers in data/ball_actions.csv).
## `over` may replace style / speed / noise. `receiver` is who the pass is meant for (he runs onto it and controls it more easily).
func kick_action(f: Footballer, action: String, to: Vector2, to_vel := Vector2.ZERO, over := {}, receiver: Footballer = null) -> void:
	g.kicking.kick(f, action, to, to_vel, over, receiver)

func launch(f: Footballer, action: String, to: Vector2, to_vel: Vector2, over: Dictionary, receiver: Footballer = null) -> void:
	if g.carrier != f: return
	g.carrier = null
	g.ball.preview_spin = Vector3.ZERO
	AiScan.on_kick(f, to)
	g.ball.play_action(action, to, f.row, to_vel, over)
	f.no_touch = g.settings.no_touch_after_kick
	g.last_touch = f
	g.pass_target = receiver
	g.offside.played(f, g.rules.consume(f))                      # who is offside is decided now, as the ball is played

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
	if g.rng.randf() < chance: won_tackle(f, target)
	else: failed_tackle(f, target)

func steal(thief: Footballer, victim: Footballer) -> void:
	victim.no_touch = g.settings.lose_ball_pause
	victim.pending = Callable()
	thief.no_touch = 0.0
	take(thief)

## the ball changes hands at the tackle's strike point; the tackler is back on his feet quickly, the victim goes down (or stumbles)
func won_tackle(thief: Footballer, victim: Footballer) -> void:
	var s := g.settings
	steal(thief, victim)
	thief.lock = minf(thief.lock, 0.15)
	victim.aim_done = Callable()
	var fall: bool = g.rng.randf() < s.tackle_victim_fall or victim.ai.get("engage_fall", false)       # an engagement can put him down (risk roll, a charge)
	victim.ai.erase("engage_fall")
	if fall: g.kicking.tumble(victim, s.clips_fall)
	else: g.kicking.tumble(victim, s.clips_stumble_medium)

## he went in and missed: over-committed and stumbles or falls, and the carrier is knocked about a little
func failed_tackle(tackler: Footballer, carrier: Footballer) -> void:
	var s := g.settings
	if g.rng.randf() < s.tackle_miss_fall: g.kicking.tumble(tackler, s.clips_fall)
	else: g.kicking.tumble(tackler, s.clips_stumble_medium)
	tackler.no_touch = maxf(tackler.no_touch, 0.4)
	if carrier.lock <= 0.0 and g.rng.randf() < s.tackle_miss_carrier_stumble: g.kicking.tumble(carrier, s.clips_stumble_light)

## a defender goes in on the carrier: plays the tackle clip, and at its strike frame it is won or lost
var stat_tackles := 0
var stat_deflections := 0
var stat_tackles_won := 0

## force: an engagement decided it, so it lands even if he is a little out of reach
func start_tackle(f: Footballer, target: Footballer, won: bool, force := false) -> void:
	stat_tackles += 1
	if won: stat_tackles_won += 1
	var s := g.settings
	var list := PackedStringArray()
	for c in s.clips_tackle:
		if f.node.has_clip(c): list.append(c)
	var clip: String = "" if list.is_empty() else list[g.rng.randi() % list.size()]
	f.vel = (target.pos - f.pos).normalized() * 5.0
	f.face = (target.pos - f.pos).normalized()
	g.motion.act(f, clip, g.motion.strike_frac(clip, 0.45), func(): _tackle_lands(f, target, won, force), 1.0, s.tackle_clip_time, true)

func _tackle_lands(f: Footballer, target: Footballer, won: bool, force := false) -> void:
	if g.carrier != target or (not force and f.pos.distance_to(target.pos) > 2.4): return
	if won: won_tackle(f, target)
	else: failed_tackle(f, target)

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
			start_tackle(o, c, true)
			return
		if g.rng.randf() < s.tackle_miss_rate * dt:
			start_tackle(o, c, false)
			return
