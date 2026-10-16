class_name MatchDribble
extends RefCounted
## Taking a man on and the defender's answer: the carrier fakes one way and bursts the other; a defender who bites lunges / slides / stumbles the faked way and is out of play for a moment,
## one who reads it gets a tackle at the carrier. Also the slide tackle. Numbers: MatchSettings > Take-on and slide tackles. AI behaviours that start them: scripts/ai/behaviours/ai_takeon.gd, ai_tackle.gd.

var g: MatchGame
var _moves := {}        ## Footballer -> {def, fake, cut, t, bit}
var stat_takeons := 0
var stat_bitten := 0
var stat_slides := 0
var stat_slide_wins := 0

func _init(game: MatchGame) -> void:
	g = game

func busy(f: Footballer) -> bool:
	return _moves.has(f)

# ---------------------------------------------------------------- take-on
func take_on(f: Footballer, d: Footballer) -> bool:
	if d == null or g.carrier != f or f.lock > 0.0 or busy(f) or not f.aim_done.is_null(): return false
	var s := g.settings
	var dir := d.pos - f.pos
	if dir.length() < 0.2: dir = f.face
	dir = dir.normalized()
	var perp := Vector2(-dir.y, dir.x)
	var side := 1.0 if g.rng.randf() < 0.5 else -1.0
	if absf(f.pos.y + perp.y * side * 4.0) > MatchGame.HALF_W - 2.0: side = -side            # not towards the touchline
	var fake := (dir * 0.4 + perp * side).normalized()                                          # shows the shoulder one way ...
	var cut := (dir * 0.85 - perp * side).normalized()                                          # ... and goes the other, past him
	var skilled := g.rng.randf() < clampf((f.stat("DRI", 60) - 60) / 40.0, 0.0, s.skill_max)
	var clip := _pick(f, s.clips_takeon_skill if skilled else s.clips_takeon)
	if clip == "": clip = _pick(f, s.clips_takeon)
	var total := s.takeon_fake_time + s.takeon_burst_time
	g.motion.act(f, clip, 1.0, func(): pass, 1.0, total, true)
	var bite := s.takeon_bite_base + (f.stat("DRI", 60) - d.stat("DEF", 60)) * s.takeon_bite_per_stat
	if d.pos.distance_to(Vector2(-MatchGame.HALF_L * d.team.dir, 0.0)) < s.takeon_box_dist: bite -= s.takeon_box_read      # in his own box he stays on his feet
	bite = clampf(bite, 0.1, 0.9)
	_moves[f] = {"def": d, "fake": fake, "cut": cut, "t": 0.0, "bit": g.rng.randf() < bite, "reacted": false}
	stat_takeons += 1
	return true

func update(dt: float) -> void:
	var s := g.settings
	for key in _moves.keys():
		var f: Footballer = key
		var m: Dictionary = _moves[f]
		if g.carrier != f or g.phase != MatchGame.Phase.PLAY:
			_moves.erase(f)
			continue
		m["t"] += dt
		var d: Footballer = m["def"]
		var fake_t := s.takeon_fake_time
		var top := f.top_speed()
		var want: Vector2
		if m["t"] < fake_t:
			want = m["fake"] * top * s.takeon_fake_speed
			if m["bit"] and not m["reacted"] and m["t"] > fake_t * 0.5:                        # he commits to the faked side
				m["reacted"] = true
				_bite(d, m["fake"])
		else:
			want = m["cut"] * top * s.takeon_burst_speed
			if not m["reacted"]:
				m["reacted"] = true
				if d.lock <= 0.0 and d.no_touch <= 0.0 and d.pos.distance_to(f.pos) < s.takeon_read_reach:      # he read it: a tackle goes in
					g.poss.start_tackle(d, f, g.rng.randf() < s.takeon_read_win)
			if m["bit"]: f.shield = maxf(f.shield, s.takeon_shield)                          # nobody gets near him through the gap he made
		f.vel = f.vel.lerp(want, clampf(dt * s.takeon_turn_rate, 0.0, 1.0))
		var step := deg_to_rad(s.turn_deg_per_s) * dt * 1.5
		if f.vel.length() > 0.5: f.face = f.face.rotated(clampf(f.face.angle_to(f.vel), -step, step)).normalized()
		if m["t"] >= fake_t + s.takeon_burst_time: _moves.erase(f)

func _bite(d: Footballer, fake: Vector2) -> void:
	var s := g.settings
	if d.is_keeper() or d.lock > 0.0: return
	stat_bitten += 1
	d.pending = Callable()
	d.aim_done = Callable()
	d.face = fake
	d.no_touch = s.takeon_recover
	if g.rng.randf() < s.takeon_bite_slide:                                                      # he lunges into the faked way
		d.vel = fake * s.slide_speed * 0.8
		var clip := _pick(d, s.clips_slide)
		g.motion.act(d, clip, 1.0, func(): pass, 1.0, s.slide_clip_time, true)
	else:
		g.kicking.tumble(d, s.clips_stumble_medium)                                              # wrong-footed

# ---------------------------------------------------------------- slide tackle
func slide_tackle(d: Footballer, c: Footballer) -> bool:
	if c == null or g.carrier != c or d.lock > 0.0 or d.no_touch > 0.0 or busy(d) or d.is_keeper(): return false
	var s := g.settings
	var lead := c.pos + c.vel * s.slide_lead
	var dir := lead - d.pos
	if dir.length() < 0.2: return false
	dir = dir.normalized()
	d.face = dir
	d.vel = dir * s.slide_speed
	var clip := _pick(d, s.clips_slide)
	stat_slides += 1
	g.motion.act(d, clip, g.motion.strike_frac(clip, 0.45), func(): _slide_lands(d, c), 1.0, s.slide_clip_time, true)
	return true

func _slide_lands(d: Footballer, c: Footballer) -> void:
	var s := g.settings
	if g.carrier != c: return
	if d.pos.distance_to(c.pos) > s.slide_reach or c.shield > 0.0:
		g.poss.failed_tackle(d, c)                                                               # over-slid, he is past him
		return
	var p := clampf(s.slide_win_base + (d.stat("DEF", 60) - c.stat("DRI", 60)) * s.slide_per_stat, 0.1, 0.9)
	if g.rng.randf() < p:
		stat_slide_wins += 1
		var l := d.lock
		g.poss.won_tackle(d, c)
		d.lock = maxf(d.lock, minf(l, 0.35))                                                     # he finishes the slide
	else:
		g.poss.failed_tackle(d, c)

func _pick(f: Footballer, list: PackedStringArray) -> String:
	var ok := PackedStringArray()
	for c in list:
		if f.node.has_clip(c): ok.append(c)
	if ok.is_empty(): return ""
	return ok[g.rng.randi() % ok.size()]
