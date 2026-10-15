class_name MatchGame
extends Node
## The match. Two teams of 11 (Team / Footballer) play on the 3D stadium with the real ball. The players are plain 2D sprites projected by the Stadium,
## all the playing is done here in metres (x along the pitch, z across; home attacks towards +x, the right of the screen).
##
## You do not steer a player: you give orders with the mouse or controller (MatchControls): click a player for his menu (Pass, Through, Lob, Shoot, Run, Press, Tackle),
## drag from a player to make a run, click a skill card to play it with the selected player. Everyone plays by himself between orders. m_restart (R / Start) after full time.
## Placeholder AI and numbers: tune the exports below, or move them into data/ when they settle.

signal goal_scored(team: Team, scorer: Footballer)
signal full_time(home_score: int, away_score: int)

@export var stadium_id := "ST01"
@export var ball_id := "B01"
@export var home_formation := "F01"
@export var away_formation := "F02"
## real minutes the 90 game minutes take
@export_range(1.0, 20.0) var match_minutes := 4.0
## seconds of cooldown per cooldown number in cards.csv
@export var cooldown_scale := 1.5
## 0 = sleepy opponents, 1 = sharp
@export_range(0.0, 1.0) var ai_level := 0.6
## how slow time runs while you line up a shot (1 = no slow motion)
@export_range(0.05, 1.0) var aim_slowmo := 0.3

const HALF_L := 52.5
const HALF_W := 34.0
const GOAL_HALF := 3.66
const BAR := 2.44
const GAME_SECONDS := 5400.0
enum Phase { KICKOFF, PLAY, GOAL, FULLTIME }

@onready var stadium: Stadium = $View/Viewport/Stadium
@onready var hud: MatchHud = $Hud
@onready var controls: MatchControls = $Controls

var rng := RandomNumberGenerator.new()
var home: Team
var away: Team
var teams: Array[Team] = []
var all: Array[Footballer] = []
var ball: Ball
var carrier: Footballer
var last_touch: Footballer
var selected: Footballer          ## the player the human is giving orders to (set by MatchControls)
var phase := Phase.KICKOFF
var phase_t := 0.0
var clock := 0.0
var hand: Array = []
var cooldown := {}
var _next_kick: Team
var _slow := false

func _ready() -> void:
	rng.randomize()
	if not Data.ok:
		hud.message("No exported data. Open the manager tool and press Export to game.", 999.0)
		return
	stadium.stadium_id = stadium_id
	var used := {}
	home = Team.new(); home.label = "HOME"; home.dir = 1.0; home.human = true; home.color = Color("d63240")
	away = Team.new(); away.label = "AWAY"; away.dir = -1.0; away.color = Color("3a5bd6")
	home.build(home_formation, used, rng)
	away.build(away_formation, used, rng)
	teams = [home, away]
	for t in teams:
		for f in t.players:
			f.node = Player.create()
			stadium.add_actor(f.node, Vector2(50, 50))
			f.node.setup(f.row)
			all.append(f)
	ball = Ball.create(ball_id)
	stadium.add_ball(ball)
	ball.preview_speed = 1.0
	_deal_hand()
	controls.setup(self, hud)
	hud.card_pressed.connect(_play_card)
	_next_kick = home
	_kickoff(home)
	hud.set_hand(hand)
	_update_hud()

# ---------------------------------------------------------------- hand
func _deal_hand() -> void:
	hand.clear()
	var cards := Data.table("cards")
	for cat in ["SHOT", "SHOT", "PASS", "PASS", "DRIBBLE", "DRIBBLE", "DEFEND", "DEFEND"]:
		var pool := cards.filter(func(c): return c["cat"] == cat and not hand.has(c))
		if pool.is_empty(): continue
		hand.append(pool[rng.randi() % pool.size()])

