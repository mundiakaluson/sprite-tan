class_name DoubleTeam
extends RefCounted
## DF08 Double Team (any card with effect move=double): when it is revealed in a duel, the nearest team mate of the defender zaps in to help.
## Not a Titan moment: a small scan ping on the defender, a short charge on the helper, then he rides a thin bolt along a zig-zag path
## (ZapTrail's "zap" animation sets how far along he is), leaving a few faint afterimages (ZapGhost) and a crackle that fizzles out.
##   Upfield (the carrier further than double_deep_dist from our goal): he lands right BEHIND the carrier and takes it from behind if the duel is won.
##   Deep: he lands GOAL SIDE, behind the first defender on the side he would go past, covering; the first defender makes the challenge.
## Either way the challenge side's stat gets double_stat_bonus. Numbers: MatchSettings > Double team. Effects: scenes/engagement/zap_*.tscn.

const PING := preload("res://scenes/engagement/zap_ping.tscn")
const GHOST := preload("res://scenes/engagement/zap_ghost.tscn")
const TRAIL := preload("res://scenes/engagement/zap_trail.tscn")

var g: MatchGame
var helper: Footballer = null
var deep := false
var arrived := false
var _trail: ZapTrail = null
var _ghosts_done := 0
var _end := Vector2.ZERO
var stat_zaps := 0
var stat_deep := 0

func _init(game: MatchGame) -> void:
	g = game

## true while a helper is on his way
func active() -> bool:
	return helper != null and not arrived

## the nearest outfield team mate of `d` to the carrier, free to go (or null)
func pick_helper(c: Footballer, d: Footballer) -> Footballer:
	var s := g.settings
	var best: Footballer = null
	var bd := s.double_range
	for f in d.team.players:
		if f == d or f.is_keeper() or f.lock > 0.0: continue
		var dist := f.pos.distance_to(c.pos)
		if dist < bd and dist > s.double_min_range:
			bd = dist
			best = f
	return best

## starts the zap for this engagement; false if nobody can come (then the duel resolves as a normal one)
func start(e: Engagement) -> bool:
	var s := g.settings
	var c := e.ball
	var d := e.challenger
	var h := pick_helper(c, d)
	if h == null: return false
	helper = h
	e.helper = h
	arrived = false
	_ghosts_done = 0
	stat_zaps += 1
	var own_goal := Vector2(-MatchGame.HALF_L * d.team.dir, 0.0)
	deep = c.pos.distance_to(own_goal) < s.double_deep_dist
	var zap_time := s.double_zap_time
	var c_at := c.pos + c.vel * zap_time                                               # where the carrier will be when he lands
	if deep:
		stat_deep += 1
		var to_goal := (own_goal - c_at).normalized()
		var perp := Vector2(-to_goal.y, to_goal.x)
		var side := signf(perp.dot(d.pos - c_at))
		if side == 0.0: side = 1.0
		_end = c_at + to_goal * s.double_cover_dist - perp * side * s.double_cover_side    # goal side, on the side the first defender is not
	else:
		var run := c.vel.normalized() if c.vel.length() > 0.5 else c.face
		_end = c_at - run * s.double_behind                                             # right behind him
	_end.x = clampf(_end.x, -MatchGame.HALF_L, MatchGame.HALF_L)
	_end.y = clampf(_end.y, -MatchGame.HALF_W, MatchGame.HALF_W)
	# the path: a zig-zag from him to the landing spot
	var a := h.pos
	var dir := _end - a
	var perp2 := Vector2(-dir.y, dir.x).normalized()
	var pts := PackedVector3Array()
	var n := maxi(2, s.double_kinks)
	for i in n + 1:
		var t := float(i) / n
		var q := a + dir * t
		if i > 0 and i < n: q += perp2 * (1.0 if i % 2 else -1.0) * s.double_jitter * g.rng.randf_range(0.6, 1.0)
		pts.append(Vector3(q.x, 0.0, q.y))
	_trail = TRAIL.instantiate()
	g.stadium.actors.add_child(_trail)
	_trail.camera = g.stadium.camera
	_trail.path = pts
	_trail.head = 0.0
	_trail.start()
	_ping(d.pos, "ping")                                                               # the scan
	_ping(h.pos, "charge")                                                             # he charges
	h.pending = Callable()
	h.aim_done = Callable()
	h.vel = Vector2.ZERO
	h.lock = 2.0
	if h.node.has_clip("base_sprint"):
		h.node.play_clip("base_sprint")
		h.clip = "base_sprint"
	return true

## after the motion step: puts the helper on the trail
func update(_dt: float) -> void:
	if helper == null or arrived: return
	if _trail == null or not is_instance_valid(_trail):
		_arrive()
		return
	var h := helper
	var t := _trail.head
	var w := _trail.point_at(t)
	var ahead := _trail.point_at(minf(1.0, t + 0.05))
	var p := Vector2(w.x, w.z)
	var fwd := Vector2(ahead.x - w.x, ahead.z - w.z)
	if fwd.length() > 0.01: h.face = fwd.normalized()
	h.pos = p
	h.vel = Vector2.ZERO
	g.stadium.set_actor_pos(h.node, g.stadium.pitch_pos(Vector3(p.x, 0.0, p.y)))
	h.node.face_vector(g.stadium.screen_dir(h.pos, h.face))
	var n := g.settings.double_ghosts                                                  # afterimages where he has been
	while _ghosts_done < n and t >= (_ghosts_done + 0.5) / n:
		_ghosts_done += 1
		var gh: ZapGhost = GHOST.instantiate()
		g.stadium.add_actor(gh, g.stadium.pitch_pos(Vector3(p.x, 0.0, p.y)))
		gh.copy_from(h.node)
		gh.tree_exiting.connect(func(): g.stadium.remove_actor(gh))
		gh.start()
	if t >= 1.0: _arrive()

func _arrive() -> void:
	var h := helper
	arrived = true
	h.pos = _end
	h.lock = 0.0
	h.vel = h.face * h.top_speed() * g.settings.double_arrive_speed
	_ping(h.pos, "land")

## the engagement is over: forget the helper (the trail keeps fizzling by itself)
func clear() -> void:
	helper = null
	arrived = false
	_trail = null

func _ping(at: Vector2, anim: String) -> void:
	var p: ZapPing = PING.instantiate()
	g.stadium.add_actor(p, g.stadium.pitch_pos(Vector3(at.x, 0.0, at.y)))
	p.start(anim)
	p.tree_exiting.connect(func(): g.stadium.remove_actor(p))
