class_name MatchKeeper
extends RefCounted
## Goalkeeper saves with animation. When a shot is heading for the keeper's goal and he can reach it, he plays one of the keeper clips (gk02 reach dive, gk09 low dive, gk10 high palm,
## gk24 fingertip ...) instead of the ball snapping into his hands: he slides / dives to where the ball will cross him, arriving at the clip's `strike` frame, and at that frame the save is
## resolved (catch, palm / fingertip deflection, parry, or a miss if the ball is out of reach). Left dives mirror the clip (the clips are authored for dives to the keeper's right).
## Which clips he uses for which kind of ball is in MatchSettings > Goalkeeper saves (lists, he picks one at random: add more variants there). Every number lives there too.

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
		if f.lock <= 0.0 or f.pos.distance_to(d["to"]) < 0.01 and float(d["t"]) > float(d["T"]) + 0.6:
			_dives.erase(f)
	if g.phase != MatchGame.Phase.PLAY or g.carrier != null: return
	for k in g.all:
		if k.is_keeper() and k.lock <= 0.0 and not _dives.has(k): _consider(k)

# ---------------------------------------------------------------- is a save needed
func _consider(k: Footballer) -> void:
	var s := g.settings
	var bp := g.ball.phys.pos
	var v := g.ball.phys.vel
	if v.length() < s.save_threat_speed or v.x * k.team.dir >= 0.0: return          # slow, or not heading for his goal
	var t := (k.pos.x - bp.x) / v.x
	if t <= 0.0 or t > s.save_max_time: return
	var z := bp.z + v.z * t
	var h := maxf(bp.y + v.y * t - 0.5 * 9.81 * t * t, 0.12)
	if absf(z) > MatchGame.GOAL_HALF + 0.6: return                                    # wide of the post: no save to make
	var lateral := z - k.pos.y
	if absf(lateral) > s.dive_range or h > s.keeper_reach_height + s.jump_height: return
	var kind := _kind(lateral, h, v.length())
	var clip := _pick(kind)
	if clip == "" or not k.node.has_clip(clip): return
	var anim := k.node.anim_player.get_animation(clip)
	var ts := _strike_time(anim)
	if t > ts + s.save_reaction: return                                               # too early: wait until the clip would arrive with the ball
	_start(k, clip, kind, anim.length, ts, lateral, z, h)

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
func _start(k: Footballer, clip: String, kind: String, length: float, ts: float, lateral: float, z: float, h: float) -> void:
	var s := g.settings
	var bp := g.ball.phys.pos
	var to_ball := Vector2(bp.x - k.pos.x, bp.z - k.pos.y)
	var face := to_ball.normalized() if to_ball.length() > 0.1 else Vector2(-k.team.dir, 0.0)
	var right := Vector2(-face.y, face.x)                                             # his right on the screen
	k.face = face
	k.mirror = absf(lateral) > 0.5 and Vector2(0.0, signf(lateral)).dot(right) < 0.0     # clips dive to his right; a left dive is the mirrored clip
	var reach_z := clampf(lateral, -s.dive_range, s.dive_range) * (1.0 if kind in ["low", "mid", "far"] else s.stand_travel)
	var to := Vector2(k.pos.x + k.team.dir * s.dive_forward, k.pos.y + reach_z)
	g.motion.act(k, clip, ts / length, func(): _resolve(k, kind, lateral))
	k.lock = length
	_dives[k] = {"from": k.pos, "to": to, "t": 0.0, "T": maxf(ts, 0.1)}

# ---------------------------------------------------------------- the contact
func _resolve(k: Footballer, kind: String, lateral: float) -> void:
	var s := g.settings
	var b := g.ball
	var bp := b.phys.pos
	var v := b.phys.vel
	if g.carrier != null: return
	var reach := s.keeper_reach + k.stat("REF", 60) * s.keeper_ref_reach + s.dive_extra
	var max_h := s.keeper_reach_height + s.jump_height
	if absf(bp.x - k.pos.x) > 1.8 or absf(bp.z - k.pos.y) > reach or bp.y > max_h:
		k.no_touch = 0.4                                                               # a miss: the ball carries on
		return
	var speed := v.length()
	var clean := kind in ["catch", "claim"]
	var limit := s.save_speed_base + k.stat("HAN", 60) * s.save_speed_per_han + (s.catch_bonus if clean else 0.0)
	g.last_touch = k
	if speed <= limit and kind != "palm":
		g.poss.take(k)
		return
	var side := signf(lateral) if absf(lateral) > 0.3 else signf(bp.z - k.pos.y)
	if side == 0.0: side = 1.0
	if kind == "palm":
		b.phys.vel = Vector3(-v.x * 0.2, s.palm_lift, side * s.deflect_wide)             # over the bar / round the post
	elif kind == "far":
		b.phys.vel = Vector3(-v.x * 0.25, s.deflect_lift, side * s.deflect_wide * 1.3)   # fingertips round the post
	else:
		b.phys.vel = Vector3(-v.x * 0.3, v.y * 0.5 + 2.0, v.z + g.rng.randf_range(-5.0, 5.0))   # a parry back into play
	k.no_touch = 0.5