# ---------------------------------------------------------------- restarts
func _kickoff(kicking: Team) -> void:
	_slow = false
	for t in teams:
		for f in t.players:
			f.pos = f.slot
			if f.pos.x * t.dir > -2.0: f.pos.x = -2.0 * t.dir
			f.vel = Vector2.ZERO; f.want = Vector2.ZERO; f.lock = 0.0; f.no_touch = 0.0; f.shield = 0.0
			f.pending = Callable(); f.order = {}; f.face = Vector2(t.dir, 0.0); f.think = rng.randf_range(0.2, 0.8)
	var taker := kicking.players[0]
	var best := 1e9
	for f in kicking.players:
		if f.is_keeper(): continue
		var d := f.pos.length()
		if d < best:
			best = d; taker = f
	taker.pos = Vector2(-0.8 * kicking.dir, 0.0)
	carrier = null
	_take(taker)
	phase = Phase.KICKOFF
	phase_t = 1.8
	stadium.focus = Vector2(50, 50)
	stadium.snap_camera()
	hud.message("KICK OFF", 1.6)

func _take(f: Footballer) -> void:
	carrier = f
	last_touch = f
	f.hold = 0.0
	f.think = rng.randf_range(0.25, 0.5)
	ball.hold()

func _goal(scorer_team: Team) -> void:
	_slow = false
	scorer_team.score += 1
	phase = Phase.GOAL
	phase_t = 3.6
	_next_kick = away if scorer_team == home else home
	var who := last_touch.display_name() if last_touch != null else ""
	hud.message("GOAL!  %s" % who, 3.4)
	goal_scored.emit(scorer_team, last_touch)

func _restart_out(bp: Vector3) -> void:
	var spot := Vector2.ZERO
	var taking: Team
	var text := ""
	if absf(bp.z) > HALF_W:
		taking = away if (last_touch != null and last_touch.team == home) else home
		spot = Vector2(clampf(bp.x, -HALF_L + 2.0, HALF_L - 2.0), signf(bp.z) * (HALF_W - 0.7))
		text = "THROW-IN"
	else:
		var defending := away if bp.x > 0.0 else home       # the side whose goal line it crossed
		var attacking := home if defending == away else away
		if last_touch != null and last_touch.team == attacking:
			taking = defending
			spot = Vector2(defending.dir * -1.0 * (HALF_L - 6.0), 0.0)
			text = "GOAL KICK"
		else:
			taking = attacking
			spot = Vector2(signf(bp.x) * (HALF_L - 0.8), signf(bp.z) * (HALF_W - 0.8))
			text = "CORNER"
	var taker: Footballer = null
	var best := 1e9
	for f in taking.players:
		if text == "GOAL KICK" and not f.is_keeper(): continue
		if text != "GOAL KICK" and f.is_keeper(): continue
		var d := f.pos.distance_to(spot)
		if d < best:
			best = d; taker = f
	if taker == null: return
	taker.pos = spot
	taker.vel = Vector2.ZERO
	taker.face = Vector2(taking.dir, 0.0) if text != "CORNER" else (-spot).normalized()
	carrier = null
	_take(taker)
	taker.no_touch = 0.0
	hud.message(text, 1.2)

# ---------------------------------------------------------------- frame
func _physics_process(dt: float) -> void:
	if not Data.ok or ball == null: return
	if phase == Phase.PLAY:
		clock += dt * GAME_SECONDS / (match_minutes * 60.0)
		if clock >= GAME_SECONDS:
			phase = Phase.FULLTIME
			hud.message("FULL TIME  %d - %d     R = play again" % [home.score, away.score], 999.0)
			full_time.emit(home.score, away.score)
		else:
			for f in all: _ai(f, dt)
	elif phase == Phase.KICKOFF or phase == Phase.GOAL:
		phase_t -= dt
		if phase_t <= 0.0:
			if phase == Phase.KICKOFF: phase = Phase.PLAY
			else: _kickoff(_next_kick)
	elif phase == Phase.FULLTIME:
		if Input.is_action_just_pressed("m_restart"): get_tree().reload_current_scene()
	_move(dt)
	_ball_logic(dt)
	if phase == Phase.PLAY: _boundaries()
	for id in cooldown.keys():
		cooldown[id] = maxf(0.0, float(cooldown[id]) - dt)
	var bp := ball.phys.pos
	stadium.focus = stadium.pitch_pos(Vector3(bp.x, 0.0, bp.z))
	_update_hud()

