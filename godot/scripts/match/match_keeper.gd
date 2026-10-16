class_name MatchKeeper
extends RefCounted
## Goalkeeper saves with animation. When a shot is heading for the keeper's goal and he can reach it, he plays one of the keeper clips (gk02 reach dive, gk09 low dive, gk10 high palm,
## gk24 fingertip ...) instead of the ball snapping into his hands: he slides / dives to where the ball will cross him, arriving at the clip's `strike` frame, and at that frame the save is
## resolved (catch, palm / fingertip deflection, parry, or a miss if the ball is out of reach). Left dives mirror the clip (the clips are authored for dives to the keeper's right).
## Which clips he uses for which kind of ball is in MatchSettings > Goalkeeper saves (lists, he picks one at random: add more variants there). Every number lives there too.

## for tests and the HUD: a dive started ("start"), or how it ended ("catch", "deflect", "miss")
signal save_event(keeper: Footballer, kind: String, clip: String, outcome: String)

var g: MatchGame
var _dives := {}            ## Footballer -> {from, to, t, T}

func _init(game: MatchGame) -> void:
	g = game

func busy(f: Footballer) -> bool:
	return _dives.has(f)

func update(dt: float) -> void:
	for f in _dives.keys():
		var d: Dictionary = _dives[f]
		d["t"] = float(d["t"]) + dt
		var u := clampf(float(d["t"]) / float(d["T"]), 0.0, 1.0)
		f.pos = (d["from"] as Vector2).lerp(d["to"], 1.0 - (1.0 - u) * (1.0 - u))     # fast off the mark, easing into the reach
		f.vel = Vector2.ZERO
		# the contact is not at a fixed frame: from a little before the clip's strike frame until a little after it, the save happens the moment the ball is in reach
		if not d["done"] and float(d["t"]) >= float(d["strike"]) - g.settings.save_window_before:
			if _in_reach(f, d["kind"]):
				d["done"] = true
				_resolve(f, d["kind"], d["lateral"], true, d.get("plan", ""))
			elif float(d["t"]) >= float(d["strike"]) + g.settings.save_window_after or _passed(f):
				d["done"] = true
				_resolve(f, d["kind"], d["lateral"], false, d.get("plan", ""))
		if f.lock <= 0.0:
			_dives.erase(f)
	if g.phase != MatchGame.Phase.PLAY or g.carrier != null: return
	for k in g.all:
		if k.is_keeper() and k.lock <= 0.0 and not _dives.has(k): _consider(k)

## how far from where he ends up a ball can still be touched (arms / gloves)
func _reach(k: Footballer) -> float:
	var s := g.settings
	return s.save_reach + k.stat("REF", 60) * s.keeper_ref_reach

## how far sideways he can get in the time the clip takes to reach the ball: a corner shot beats him
func _cover(k: Footballer, seconds: float) -> float:
	var s := g.settings
	return (s.dive_speed + k.stat("REF", 60) * s.dive_speed_per_ref) * seconds

func _in_reach(k: Footballer, _kind: String) -> bool:
	var bp := g.ball.phys.pos
	var s := g.settings
	return absf(bp.x - k.pos.x) < s.save_depth and absf(bp.z - k.pos.y) < _reach(k) and bp.y < s.keeper_reach_height + s.jump_height

## the ball went past him (behind his x) without coming into reach
func _passed(k: Footballer) -> bool:
	return (g.ball.phys.pos.x - k.pos.x) * k.team.dir < -g.settings.save_depth

# ---------------------------------------------------------------- is a save needed
func _consider(k: Footballer) -> void:
	var s := g.settings
	var bp := g.ball.phys.pos
	var v := g.ball.phys.vel
	if v.length() < s.save_threat_speed or v.x * k.team.dir >= 0.0: return          # slow, or not heading for his goal
	if g.last_touch == null or g.last_touch.team == k.team: return                   # a pass or clearance of his own side is no shot
	var t := (k.pos.x - bp.x) / v.x
	if t <= 0.0 or t > s.save_max_time: return
	var z := bp.z + v.z * t                                                           # the straight-line guess
	var h := maxf(bp.y + v.y * t - 0.5 * 9.81 * t * t, 0.12)
	var real := _future(t)                                                            # where the bend / dip / skip really takes it
	var read := clampf(s.read_base + (k.stat("REF", 60) - 60) * s.read_per_ref, 0.0, 1.0)
	z = lerpf(z, real.z, read)                                                        # a good keeper reads the curve, a poor one dives at the line it started on
	h = maxf(lerpf(h, real.y, read), 0.12)
	if absf(z) > MatchGame.GOAL_HALF + 0.6: return                                    # wide of the post: no save to make
	var lateral := z - k.pos.y
	if absf(lateral) > s.dive_range or h > s.keeper_reach_height + s.jump_height: return
	var kind := _kind(lateral, h, v.length())
	var plan := _plan(k, kind, lateral, v.length())                                   # decided now, so the clip shows it: catch / parry / beaten
	var clip := _pick_for(kind, plan)
	if clip == "" or not k.node.has_clip(clip): clip = _pick(kind)
	if clip == "" or not k.node.has_clip(clip): return
	var anim := k.node.anim_player.get_animation(clip)
	var ts := _strike_time(anim)
	if t > ts + s.save_reaction: return                                               # too early: wait until the clip would arrive with the ball
	save_event.emit(k, kind, clip, "start")
	_start(k, clip, kind, anim.length, ts, lateral, z, h, plan)

