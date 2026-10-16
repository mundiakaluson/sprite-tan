class_name MatchKicking
extends RefCounted
## A kick is not instant: the player first PIVOTS to face where the ball is going (a pass back means he turns round with the ball at his feet), then plays the kick clip,
## and at the strike frame the ball goes. Under pressure, or with a poor pass, the kick can be scuffed (more error on the ball) and he stumbles or falls after it.
## All numbers: MatchSettings > Kick turn and stumble.

var g: MatchGame
var _tumble_chain := {}      ## Footballer -> clip to play after a fall
var stat_passes := 0         ## counters for the headless balance runs
var stat_scuffs := 0
var stat_tumbles := 0

func _init(game: MatchGame) -> void:
	g = game

func busy(f: Footballer) -> bool:
	return not f.aim_done.is_null()

## the entry point (MatchPossession.kick_action calls this)
func kick(f: Footballer, action: String, to: Vector2, to_vel: Vector2, over: Dictionary, receiver: Footballer) -> void:
	if g.carrier != f or f.lock > 0.0 or busy(f): return
	var s := g.settings
	var dir := to - f.pos
	if dir.length() > 0.1 and absf(f.face.angle_to(dir)) > deg_to_rad(s.pivot_min_deg):
		f.aim = dir.normalized()
		f.aim_t = 0.0
		f.settle = maxf(f.settle, 0.3)                                   # the ball stays with him as he turns
		f.aim_done = func(): _strike(f, action, to, to_vel, over, receiver)
		_turn_clip(f)
		return
	_strike(f, action, to, to_vel, over, receiver)

func _strike(f: Footballer, action: String, to: Vector2, to_vel: Vector2, over_in: Dictionary, receiver: Footballer) -> void:
	f.aim_done = Callable()
	f.mirror = false
	if g.carrier != f: return
	if receiver != null: to = receiver.pos                                  # he may have moved while we turned
	var dir := to - f.pos
	var speed := f.vel.length()
	var over := over_in.duplicate()
	if dir.length() > 0.1:
		over["_mis"] = clampf(absf(f.face.angle_to(dir)) / deg_to_rad(90.0), 0.0, 1.0)      # how far round he still was: kicking before turning is less accurate
		f.face = dir.normalized()                                              # a small turn at most (bigger ones were pivots), so he kicks where the ball goes
		f.settle = maxf(f.settle, 0.15)
	var clip := pick_clip(f, action, to)
	var dur := g.settings.shot_clip_time if action == "shot" else g.settings.kick_clip_time
	g.motion.act(f, clip, g.motion.strike_frac(clip, 0.5), func(): _release(f, action, to, to_vel, over, receiver), 1.0, dur, speed > 1.0)

## the kick clip for this action: by distance, direction behind him, and kind of pass; one at random from the list
func pick_clip(f: Footballer, action: String, to: Vector2) -> String:
	var s := g.settings
	var d := f.pos.distance_to(to)
	var back := absf(f.face.angle_to(to - f.pos)) > deg_to_rad(s.pass_back_deg)
	var list: PackedStringArray
	match action:
		"shot": list = s.clips_shot_far if d > s.shot_far_m else s.clips_shot_close
		"through": list = s.clips_pass_through
		"lob": list = s.clips_pass_lob
		_:
			if back: list = s.clips_pass_back
			elif d < s.pass_short_m: list = s.clips_pass_short
			elif d > s.pass_long_m: list = s.clips_pass_long
			else: list = s.clips_pass_medium
	var ok := PackedStringArray()
	for c in list:
		if f.node.has_clip(c): ok.append(c)
	if ok.is_empty(): return "ps03_driven_pass" if f.node.has_clip("ps03_driven_pass") else ""
	return ok[g.rng.randi() % ok.size()]

## the turn animation: a skilled player turns sharp, a heavy one plants and steps round
func _turn_clip(f: Footballer) -> void:
	var s := g.settings
	var dri := f.stat("DRI", 60)
	var list := s.clips_turn_skilled if dri >= s.skilled_dri else (s.clips_turn_heavy if dri < s.heavy_dri else s.clips_turn_normal)
	var ok := PackedStringArray()
	for c in list:
		if f.node.has_clip(c): ok.append(c)
	if ok.is_empty(): return
	var clip := ok[g.rng.randi() % ok.size()]
	var turn := f.face.angle_to(f.aim)
	var agi := lerpf(s.agility_min, s.agility_max, clampf((dri - 40) / 50.0, 0.0, 1.0))
	var rate := deg_to_rad(s.pivot_deg_per_s) * agi / (1.0 + f.vel.length() * 0.5 * s.pivot_speed_drag)
	g.motion._time(f, clip, clampf(absf(turn) / rate, 0.25, s.pivot_max))     # the clip lasts as long as the turn does
	f.node.play_clip(clip)
	f.clip = clip
	f.mirror = turn < 0.0                                                # the turn clips turn to his right; a left turn plays mirrored