func _update_hud() -> void:
	hud.set_score(home.score, away.score, int(clock / 60.0))
	hud.set_controlled(selected.display_name() if selected != null else "")
	hud.set_cooldowns(cooldown)

func _ball2() -> Vector2:
	return Vector2(ball.phys.pos.x, ball.phys.pos.z)

# ---------------------------------------------------------------- the human
func _nearest_to_ball(t: Team, outfield_only: bool, skip: Footballer = null) -> Footballer:
	var best: Footballer = null
	var bd := 1e9
	var b2 := _ball2()
	for f in t.players:
		if f == skip or (outfield_only and f.is_keeper()): continue
		var d := f.pos.distance_to(b2)
		if d < bd:
			bd = d; best = f
	return best

# ---------------------------------------------------------------- the AI
func _ai_speed(f: Footballer) -> float:
	return 1.0 if f.team.human else lerpf(0.8, 1.0, ai_level)

func _ai(f: Footballer, dt: float) -> void:
	if f.lock > 0.0: return
	if not f.order.is_empty() and not f.is_keeper():
		_follow_order(f, dt)
		return
	if f.is_keeper():
		_ai_keeper(f, dt)
		return
	if carrier == f:
		_ai_carrier(f, dt)
		return
	var t := f.team
	var has := carrier != null and carrier.team == t
	var b2 := _ball2()
	if not has and _nearest_to_ball(t, true) == f:
		var tgt := b2 + Vector2(ball.phys.vel.x, ball.phys.vel.z) * 0.25
		if carrier != null: tgt = carrier.pos
		f.want = (tgt - f.pos).limit_length(f.top_speed() * _ai_speed(f)) if f.pos.distance_to(tgt) > 1.0 else Vector2.ZERO
		return
	var w := 0.6
	var k := 0.3
	match f.role:
		"CB": w = 0.3; k = 0.22
		"LB", "RB": w = 0.6; k = 0.25
		"CDM": w = 0.5; k = 0.3
		"CM": w = 0.8; k = 0.35
		_: w = 1.0; k = 0.4
	var push := (14.0 if has else -4.0) * w
	var spot := f.slot + Vector2(push * t.dir, 0.0) + (b2 - f.slot) * k
	spot.x = clampf(spot.x, -HALF_L + 3.0, HALF_L - 3.0)
	spot.y = clampf(spot.y, -HALF_W + 2.0, HALF_W - 2.0)
	var to := spot - f.pos
	f.want = to.normalized() * minf(f.top_speed() * 0.8 * _ai_speed(f), to.length() * 1.6) if to.length() > 0.5 else Vector2.ZERO

func _ai_keeper(f: Footballer, dt: float) -> void:
	var t := f.team
	if carrier == f:
		f.hold += dt
		f.want = Vector2.ZERO
		if f.hold > 1.3: _do_pass(f, Vector2.ZERO, true)
		return
	var gx := -t.dir * (HALF_L - 2.0)
	var b2 := _ball2()
	var tz := clampf(b2.y * 0.45, -3.3, 3.3)
	var tx := gx
	if absf(b2.x - gx) < 24.0: tx = gx + t.dir * 1.8
	var to := Vector2(tx, tz) - f.pos
	f.want = to.limit_length(f.top_speed() * _ai_speed(f)) if to.length() > 0.3 else Vector2.ZERO

