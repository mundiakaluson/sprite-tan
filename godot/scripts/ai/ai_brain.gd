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
	for f in g.all:
		if f.lock > 0.0: continue
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
		if f.is_keeper() or f.lock > 0.0 or profiles[t].interact.exempt_press(f): continue
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
	match i.action:
		"pass", "through", "lob":
			if i.target != null: g.poss.kick_action(f, i.action, i.target.pos, i.target.vel, {}, i.target)
			elif i.aim != Vector2.INF: g.poss.kick_action(f, i.action, i.aim)
		"shoot":
			g.poss.kick_action(f, "shot", i.aim, Vector2.ZERO, {})
		"smother": g.keeper.smother(f, i.target)
		"takeon": g.dribble.take_on(f, i.target)
		"slide": g.dribble.slide_tackle(f, i.target)
		"tackle":
			if i.target != null and g.carrier == i.target and f.lock <= 0.0 and f.no_touch <= 0.0:
				var won := g.rng.randf() < clampf(0.5 + (f.stat("DEF", 60) - i.target.stat("DRI", 60)) * 0.01, 0.15, 0.85)
				g.poss.start_tackle(f, i.target, won)