func update(dt: float) -> void:
	var s := g.settings
	for f in g.all:
		if not f.aim_done.is_null():
			if g.carrier != f or g.phase != MatchGame.Phase.PLAY:
				f.aim_done = Callable()
				f.mirror = false
			else:
				f.aim_t += dt
				var a := f.face.angle_to(f.aim)
				var agi := lerpf(s.agility_min, s.agility_max, clampf((f.stat("DRI", 60) - 40) / 50.0, 0.0, 1.0))
				var step := deg_to_rad(s.pivot_deg_per_s) * agi / (1.0 + f.vel.length() * s.pivot_speed_drag) * dt
				f.face = f.face.rotated(clampf(a, -step, step))
				if f.vel.length() > 0.1:                                    # the run bends round with the turn and bleeds off speed
					var sp := maxf(f.vel.length() - s.pivot_brake * dt, minf(f.vel.length(), s.pivot_min_speed))
					f.vel = f.vel.rotated(clampf(f.vel.angle_to(f.aim), -step, step)).normalized() * sp
				if absf(f.face.angle_to(f.aim)) < deg_to_rad(s.pivot_done_deg) or f.aim_t > s.pivot_max:
					var cb := f.aim_done
					f.aim_done = Callable()
					cb.call()
		if _tumble_chain.has(f) and f.lock <= 0.0:
			var clip: String = _tumble_chain[f]
			_tumble_chain.erase(f)
			_play(f, clip)

# ---------------------------------------------------------------- the strike, and what it costs
func _release(f: Footballer, action: String, to: Vector2, to_vel: Vector2, over: Dictionary, receiver: Footballer) -> void:
	if g.carrier != f: return
	var s := g.settings
	var passing := action in ["pass", "through", "lob"]
	var press := _pressure(f)                                               # 0 = free, 1 = an opponent on him
	var bad := false
	var o := over.duplicate()
	if passing:
		var misaligned := float(o.get("_mis", 0.0))
		o.erase("_mis")
		var chance := s.scuff_base + (60 - f.stat("PAS", 60)) * s.scuff_per_pas + press * s.scuff_pressure + misaligned * s.scuff_misaligned
		bad = g.rng.randf() < chance
		stat_passes += 1
		if bad:
			stat_scuffs += 1
			o["noise"] = maxf(float(o.get("noise", 0.0)), s.scuff_noise)
			g.hud.toast("%s: scuffed" % f.display_name())
	g.poss.launch(f, action, to, to_vel, o, receiver)
	if g.carrier == f: return                                               # the ball was not released
	if not passing: return
	var fall := bad and press > 0.0 and g.rng.randf() < s.fall_chance * (0.5 + press)
	if fall: tumble(f, s.clips_fall)
	elif bad: tumble(f, s.clips_stumble_medium)
	elif press > 0.0 and g.rng.randf() < s.stumble_pressed * press: tumble(f, s.clips_stumble_light)

## 0..1: how close the nearest opponent is (1 = at his shoulder, 0 = further than kick_pressure_radius)
func _pressure(f: Footballer) -> float:
	var s := g.settings
	var best := s.kick_pressure_radius
	for o in g.all:
		if o.team == f.team or o.is_keeper(): continue
		best = minf(best, o.pos.distance_to(f.pos))
	return 1.0 - best / s.kick_pressure_radius

func tumble(f: Footballer, list: PackedStringArray) -> void:
	stat_tumbles += 1
	if list.is_empty(): return
	var clip := list[g.rng.randi() % list.size()]
	if not f.node.has_clip(clip): return
	f.vel = f.face * g.settings.stumble_drift
	_play(f, clip)
	if clip.begins_with("base_fall") and f.node.has_clip("base_get_up"): _tumble_chain[f] = "base_get_up"

func _play(f: Footballer, clip: String) -> void:
	f.node.play_clip(clip)
	f.clip = clip
	f.lock = minf(f.node.anim_player.get_animation(clip).length, 2.0)