func _ai_carrier(f: Footballer, dt: float) -> void:
	f.think -= dt
	var goal := Vector2(HALF_L * f.team.dir, 0.0)
	var to_goal := goal - f.pos
	var dirv := to_goal.normalized()
	var opp := _nearest_opponent(f)
	var pressure := 99.0
	if opp != null:
		var d := opp.pos - f.pos
		pressure = d.length()
		if pressure < 7.0 and d.dot(dirv) > 0.0:
			var side := Vector2(-dirv.y, dirv.x)
			if side.dot(d) > 0.0: side = -side
			dirv = (dirv + side * 0.9).normalized()
	f.want = dirv * f.top_speed() * 0.92 * _ai_speed(f)
	if f.think > 0.0: return
	f.think = rng.randf_range(0.35, 0.8)
	var dist := to_goal.length()
	if dist < 24.0 and rng.randf() < 0.55:
		_do_shot(f, rng.randf_range(-0.9, 0.9))
	elif pressure < 4.5 or (dist > 26.0 and rng.randf() < 0.25):
		_do_pass(f, Vector2.ZERO, rng.randf() < 0.15)

func _nearest_opponent(f: Footballer) -> Footballer:
	var other := away if f.team == home else home
	var best: Footballer = null
	var bd := 1e9
	for o in other.players:
		var d := o.pos.distance_to(f.pos)
		if d < bd:
			bd = d; best = o
	return best

# ---------------------------------------------------------------- passing and shooting
func _best_target(f: Footballer, aim: Vector2) -> Footballer:
	var other := away if f.team == home else home
	var best: Footballer = null
	var bs := -1e9
	for m in f.team.players:
		if m == f: continue
		var v := m.pos - f.pos
		var dist := v.length()
		if dist < 4.0 or dist > 48.0: continue
		var s := 0.0
		if aim.length() > 0.1:
			s += aim.normalized().dot(v.normalized()) * 30.0
		else:
			s += v.x * f.team.dir / 45.0 * 12.0
		s -= absf(dist - 20.0) * 0.4
		var open := 12.0
		for o in other.players:
			open = minf(open, o.pos.distance_to(m.pos))
			var seg := Geometry2D.get_closest_point_to_segment(o.pos, f.pos, m.pos)
			if seg.distance_to(o.pos) < 2.2: s -= 12.0
		s += open
		if m.is_keeper() and not f.is_keeper(): s -= 15.0
		if s > bs:
			bs = s; best = m
	return best

func _do_pass(f: Footballer, aim: Vector2, lob: bool, target: Footballer = null) -> void:
	var tgt := target if target != null else _best_target(f, aim)
	var action := "lob" if lob else "pass"
	if tgt == null: _kick_action(f, action, f.pos + (aim if aim.length() > 0.1 else f.face) * 18.0)
	else: _kick_action(f, action, tgt.pos, tgt.vel)

func _do_shot(f: Footballer, aim_z: float) -> void:
	var to := Vector2(HALF_L * f.team.dir + f.team.dir * 1.5, clampf(aim_z * 3.0, -3.1, 3.1))
	var over := {}
	var r := rng.randf()
	if f.pos.distance_to(to) > 15.0 and r < 0.25: over["style"] = "K02"
	elif r > 0.92: over["style"] = "K06"
	_kick_action(f, "shot", to, Vector2.ZERO, over)

## The kick animation, then the ball state does the kick (Ball.play_action: Pass / Through / Lob / Shot, numbers in data/ball_actions.csv). `over` may replace style / speed / noise.
func _kick_action(f: Footballer, action: String, to: Vector2, to_vel := Vector2.ZERO, over := {}) -> void:
	_act(f, "kick", 0.35, func(): _launch(f, action, to, to_vel, over))

func _launch(f: Footballer, action: String, to: Vector2, to_vel: Vector2, over: Dictionary) -> void:
	if carrier != f: return
	carrier = null
	ball.preview_spin = Vector3.ZERO
	ball.play_action(action, to, f.row, to_vel, over)
	f.no_touch = 0.35
	last_touch = f

