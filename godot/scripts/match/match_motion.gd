class_name MatchMotion
extends RefCounted
## Moves the footballers (acceleration, turning, keeping apart) and shows them: the Player node gets its pitch position, facing and run / walk / idle clip.

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

## play a clip and run `strike` when it reaches its contact point; the player is committed meanwhile
var _stretched := {}      ## clip -> true while its tree node plays in a custom time

## plays a clip as a committed action; `strike` runs at `strike_frac` of it. `keep` = fraction of speed kept (kicks on the run keep it all, with glide),
## `duration` > 0 plays the whole clip in that many seconds (the authored kick clips are ~1.5 s)
func act(f: Footballer, clip_name: String, strike_frac: float, strike: Callable, keep := 0.3, duration := 0.0, glide := false) -> void:
	var length := 0.0
	if f.node.has_clip(clip_name):
		length = f.node.anim_player.get_animation(clip_name).length
		_time(f, clip_name, duration)
		if duration > 0.0: length = duration
		f.node.play_clip(clip_name)
		f.clip = clip_name
	elif duration > 0.0: length = duration                                  # clip not baked yet: the timing still holds
	f.lock = minf(length, 1.1)
	f.pending = strike
	f.pending_t = length * strike_frac
	f.vel *= keep
	f.glide = glide

## sets how long the clip's node in the animation tree takes (0 = its own length)
func _time(f: Footballer, clip_name: String, duration: float) -> void:
	var tree := f.node.anim_tree.tree_root as AnimationNodeStateMachine
	if tree == null or not tree.has_node(StringName(clip_name)): return
	var n := tree.get_node(StringName(clip_name)) as AnimationNodeAnimation
	if n == null: return
	if duration > 0.0:
		n.use_custom_timeline = true
		n.timeline_length = duration
		n.stretch_time_scale = true
		_stretched[clip_name] = true
	elif _stretched.has(clip_name):
		n.use_custom_timeline = false
		_stretched.erase(clip_name)

## the clip's own ball position for the frame he is on (exported per frame with the clip: side, forward, up in rig units), turned into pitch metres;
## Vector3.INF when the clip has no ball track or the ball is not in it on this frame. Used to keep the real ball in a keeper's hands through a catch or a gesture.
func clip_ball(f: Footballer) -> Vector3:
	var a: Dictionary = Data.anims.get("animations", {}).get(f.clip, {})
	var tr: Array = a.get("ball", [])
	if tr.is_empty() or f.node == null or f.node.sprite == null: return Vector3.INF
	var i := clampi(f.node.sprite.frame_index, 0, tr.size() - 1)
	var e: Array = tr[i]
	if e.size() < 4 or int(e[3]) == 0: return Vector3.INF
	var u := g.settings.rig_unit_m
	var right := Vector2(-f.face.y, f.face.x) * (-1.0 if f.mirror else 1.0)
	var p := f.pos + f.face * float(e[1]) * u + right * float(e[0]) * u
	return Vector3(p.x, maxf(float(e[2]) * u, g.ball.phys.rad), p.y)

## where in a clip (0..1) its strike event is
func strike_frac(clip_name: String, fallback := 0.5) -> float:
	var a: Dictionary = Data.anims.get("animations", {}).get(clip_name, {})
	var fr := float(a.get("frames", 0))
	var ev: Dictionary = a.get("events", {})
	if fr > 0.0 and ev.has("strike"): return clampf(float(ev["strike"]) / fr, 0.1, 0.9)
	return fallback

func update(dt: float) -> void:
	var s := g.settings
	var playing := g.phase == MatchGame.Phase.PLAY or g.phase == MatchGame.Phase.RESTART
	for f in g.all:
		f.no_touch = maxf(0.0, f.no_touch - dt)
		f.lock = maxf(0.0, f.lock - dt)
		f.shield = maxf(0.0, f.shield - dt)
		if not f.pending.is_null():
			f.pending_t -= dt
			if f.pending_t <= 0.0:
				var cb := f.pending
				f.pending = Callable()
				cb.call()
		if f.lock <= 0.0:
			f.glide = false
			f.glide_k = 1.0
		var want := f.want if (f.lock <= 0.0 and playing and f.aim_done.is_null()) else Vector2.ZERO
		var gliding := (f.glide and f.lock > 0.0) or not f.aim_done.is_null()
		var rate := 0.0 if not f.aim_done.is_null() else s.glide_brake * f.glide_k if gliding else (s.accel if want.length() > f.vel.length() - 0.1 else s.brake)
		var before := f.pos
		f.vel = f.vel.move_toward(want, rate * dt)
		f.pos += f.vel * dt
		f.pos.x = clampf(f.pos.x, -MatchGame.HALF_L - 3.0, MatchGame.HALF_L + 3.0)
		f.pos.y = clampf(f.pos.y, -MatchGame.HALF_W - 2.0, MatchGame.HALF_W + 2.0)
		if g.carrier == f: f.carried += before.distance_to(f.pos)
		var raw := f.top_speed(false)
		var sp := f.vel.length()
		if playing:
			if sp > s.sprint_clip_frac * raw: f.stamina -= s.sprint_drain * maxf(0.3, 1.3 - f.stat("PHY", 60) / 100.0 * s.phy_k) * dt
			elif sp > 0.45 * raw: f.stamina += s.jog_regen * dt
			else: f.stamina += s.rest_regen * dt
			f.stamina = clampf(f.stamina, 0.0, 1.0)
		var tb := Vector2(g.ball.phys.pos.x, g.ball.phys.pos.z) - f.pos
		if f.is_keeper() and f.lock <= 0.0 and f.aim_done.is_null() and not gliding and not f.ai.get("rush", false) and tb.length() > 1.0:   # eyes on the ball, always (but not when he charges out)
			var kstep := deg_to_rad(s.keeper_turn_deg_per_s) * dt                  # a keeper keeps his chest to the ball while he shuffles across
			f.face = f.face.rotated(clampf(f.face.angle_to(tb), -kstep, kstep)).normalized()
		elif f.ai.has("look") and float(f.ai.get("look_until", -1.0)) > g.clock and f.vel.length() < s.look_max_speed and f.aim_done.is_null() and not gliding and f.lock <= 0.0:
			var lstep := deg_to_rad(s.turn_deg_per_s) * dt                    # a glance over the shoulder / opening up for a pass
			f.face = f.face.rotated(clampf(f.face.angle_to(f.ai["look"]), -lstep, lstep)).normalized()
		elif f.vel.length() > 0.5 and f.aim_done.is_null() and not gliding:
			var step := deg_to_rad(s.turn_deg_per_s) * dt                      # turns by an angle, so a U-turn can not collapse the vector
			f.face = f.face.rotated(clampf(f.face.angle_to(f.vel), -step, step)).normalized()
		f.want = Vector2.ZERO
	for i in g.all.size():
		for j in range(i + 1, g.all.size()):
			var d := g.all[j].pos - g.all[i].pos
			var l := d.length()
			if l < s.separation and l > 0.001:
				var push := d / l * (s.separation - l) * 0.5
				g.all[i].pos -= push
				g.all[j].pos += push
	for f in g.all: _show(f)

