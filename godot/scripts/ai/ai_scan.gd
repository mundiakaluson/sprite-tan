class_name AiScan
extends Resource
## Scanning and receiving (behaviour catalogue section 1 "Receiving", batch 3).
##  Scan: while his team has the ball and he could be the next receiver, a player glances away from the ball now and then (his facing turns for a moment, you can
##   see it): scans per second by game sense and role (Jordet: 0.44/s on average, central midfielders most, forwards least, almost none with an opponent within 1 m).
##   A scan is remembered for `memory` s.
##  Critical scan: about half a second before the ball reaches him, a player with sense takes one last look.
##  Open body: while the pass travels to him he opens his body to the space (towards goal) instead of squaring up to the ball, if he has scanned.
##  First touch: when he gets it, a player who has scanned takes it away from pressure and turns on the half-turn when there is room; with a man tight behind him he
##   protects it and sets it back (AiSetBack). One who has not scanned takes it facing where it came from and has to turn with it later (MatchKicking's pivot).
## Scanned players also decide faster and scuff fewer passes. AiProfile > Scan, scenes/ai/scan.tres.

@export_group("Scanning")
@export var scan_enabled := true
## scans per second at game sense 40 and 90, before the role factor
@export var rate_low := 0.2
@export var rate_high := 0.6
## by role
@export var role_k := {"CM": 1.2, "CDM": 1.15, "CAM": 1.05, "CB": 0.95, "LB": 0.85, "RB": 0.85, "LW": 0.85, "RW": 0.85, "ST": 0.7}
## only within this distance (m) of the ball; an opponent closer than tight_close (m) all but stops it, from free_at (m) it is not affected
@export var scan_range := 32.0
@export var tight_close := 1.0
@export var free_at := 4.0
## a glance turns him this far (degrees) for glance_time (real s)
@export var glance_deg := 75.0
@export var glance_time := 0.28
## a scan is remembered this long (real s)
@export var memory := 2.2
## the critical scan: when the ball is this many real s from him, chance = critical_k x game sense / 100
@export var critical_eta := 0.6
@export_range(0.0, 1.5) var critical_k := 1.0

@export_group("Receiving")
## a marker this close (m) and goal side of him when the ball arrives: protect it and set it back
@export var tight_behind := 2.6
## with an opponent within this (m), the first touch goes away from him
@export var touch_away_within := 5.5
@export_range(0.0, 2.0) var touch_away_weight := 0.9
## decision time after a touch (game sense players with a picture decide at once)
@export var think_scanned := Vector2(0.05, 0.18)
@export var think_blind := Vector2(0.35, 0.65)
## a player on the ball without a picture misreads his options: he misses a defender in a lane with this chance, and judges space around a mate with this much noise (m)
@export_range(0.0, 1.0) var blind_lane_miss := 0.4
@export var blind_open_noise := 2.5
## scanned players' passes scuff less (multiplies MatchKicking's scuff chance)
@export_range(0.0, 1.0) var scanned_scuff_k := 0.65

static var stat_scans := {}          ## role -> scans
static var stat_time := {}           ## role -> seconds eligible to scan
static var stat_critical := 0
static var stat_turns := 0           ## received and turned on the half-turn
static var stat_protect := 0         ## received with a man tight: protected it
static var stat_blind := 0           ## received without a scan
static var stat_fwd := {"scanned": [0, 0], "blind": [0, 0]}   ## forward passes [completed, played] by whether the passer had scanned

func _now(c: AiContext) -> float:
	return c.game.clock

## once per team per frame
func compute(c: AiContext, dt: float) -> void:
	if not scan_enabled: return
	var g := c.game
	var ours_moving := c.has_ball or (c.carrier == null and g.pass_target != null and g.pass_target.team == c.team)
	if not ours_moving: return
	var now := _now(c)
	var rdt := dt / maxf(Engine.time_scale, 0.05)
	for f in c.team.players:
		if f.is_keeper() or f == c.carrier or f.lock > 0.0: continue
		if f.pos.distance_to(c.ball) > scan_range: continue
		var o := c.nearest_opponent(f.pos)
		var d := o.pos.distance_to(f.pos) if o != null else 99.0
		var press_k := clampf((d - tight_close) / maxf(free_at - tight_close, 0.1), 0.12, 1.0)
		var sense := clampf(((f.stat("PAS", 60) + f.stat("DRI", 60)) * 0.5 - 40.0) / 50.0, 0.0, 1.0)
		var rate := lerpf(rate_low, rate_high, sense) * float(role_k.get(f.role, 1.0)) * press_k
		stat_time[f.role] = float(stat_time.get(f.role, 0.0)) + rdt
		if g.pass_target == f and c.carrier == null:
			_critical(f, c, sense, now)
			continue
		if g.rng.randf() < rate * rdt: _glance(f, c, now)