## play a clip and run `strike` when it reaches its contact point; the player is committed meanwhile
func _act(f: Footballer, clip_name: String, strike_frac: float, strike: Callable) -> void:
	var length := 0.0
	if f.node.has_clip(clip_name):
		length = f.node.anim_player.get_animation(clip_name).length
		f.node.play_clip(clip_name)
		f.clip = clip_name
	f.lock = minf(length, 1.1)
	f.pending = strike
	f.pending_t = length * strike_frac
	f.vel *= 0.3

# ---------------------------------------------------------------- tackling
func _try_tackle(f: Footballer) -> void:
	if carrier == null or carrier.team == f.team or f.lock > 0.0 or f.no_touch > 0.0: return
	if f.pos.distance_to(carrier.pos) > 3.0: return
	var target := carrier
	f.vel = (target.pos - f.pos).normalized() * 6.0
	_act(f, "df01_stand_tackle", 0.45, func(): _resolve_tackle(f, target, 0.0))

func _resolve_tackle(f: Footballer, target: Footballer, bonus: float) -> void:
	if carrier != target or f.pos.distance_to(target.pos) > 2.4:
		f.lock = maxf(f.lock, 0.4)
		return
	if target.shield > 0.0: return
	var chance := 0.5 + (f.stat("DEF", 60) - target.stat("DRI", 60)) * 0.01 + bonus
	if rng.randf() < chance:
		_steal(f, target)
	else:
		f.lock = maxf(f.lock, 0.6)

func _steal(thief: Footballer, victim: Footballer) -> void:
	victim.no_touch = 0.9
	victim.pending = Callable()
	thief.no_touch = 0.0
	_take(thief)

func _auto_tackles(dt: float) -> void:
	if carrier == null or carrier.shield > 0.0: return
	var other := away if carrier.team == home else home
	for o in other.players:
		if o.no_touch > 0.0 or o.lock > 0.0: continue
		if o.pos.distance_to(carrier.pos) > 1.2: continue
		var rate := 1.3 * (o.stat("DEF", 60) + 30.0) / (carrier.stat("DRI", 60) + 30.0) * lerpf(0.6, 1.0, ai_level)
		if rng.randf() < rate * dt:
			_steal(o, carrier)
			return

# ---------------------------------------------------------------- orders (from MatchControls)
## the buttons of the order menu for a player
func menu_for(f: Footballer) -> Array:
	if carrier == f: return ["through", "run"]
	return ["run", "press", "tackle"]

## slow motion while the human lines up a shot (eased in and out in _process)
func set_slowmo(on: bool) -> void:
	_slow = on

func _process(dt: float) -> void:
	var real_dt := dt / maxf(Engine.time_scale, 0.05)
	var target := aim_slowmo if _slow and phase == Phase.PLAY else 1.0
	Engine.time_scale = move_toward(Engine.time_scale, target, 5.0 * real_dt)

func _exit_tree() -> void:
	Engine.time_scale = 1.0

## shoot at a spot of the grass (the drag from the ball carrier)
func order_shoot_at(f: Footballer, spot: Vector2) -> void:
	if carrier != f: return
	var over := {}
	if rng.randf() < 0.12: over["style"] = "K02"
	_kick_action(f, "shot", spot, Vector2.ZERO, over)

## a run: he goes there by himself (the carrier dribbles there), then the AI takes over again
func order_run(f: Footballer, spot: Vector2) -> void:
	spot.x = clampf(spot.x, -HALF_L + 1.0, HALF_L - 1.0)
	spot.y = clampf(spot.y, -HALF_W + 1.0, HALF_W - 1.0)
	f.order = {"kind": "run", "target": spot, "t": 9.0}
	hud.toast("%s: run" % f.display_name())

## chase the ball (or its carrier) for a few seconds
func order_press(f: Footballer) -> void:
	f.order = {"kind": "press", "t": 5.0}
	hud.toast("%s: press" % f.display_name())