## the ball's real position t seconds ahead (a copy of its physics stepped forward)
func _future(t: float) -> Vector3:
	var src := g.ball.phys
	var p := BallPhysics.new()
	for key in ["g", "rad", "drag", "mag", "knu", "knu_v", "crisis", "crisis_v", "e", "mu", "roll", "sdec", "power", "touch", "mass", "pos", "vel", "spin", "t", "seed_value"]:
		p.set(key, src.get(key))
	var dt := 1.0 / 60.0
	var left := t
	while left > 0.0:
		p.step(minf(dt, left))
		left -= dt
	return p.pos

func _kind(lateral: float, h: float, speed: float) -> String:
	var s := g.settings
	if h > s.high_ball:
		return "claim" if speed < s.claim_speed else "palm"
	if absf(lateral) < s.stand_range and h < s.high_ball and speed < s.catch_speed: return "catch"
	if h < s.low_ball: return "low"
	if absf(lateral) > s.far_range: return "far"
	return "mid"

func _pick(kind: String) -> String:
	var list: PackedStringArray
	var s := g.settings
	match kind:
		"catch": list = s.clips_catch
		"claim": list = s.clips_claim
		"palm": list = s.clips_palm
		"low": list = s.clips_low
		"far": list = s.clips_far
		_: list = s.clips_mid
	if list.is_empty(): return ""
	return list[g.rng.randi() % list.size()]

## seconds into the clip where its `strike` method key fires (the hand contact); a fraction of the length if the clip has none
func _strike_time(anim: Animation) -> float:
	for i in anim.get_track_count():
		if anim.track_get_type(i) != Animation.TYPE_METHOD: continue
		for j in anim.track_get_key_count(i):
			var args: Array = anim.method_track_get_params(i, j)
			if args.size() > 0 and String(args[0]) == "strike": return anim.track_get_key_time(i, j)
	return anim.length * 0.3

# ---------------------------------------------------------------- the dive
func _start(k: Footballer, clip: String, kind: String, length: float, ts: float, lateral: float, z: float, h: float, plan := "parry") -> void:
	var s := g.settings
	var bp := g.ball.phys.pos
	var to_ball := Vector2(bp.x - k.pos.x, bp.z - k.pos.y)
	var face := to_ball.normalized() if to_ball.length() > 0.1 else Vector2(-k.team.dir, 0.0)
	var right := Vector2(-face.y, face.x)                                             # his right on the screen
	k.face = face
	k.mirror = absf(lateral) > 0.5 and Vector2(0.0, signf(lateral)).dot(right) < 0.0     # clips dive to his right; a left dive is the mirrored clip
	# his body stops an arm's length short of the ball so the HAND meets it (a parry off the glove, not off the chest); a catch takes it in front of the body
	var hand := (s.catch_hand_offset if plan == "catch" else s.hand_offset) if kind in ["low", "mid", "far"] else 0.0
	var body_z := signf(lateral) * maxf(absf(lateral) - hand, 0.0)
	var reach_z := clampf(body_z, -_cover(k, ts), _cover(k, ts)) * (1.0 if kind in ["low", "mid", "far"] else s.stand_travel)
	var to := Vector2(k.pos.x + k.team.dir * s.dive_forward, k.pos.y + reach_z)
	g.motion.act(k, clip, 1.0, func(): pass)
	k.lock = length + s.save_window_after
	_dives[k] = {"from": k.pos, "to": to, "t": 0.0, "T": maxf(ts, 0.1), "strike": ts, "kind": kind, "lateral": lateral, "done": false, "plan": plan}

# ---------------------------------------------------------------- the contact
## the stop chance (REF / HAN, how far he has to go, the kick style's difficulty countered by his class)
func _stop_chance(k: Footballer, lateral: float) -> float:
	var s := g.settings
	var skill := s.save_skill_base + (k.stat("REF", 60) + k.stat("HAN", 60)) * 0.5 * s.save_skill_per_stat
	var diff := Data.num(Data.row("kick_styles", g.ball.style).get("save_difficulty"), 0.0)
	var counter := clampf(((k.stat("REF", 60) + k.stat("HAN", 60)) * 0.5 - 60.0) / 40.0 * s.keeper_counter, 0.0, 1.0)
	return clampf(skill * (1.0 - s.dive_difficulty * clampf(absf(lateral) / s.dive_range, 0.0, 1.0)) * (1.0 - diff * (1.0 - counter)), 0.02, 0.98)