func _glance(f: Footballer, c: AiContext, now: float) -> void:
	f.ai["scan_t"] = now
	stat_scans[f.role] = int(stat_scans.get(f.role, 0)) + 1
	var to_ball := (c.ball - f.pos).normalized()
	var side := 1.0 if Vector2(-to_ball.y, to_ball.x).dot((c.goal() - f.pos).normalized()) > 0.0 else -1.0
	f.ai["look"] = to_ball.rotated(deg_to_rad(glance_deg) * side)        # over the shoulder, on the side of their goal
	f.ai["look_until"] = now + c.game_s(glance_time)

func _critical(f: Footballer, c: AiContext, sense: float, now: float) -> void:
	var v := c.ball_vel.length()
	if v < 1.0: return
	var eta := c.ball.distance_to(f.pos) / v
	var key := int(c.game.kicking.stat_passes)
	if eta > critical_eta or int(f.ai.get("crit_key", -1)) == key: return
	f.ai["crit_key"] = key
	if c.game.rng.randf() < critical_k * (0.3 + 0.7 * sense):
		_glance(f, c, now)
		stat_critical += 1

func scanned(f: Footballer, c: AiContext) -> bool:
	return _now(c) - float(f.ai.get("scan_t", -1e9)) < c.game_s(memory)

## per player after his role decided: the receiver opens up while the ball travels (the facing MatchMotion uses when he is not running fast)
func post(f: Footballer, i: AiIntent, c: AiContext) -> void:
	if not scan_enabled or i == null: return
	if c.game.pass_target == f and c.carrier == null and scanned(f, c):
		var to_ball := (c.ball - f.pos).normalized()
		var open := (to_ball + (c.goal() - f.pos).normalized() * 0.9).normalized()
		f.ai["look"] = open
		f.ai["look_until"] = _now(c) + c.game_s(0.2)

## he just got the ball (MatchPossession.take -> AiBrain.received). prev = who touched it before him
func on_take(f: Footballer, prev: Footballer, c: AiContext) -> void:
	_count_pass(f, prev, c)
	if not scan_enabled or f.is_keeper(): return
	f.ai.erase("setback")
	f.ai.erase("look")
	var g := c.game
	var o := c.nearest_opponent(f.pos)
	var d := o.pos.distance_to(f.pos) if o != null else 99.0
	var to_goal := (c.goal() - f.pos).normalized()
	if not scanned(f, c):
		stat_blind += 1
		f.think = g.rng.randf_range(think_blind.x, think_blind.y)
		return
	f.think = g.rng.randf_range(think_scanned.x, think_scanned.y)
	f.ai["picture"] = true
	var behind := o != null and d < tight_behind and (o.pos - f.pos).dot(to_goal) > 0.3 * d
	if behind:                                                               # a man tight on his back: protect it, set it back
		f.face = (f.pos - o.pos).normalized()
		f.ai["setback"] = true
		stat_protect += 1
		return
	var dir := to_goal
	if o != null and d < touch_away_within: dir = (to_goal + (f.pos - o.pos).normalized() * touch_away_weight).normalized()
	f.face = dir                                                             # the half-turn: first touch into the space
	stat_turns += 1

## pass bookkeeping for the headless numbers: forward passes completed by whether the passer had a picture when he got the ball
func _count_pass(f: Footballer, prev: Footballer, c: AiContext) -> void:
	if prev == null or prev == f or prev.is_keeper(): return
	var fwd := bool(prev.ai.get("fwd_pass", false))
	if not fwd: return
	prev.ai.erase("fwd_pass")
	var k := "scanned" if bool(prev.ai.get("picture_pass", false)) else "blind"
	var arr: Array = stat_fwd[k]
	arr[1] += 1
	if prev.team == f.team: arr[0] += 1

## a pass is struck: remember whether it went forward and whether he had a picture (for the numbers above)
static func on_kick(f: Footballer, to: Vector2) -> void:
	f.ai["fwd_pass"] = (to.x - f.pos.x) * f.team.dir > 6.0
	f.ai["picture_pass"] = bool(f.ai.get("picture", false))
	f.ai.erase("picture")