func order_tackle(f: Footballer) -> void:
	if carrier == null or carrier.team == f.team:
		hud.toast("Nobody to tackle")
		return
	if f.pos.distance_to(carrier.pos) > 3.0:
		f.order = {"kind": "press", "t": 3.0}
		hud.toast("Too far: closing down")
		return
	_try_tackle(f)

## kind = "pass" / "through" / "lob". To a team mate (the ball leads him; a through ball also sends him running) or to a spot.
func order_pass(f: Footballer, kind: String, mate: Footballer, spot: Vector2) -> void:
	if carrier != f:
		hud.toast("%s has not got the ball" % f.display_name())
		return
	var action := kind if kind in ["pass", "through", "lob"] else "pass"
	if mate != null:
		var vel := Vector2.ZERO
		if action == "through":
			vel = Vector2(f.team.dir * 7.0, 0.0)
			order_run(mate, mate.pos + vel * 1.5)
		_kick_action(f, action, mate.pos, mate.vel if vel == Vector2.ZERO else vel)
	elif spot != Vector2.INF:
		_kick_action(f, action, spot)

func _follow_order(f: Footballer, dt: float) -> void:
	var o := f.order
	o["t"] = float(o.get("t", 5.0)) - dt
	if o["t"] <= 0.0:
		f.order = {}
		return
	var kind := String(o["kind"])
	if kind == "run":
		var to: Vector2 = o["target"] - f.pos
		if to.length() < 1.2:
			f.order = {}
			return
		f.want = to.normalized() * f.top_speed() * (0.95 if carrier == f else 1.1)
	elif kind == "press":
		if carrier != null and carrier.team == f.team and carrier != f:
			f.order = {}
			return
		var tgt := carrier.pos if carrier != null and carrier != f else _ball2()
		var to2 := tgt - f.pos
		f.want = to2.limit_length(f.top_speed() * 1.1) if to2.length() > 0.8 else Vector2.ZERO

# ---------------------------------------------------------------- cards
func _card_clip(c: Dictionary, fallback: String) -> String:
	var s := ""
	for ch in String(c["name"]).to_lower():
		s += ch if (ch >= "a" and ch <= "z") or (ch >= "0" and ch <= "9") else "_"
	var clip_name := "%s_%s" % [String(c["id"]).to_lower(), s]
	if selected != null and selected.node.has_clip(clip_name): return clip_name
	return fallback

func _play_card(i: int) -> void:
	if i >= hand.size() or phase != Phase.PLAY: return
	if selected == null:
		hud.toast("Pick a player first")
		return
	var c: Dictionary = hand[i]
	var id := String(c["id"])
	if float(cooldown.get(id, 0.0)) > 0.0:
		hud.toast("%s: cooling down" % c["name"])
		return
	var f := selected
	var ok := false
	var cat := String(c["cat"])
	var dirv := Vector2.ZERO
	if cat == "SHOT" or cat == "PASS" or cat == "DRIBBLE":
		if carrier != f:
			hud.toast("%s needs the ball" % c["name"])
			return
	if cat == "SHOT": ok = _card_shot(f, c, dirv)
	elif cat == "PASS": ok = _card_pass(f, c, dirv)
	elif cat == "DRIBBLE": ok = _card_dribble(f, c)
	elif cat == "DEFEND": ok = _card_defend(f, c)
	else:
		hud.toast("%s is not in this build" % c["name"])
		return
	if ok:
		cooldown[id] = Data.num(c["cd"], 3.0) * cooldown_scale
		hud.card_used(i)

func _roll(c: Dictionary, bonus: float) -> bool:
	return rng.randf() * 100.0 < Data.num(c["succ"], 70.0) + bonus

