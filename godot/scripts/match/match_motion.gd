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

## where in a clip (0..1) its strike event is
func strike_frac(clip_name: String, fallback := 0.5) -> float:
	var a: Dictionary = Data.anims.get("animations", {}).get(clip_name, {})
	var fr := float(a.get("frames", 0))
	var ev: Dictionary = a.get("events", {})
	if fr > 0.0 and ev.has("strike"): return clampf(float(ev["strike"]) / fr, 0.1, 0.9)
	return fallback

func update(dt: float) -> void:
	var s := g.settings
	var playing := g.phase == MatchGame.Phase.PLAY
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
		if f.lock <= 0.0: f.glide = false
		var want := f.want if (f.lock <= 0.0 and playing and f.aim_done.is_null()) else Vector2.ZERO
		var gliding := (f.glide and f.lock > 0.0) or not f.aim_done.is_null()
		var rate := 0.0 if not f.aim_done.is_null() else s.glide_brake if gliding else (s.accel if want.length() > f.vel.length() - 0.1 else s.brake)
		var before := f.pos
		f.vel = f.vel.move_toward(want, rate * dt)
		f.pos += f.vel * dt
		f.pos.x = clampf(f.pos.x, -MatchGame.HALF_L - 3.0, MatchGame.HALF_L + 3.0)
		f.pos.y = clampf(f.pos.y, -MatchGame.HALF_W - 2.0, MatchGame.HALF_W + 2.0)
		if g.carrier == f: f.carried += before.distance_to(f.pos)
		if f.vel.length() > 0.5 and f.aim_done.is_null() and not gliding:
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
	f.node.set_mirror(f.mirror and (f.lock > 0.0 or not f.aim_done.is_null()))
	f.node.face_vector(g.stadium.screen_dir(f.pos, f.face))          # the picture turns by what the camera sees, not by the pitch angle
	if f.lock > 0.0 or not f.aim_done.is_null(): return
	f.mirror = false
	var speed := f.vel.length()
	var want_clip := "base_idle"
	if speed > 5.8: want_clip = "base_sprint"
	elif speed > 3.2: want_clip = "base_jog"
	elif speed > 0.4: want_clip = "base_walk"
	if want_clip != f.clip and f.node.has_clip(want_clip):
		f.node.play_clip(want_clip)
		f.clip = want_clip
