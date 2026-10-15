class_name MatchMotion
extends RefCounted
## Moves the footballers (acceleration, turning, keeping apart) and shows them: the Player node gets its pitch position, facing and run / walk / idle clip.

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

## play a clip and run `strike` when it reaches its contact point; the player is committed meanwhile
func act(f: Footballer, clip_name: String, strike_frac: float, strike: Callable) -> void:
	var length := 0.0
	if f.node.has_clip(clip_name):
		length = f.node.anim_player.get_animation(clip_name).length
		f.node.play_clip(clip_name)
		f.clip = clip_name
	f.lock = minf(length, 1.1)
	f.pending = strike
	f.pending_t = length * strike_frac
	f.vel *= 0.3

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
		var want := f.want if (f.lock <= 0.0 and playing) else Vector2.ZERO
		var rate := s.accel if want.length() > f.vel.length() - 0.1 else s.brake
		var before := f.pos
		f.vel = f.vel.move_toward(want, rate * dt)
		f.pos += f.vel * dt
		f.pos.x = clampf(f.pos.x, -MatchGame.HALF_L - 3.0, MatchGame.HALF_L + 3.0)
		f.pos.y = clampf(f.pos.y, -MatchGame.HALF_W - 2.0, MatchGame.HALF_W + 2.0)
		if g.carrier == f: f.carried += before.distance_to(f.pos)
		if f.vel.length() > 0.5:
			f.face = f.face.lerp(f.vel.normalized(), clampf(dt * s.turn_rate, 0.0, 1.0)).normalized()
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
	f.node.face_vector(f.face)
	if f.lock > 0.0: return
	var speed := f.vel.length()
	var want_clip := "base_idle"
	if speed > 5.8: want_clip = "base_sprint"
	elif speed > 3.2: want_clip = "base_jog"
	elif speed > 0.4: want_clip = "base_walk"
	if want_clip != f.clip and f.node.has_clip(want_clip):
		f.node.play_clip(want_clip)
		f.clip = want_clip