func _card_shot(f: Footballer, c: Dictionary, dirv: Vector2) -> bool:
	var curve := Data.num(c["ball_curve"])
	var style := "K01"
	if curve > 0.0: style = "K02"
	elif curve < 0.0: style = "K03"
	elif Data.num(c["ball_arc"]) >= 2.0: style = "K06"
	if String(c["name"]).findn("knuckle") >= 0: style = "K04"
	var good := _roll(c, (f.stat("SHO", 60) - 60) * 0.3)
	var spd := 14.0 + Data.num(c["ball_speed"], 5.0) * 2.6
	var noise := 1.5 if good else 8.0 + Data.num(c["risk"], 10.0) * 0.6
	if not good: spd *= 0.75
	var to := Vector2(HALF_L * f.team.dir + f.team.dir * 1.5, clampf(dirv.y * 3.0, -3.1, 3.1))
	hud.toast(String(c["name"]) if good else "%s: miscued" % c["name"])
	_act(f, _card_clip(c, "kick"), 0.4, func(): _launch(f, "shot", to, Vector2.ZERO, {"style": style, "speed": spd, "noise": noise}))
	return true

func _card_pass(f: Footballer, c: Dictionary, dirv: Vector2) -> bool:
	var tgt := _best_target(f, dirv)
	var to := f.pos + f.face * 18.0 if tgt == null else tgt.pos + tgt.vel * 0.5
	var dist := f.pos.distance_to(to)
	var arc := Data.num(c["ball_arc"])
	var style := "K07"
	var spd := clampf(dist * 0.85 + 6.0, 9.0, 26.0) * (1.0 + Data.num(c["ball_speed"], 4.0) * 0.03)
	if arc >= 2.0:
		style = "K05"
		spd = clampf(sqrt(dist * 10.3), 8.0, 30.0)
	elif String(c["name"]).findn("cross") >= 0:
		style = "K08"
	var good := _roll(c, (f.stat("PAS", 60) - 60) * 0.3)
	var noise := 1.0 if good else 10.0
	hud.toast(String(c["name"]) if good else "%s: scuffed" % c["name"])
	_act(f, _card_clip(c, "kick"), 0.4, func(): _launch(f, "lob" if style == "K05" else "pass", to, Vector2.ZERO, {"style": style, "speed": spd, "noise": noise}))
	return true

func _card_dribble(f: Footballer, c: Dictionary) -> bool:
	var good := _roll(c, (f.stat("DRI", 60) - 60) * 0.3)
	var clip_name := _card_clip(c, "")
	var dir := f.face
	if clip_name != "": _act(f, clip_name, 0.5, func(): pass)
	f.shield = 1.3
	f.vel = dir * 7.0
	if good:
		hud.toast(String(c["name"]))
	else:
		hud.toast("%s: lost it" % c["name"])
		carrier = null
		f.no_touch = 0.7
		ball.launch(ball.phys.pos, Vector3(dir.x, 0.0, dir.y), 4.0)
		ball.set_free()
	return true

func _card_defend(f: Footballer, c: Dictionary) -> bool:
	if carrier == null or carrier.team == f.team:
		hud.toast("%s: nobody to challenge" % c["name"])
		return false
	var reach := 3.0 + Data.num(c["reach"], 4.0) * 0.25
	if f.pos.distance_to(carrier.pos) > reach:
		hud.toast("%s: too far" % c["name"])
		return false
	var target := carrier
	var good := _roll(c, (f.stat("DEF", 60) - target.stat("DRI", 60)) * 0.3)
	f.vel = (target.pos - f.pos).normalized() * 6.5
	hud.toast(String(c["name"]) if good else "%s: missed" % c["name"])
	_act(f, _card_clip(c, "df01_stand_tackle"), 0.45, func(): _resolve_tackle(f, target, 1.0 if good else -1.0))
	return true

