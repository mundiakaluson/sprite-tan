class_name AiBrain
extends RefCounted
## Runs the AI for every player the human is not ordering: works out the team phase, picks the presser, asks the role's AiRole what each player wants
## (an AiIntent) and applies it (movement, passes, shots). The roles are Resources (scripts/ai/roles/, one file each) collected in an AiProfile, so all their numbers are in the inspector; add a role by adding a field to AiProfile.

enum Phase { BUILD_UP, PROGRESS, FINAL_THIRD, ORGANISE, PRESS, TRANSITION }

var g: MatchGame
var profiles := {}  ## Team -> AiProfile (MatchSettings > AI: home_ai / away_ai; a missing one uses the role defaults)
var ctx := {}       ## Team -> AiContext

func _init(game: MatchGame) -> void:
	g = game
	profiles = {g.home: (g.settings.home_ai if g.settings.home_ai != null else AiProfile.new()).fill(), g.away: (g.settings.away_ai if g.settings.away_ai != null else AiProfile.new()).fill()}
	for t in g.teams:
		var c := AiContext.new()
		c.setup(g, t)
		c.profile = profiles[t]
		ctx[t] = c

func update(dt: float) -> void:
	for t in g.teams:
		_phase(ctx[t])
	for t in g.teams:
		ctx[t].tick(dt)
		profiles[t].interact.compute(ctx[t])
		profiles[t].line.compute(ctx[t], dt)
		profiles[t].transition.compute(ctx[t], dt)
	for f in g.all:
		if f.lock > 0.0: continue
		if g.phase == MatchGame.Phase.RESTART and g.rules.taker == f: continue          # the taker waits on the ball until the restart is ready
		if not f.order.is_empty() and not f.is_keeper():
			g.orders.follow(f, dt)
			continue
		if f.is_keeper() and String(f.order.get("kind", "")) == "rush":           # the human sent the keeper out
			f.order["t"] = float(f.order["t"]) - dt
			var c0: AiContext = ctx[f.team]
			if f.order["t"] <= 0.0 or c0.carrier == null or c0.carrier.team == f.team:
				f.order = {}
			else:
				var gk: AiRole = profiles[f.team].role_for(f.role)
				if gk is AiGk:
					_apply(f, (gk as AiGk).rush(f, c0), c0)
					continue
		var role: AiRole = profiles[f.team].role_for(f.role)
		var intent := role.think(f, ctx[f.team], dt)
		profiles[f.team].interact.post(f, intent, ctx[f.team])
		profiles[f.team].transition.post(f, intent, ctx[f.team])
		profiles[f.team].line.post(f, intent, ctx[f.team])
		_apply(f, intent, ctx[f.team])

## the stance a team plays right now: the HUD's choice, or for "auto" the profile's rules (protect a lead late, press when behind)
func _stance(c: AiContext) -> TeamStance:
	var p: AiProfile = profiles[c.team]
	var id := c.team.stance_id
	if id == "auto": id = p.auto_stance_id(g.clock / 60.0, c.team.score - c.other.score)
	return p.stance_for(id)

## the TEAM buttons of a side: [{id, label, note}]
func stance_list(t: Team) -> Array:
	var out: Array = []
	for s in profiles[t].stances: out.append({"id": s.id, "label": s.label, "note": s.note})
	return out

func _phase(c: AiContext) -> void:
	c.set_stance(_stance(c))
	c.refresh()
	var t := c.team
	var depth := c.depth(c.ball)
	if c.has_ball:
		c.phase = Phase.BUILD_UP if depth < 0.5 - g.settings.third_line / Stadium.L else (Phase.FINAL_THIRD if depth > 0.5 + g.settings.third_line / Stadium.L else Phase.PROGRESS)
		c.presser = null
		return
	c.phase = Phase.TRANSITION if c.carrier == null else (Phase.PRESS if depth > 0.5 and c.f("press") > g.settings.press_line else Phase.ORGANISE)
	# the nearest outfield player (to the carrier, or to the ball) closes down; the intended receiver of our own pass is never a presser
	var tgt := c.carrier.pos if c.carrier != null else c.ball
	c.presser = null
	var bd := 1e9
	for f in t.players:
		if f.is_keeper() or f.lock > 0.0 or profiles[t].interact.exempt_press(f) or g.offside.aware(f): continue
		var d := f.pos.distance_to(tgt)
		if d < bd:
			bd = d
			c.presser = f