func _show(f: Footballer) -> void:
	g.stadium.set_actor_pos(f.node, g.stadium.pitch_pos(Vector3(f.pos.x, 0.0, f.pos.y)))
	var busy := f.lock > 0.0 or not f.aim_done.is_null()
	var shuffle_left := false
	var want_clip := "base_idle"
	if not busy:
		var speed := f.vel.length()
		var raw := f.top_speed(false)
		if speed > 3.2 and f.stamina < g.settings.tired_clip_below: want_clip = "base_tired_run"
		elif speed > g.settings.sprint_clip_frac * raw and speed > 4.0: want_clip = "base_sprint"
		elif speed > 3.2: want_clip = "base_jog"
		elif speed > 0.4: want_clip = "base_walk"
		if speed < 0.5 and f.ai.get("air_wait", false) and f.node.has_clip(g.settings.clip_wait_air): want_clip = g.settings.clip_wait_air      # waiting under a high ball, eyes up
		var st := g.settings
		if speed < st.stance_clip_speed:                                            # the AI layer's stances (sprites/moves_ai.py)
			if g.carrier == f and f.ai.get("shielding", false) and f.node.has_clip(st.clip_shield): want_clip = st.clip_shield
			elif float(f.ai.get("jockey_until", -1.0)) > g.clock and f.node.has_clip(st.clip_jockey): want_clip = st.clip_jockey
			elif speed < 0.6 and f.ai.get("wall", false) and g.rules.kind == "free_kick" and f.node.has_clip(st.clip_wall): want_clip = st.clip_wall
		if f.is_keeper():
			var k := _keeper_clip(f, speed)
			if k != "" and f.node.has_clip(k):
				want_clip = k
				if k == g.settings.clip_keeper_shuffle: shuffle_left = f.vel.dot(Vector2(-f.face.y, f.face.x)) < 0.0     # the clip shuffles to his right
	f.node.set_mirror((f.mirror and busy) or shuffle_left)
	f.node.face_vector(g.stadium.screen_dir(f.pos, f.face))          # the picture turns by what the camera sees, not by the pitch angle
	if busy: return
	f.mirror = false
	if want_clip != f.clip and f.node.has_clip(want_clip):
		f.node.play_clip(want_clip)
		f.clip = want_clip

## the keeper's own clips: sidesteps with his chest to the ball, and a stance that follows the danger (relaxed / alert / set for a shot)
func _keeper_clip(f: Footballer, speed: float) -> String:
	var s := g.settings
	var ball := Vector2(g.ball.phys.pos.x, g.ball.phys.pos.z)
	if speed > 0.4:
		if speed < s.keeper_watch_speed or not f.ai.get("rush", false):
			var cross := absf(f.vel.dot(Vector2(-f.face.y, f.face.x)))
			if cross > s.keeper_shuffle_lateral * speed: return s.clip_keeper_shuffle
		return ""
	var dist := absf(ball.x - (-MatchGame.HALF_L * f.team.dir))
	var danger := g.carrier == null or g.carrier.team != f.team
	if g.rules.kind == "penalty" and g.rules.team != f.team and f.node.has_clip(s.clip_keeper_penalty): return s.clip_keeper_penalty     # on his line, arms out, swaying
	if f.ai.get("set", false): return s.clip_keeper_set                  # his scan says a shot is coming: set, low, on his toes
	if danger and dist < s.keeper_set_dist: return s.clip_keeper_set
	if danger and dist < s.keeper_alert_dist: return s.clip_keeper_idle
	return "base_idle"