## what this save will be, rolled when he commits: "catch" (holds it), "parry" (off the glove) or "beaten"
func _plan(k: Footballer, kind: String, lateral: float, speed: float) -> String:
	var s := g.settings
	if g.rng.randf() > _stop_chance(k, lateral):
		return "parry" if g.rng.randf() < s.save_parry else "beaten"
	var clean := kind in ["catch", "claim"]
	var limit := s.save_speed_base + k.stat("HAN", 60) * s.save_speed_per_han + (s.catch_bonus if clean else 0.0)
	return "catch" if speed <= limit and kind != "palm" else "parry"

## a clip that shows the planned outcome: diving catches / chest catches for a catch, the one-hand dives otherwise
func _pick_for(kind: String, plan: String) -> String:
	var s := g.settings
	if plan == "catch":
		var list: PackedStringArray = s.clips_catch_dive if kind in ["low", "mid", "far"] else (s.clips_catch_body if kind == "catch" else PackedStringArray())
		if not list.is_empty(): return list[g.rng.randi() % list.size()]
	return _pick(kind)

func _resolve(k: Footballer, kind: String, lateral: float, in_reach: bool, plan := "") -> void:
	var s := g.settings
	var b := g.ball
	var bp := b.phys.pos
	var v := b.phys.vel
	if g.carrier != null: return
	if not in_reach:
		k.no_touch = 0.4                                                               # a miss: the ball carries on
		save_event.emit(k, kind, "", "miss")
		return
	if plan == "": plan = _plan(k, kind, lateral, v.length())
	if plan == "beaten":                                                               # it beats him
		k.no_touch = 0.4
		save_event.emit(k, kind, "", "miss")
		return
	var parry := plan == "parry"
	g.last_touch = k
	if plan == "catch":
		save_event.emit(k, kind, "", "catch")
		g.poss.take(k)
		return
	var side := signf(lateral) if absf(lateral) > 0.3 else signf(bp.z - k.pos.y)
	if side == 0.0: side = 1.0
	if kind == "palm":
		b.phys.vel = Vector3(-v.x * 0.2, s.palm_lift, side * s.deflect_wide)             # over the bar / round the post
	else:
		var out := Vector2(k.team.dir, 0.0)                                            # away from his goal
		var rebound := k.pos + out * s.parry_spot
		var danger := false
		for o in g.all:
			if o.team != k.team and not o.is_keeper() and o.pos.distance_to(rebound) < s.parry_danger: danger = true
		var scatter := s.parry_scatter * clampf((80.0 - k.stat("HAN", 60)) / 40.0, 0.0, 1.0)
		if danger or kind == "far":                                                    # attackers waiting: push it round the post, out for a corner
			b.phys.vel = Vector3(-v.x * 0.2, s.deflect_lift, side * s.deflect_wide * 1.3 + g.rng.randf_range(-scatter, scatter) * 0.3)
			save_event.emit(k, kind, "", "parry_corner")
		else:                                                                          # nobody there: steer it back out to the flank
			var flank := side if absf(k.pos.y + side) > 0.0 else 1.0
			b.phys.vel = Vector3(out.x * s.parry_out, 1.5, flank * s.parry_side) + Vector3(g.rng.randf_range(-scatter, scatter), 0.0, g.rng.randf_range(-scatter, scatter))
			save_event.emit(k, kind, "", "parry_field")
	k.no_touch = 0.5
	save_event.emit(k, kind, "", "deflect")

# ---------------------------------------------------------------- one on one: closing the carrier down
var stat_smothers := 0

func smother(k: Footballer, c: Footballer) -> void:
	stat_smothers += 1
	var s := g.settings
	if c == null or g.carrier != c or k.lock > 0.0 or busy(k): return
	var dir := (c.pos + c.vel * 0.15 - k.pos)
	if dir.length() < 0.1: dir = k.face
	dir = dir.normalized()
	k.face = dir
	k.vel = dir * 5.5
	var clip := s.clip_smother if k.node.has_clip(s.clip_smother) else ""
	g.motion.act(k, clip, g.motion.strike_frac(clip, 0.4), func(): _smother_lands(k, c), 1.0, s.smother_clip_time, true)

func _smother_lands(k: Footballer, c: Footballer) -> void:
	var s := g.settings
	if g.carrier != c: return
	if k.pos.distance_to(c.pos) > s.smother_reach or c.shield > 0.0:
		g.poss.failed_tackle(k, c)                                              # he went too early / too late: down, the carrier is through
		return
	var p := clampf(s.smother_base + ((k.stat("REF", 60) + k.stat("HAN", 60)) * 0.5 - c.stat("DRI", 60)) * s.smother_per_stat, 0.15, 0.85)
	if g.rng.randf() < p:
		save_event.emit(k, "smother", "", "catch")
		g.poss.won_tackle(k, c)
		k.lock = maxf(k.lock, 0.3)
	else:
		g.poss.failed_tackle(k, c)