# ---------------------------------------------------------------- movement
func _move(dt: float) -> void:
	for f in all:
		f.no_touch = maxf(0.0, f.no_touch - dt)
		f.lock = maxf(0.0, f.lock - dt)
		f.shield = maxf(0.0, f.shield - dt)
		if not f.pending.is_null():
			f.pending_t -= dt
			if f.pending_t <= 0.0:
				var cb := f.pending
				f.pending = Callable()
				cb.call()
		var want := f.want if (f.lock <= 0.0 and phase == Phase.PLAY) else Vector2.ZERO
		f.vel = f.vel.move_toward(want, 32.0 * dt)
		f.pos += f.vel * dt
		f.pos.x = clampf(f.pos.x, -HALF_L - 3.0, HALF_L + 3.0)
		f.pos.y = clampf(f.pos.y, -HALF_W - 2.0, HALF_W + 2.0)
		if f.vel.length() > 0.5:
			f.face = f.face.lerp(f.vel.normalized(), clampf(dt * 14.0, 0.0, 1.0)).normalized()
		f.want = Vector2.ZERO
	for i in all.size():
		for j in range(i + 1, all.size()):
			var d := all[j].pos - all[i].pos
			var l := d.length()
			if l < 0.8 and l > 0.001:
				var push := d / l * (0.8 - l) * 0.5
				all[i].pos -= push
				all[j].pos += push
	for f in all:
		stadium.set_actor_pos(f.node, stadium.pitch_pos(Vector3(f.pos.x, 0.0, f.pos.y)))
		f.node.face_vector(f.face)
		if f.lock <= 0.0:
			var speed := f.vel.length()
			var want_clip := "base_idle"
			if speed > 6.0: want_clip = "base_sprint"
			elif speed > 3.2: want_clip = "base_jog"
			elif speed > 0.4: want_clip = "base_walk"
			if want_clip != f.clip and f.node.has_clip(want_clip):
				f.node.play_clip(want_clip)
				f.clip = want_clip

# ---------------------------------------------------------------- the ball
func _ball_logic(dt: float) -> void:
	if carrier != null:
		var c := carrier
		var spot := c.pos + c.face * 0.55
		ball.phys.pos = Vector3(spot.x, ball.phys.rad, spot.y)
		var v3 := Vector3(c.vel.x, 0.0, c.vel.y)
		ball.phys.vel = v3
		ball.live = false
		ball.preview_spin = v3.cross(Vector3.UP) / ball.phys.rad if v3.length() > 0.1 else Vector3.ZERO
		last_touch = c
		if phase == Phase.PLAY: _auto_tackles(dt)
		return
	if phase != Phase.PLAY: return
	var bp := ball.phys.pos
	var b2 := Vector2(bp.x, bp.z)
	var speed := ball.phys.vel.length()
	var best: Footballer = null
	var bd := 1.0
	for f in all:
		if f.no_touch > 0.0: continue
		var reach := 0.9
		var max_h := 1.3
		if f.is_keeper():
			reach = 1.6 + f.stat("REF", 60) * 0.012
			max_h = 2.5
		if bp.y > max_h: continue
		var d := f.pos.distance_to(b2) / reach
		if d < bd:
			bd = d; best = f
	if best == null: return
	if best.is_keeper():
		var limit_k := 14.0 + best.stat("HAN", 60) * 0.25
		if speed <= limit_k:
			_take(best)
		else:
			ball.phys.vel = Vector3(-ball.phys.vel.x * 0.3, ball.phys.vel.y * 0.5 + 2.0, ball.phys.vel.z + rng.randf_range(-5.0, 5.0))
			best.no_touch = 0.5
			last_touch = best
		return
	var limit := (11.0 + best.stat("DRI", 60) * 0.13) * ball.touch()
	if speed <= limit:
		_take(best)
	else:
		ball.phys.vel *= 0.45
		best.no_touch = 0.4
		last_touch = best

func _boundaries() -> void:
	var bp := ball.phys.pos
	if absf(bp.x) > HALF_L + 0.2:
		if absf(bp.z) < GOAL_HALF and bp.y < BAR + ball.phys.rad:
			_goal(home if bp.x > 0.0 else away)
		elif absf(bp.x) > HALF_L + 0.6:
			_restart_out(bp)
	elif absf(bp.z) > HALF_W + 0.3:
		_restart_out(bp)