func _apply(f: Footballer, i: AiIntent, c: AiContext) -> void:
	var top := f.top_speed()
	if i.move_to != Vector2.INF:
		var to := i.move_to - f.pos
		var d := to.length()
		f.want = to / d * minf(top * i.speed, d * 2.0) if d > 0.4 else Vector2.ZERO
	if g.engage.frozen() and (g.engage.busy(f) or (i.target != null and g.engage.busy(i.target))): return      # the two in an engagement wait for the picks
	match i.action:
		"pass", "through", "lob":
			if i.target != null:
				if i.action == "through":                                       # the runner sets off when the ball is struck (a smart one curls round defenders)
					var mate := i.target
					var dir := mate.vel.normalized() if mate.vel.length() > 1.0 else Vector2(f.team.dir, 0.0)
					if dir.x * f.team.dir < 0.2: dir = Vector2(f.team.dir, 0.0)
					var plan := g.orders.plan_run(mate, dir, f)
					g.kicking.after_release(f, func(): g.orders.send_runner(f, mate, Vector2(f.team.dir * g.settings.through_run_speed, 0.0), plan))
					if plan.has("curve"):
						var over := i.over.duplicate()
						over["_to_space"] = true
						over["speed"] = plan["speed"]
						g.poss.kick_action(f, i.action, plan["meet"], Vector2.ZERO, over, i.target)
						return
				if i.action in ["pass", "through"]:                             # a clever passer bends it round a defender in the lane (MatchSettings > Bent passes)
					var lead := Data.num(Data.row("ball_actions", i.action).get("lead"), 0.5)
					var curl := g.orders.plan_curl(f, i.target.pos + i.target.vel * lead, i.action)
					if not curl.is_empty():
						var ov := i.over.duplicate()
						ov["_to_space"] = true
						ov["style"] = curl["style"]
						ov["speed"] = curl["speed"]
						g.poss.kick_action(f, i.action, curl["aim"], Vector2.ZERO, ov, i.target)
						return
				g.poss.kick_action(f, i.action, i.target.pos, i.target.vel, i.over, i.target)
			elif i.aim != Vector2.INF: g.poss.kick_action(f, i.action, i.aim)
		"shoot":
			if c.countering: AiTransition.stat_counter_shots += 1
			var over := {}
			if i.style != "": over["style"] = i.style
			if i.clip != "": over["_clip"] = i.clip
			if i.speed_override > 0.0: over["speed"] = i.speed_override
			g.poss.kick_action(f, "shot", i.aim, Vector2.ZERO, over)
		"smother": g.keeper.smother(f, i.target)
		"gesture":                                                              # a keeper's gesture with the ball in his hands (AiKeeperGesture)
			if f.lock <= 0.0 and i.clip != "":
				if i.target != null and i.target.pos.distance_to(f.pos) > 0.5: f.face = (i.target.pos - f.pos).normalized()
				f.want = Vector2.ZERO
				g.motion.act(f, i.clip, 0.9, func(): pass, 0.0, i.speed_override)
		"takeon":                                                                 # a duel: the engagement director may freeze it for card picks
			if not g.engage.duel(f, i.target, f, "takeon"): g.dribble.take_on(f, i.target)
		"slide":
			if not g.engage.duel(i.target, f, f, "slide"): g.dribble.slide_tackle(f, i.target)
		"tackle":
			if i.target != null and g.carrier == i.target and f.lock <= 0.0 and f.no_touch <= 0.0 and not g.engage.duel(i.target, f, f, "tackle"):
				var won := g.rng.randf() < clampf(0.5 + (f.stat("DEF", 60) - i.target.stat("DRI", 60)) * 0.01, 0.15, 0.85)
				g.poss.start_tackle(f, i.target, won)

## headless counters of the team-play layers
func stats() -> Dictionary:
	return {"traps": AiLine.stat_traps, "line_drop_frames": AiLine.stat_drops, "line_squeeze_frames": AiLine.stat_squeezes,
		"counter_presses": AiTransition.stat_cp, "cp_regains": AiTransition.stat_cp_regain, "counters": AiTransition.stat_counters, "counter_shots": AiTransition.stat_counter_shots,
		"recovery_sprint_frames": AiTransition.stat_recover_frames}
