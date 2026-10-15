class_name AiInteract
extends Resource
## The interaction layer: what makes the team play TOGETHER rather than every player following his own spot. It runs after each role / formation has decided (AiBrain calls compute() once
## per team per frame and post() for every player) and adjusts the movement. Everything is an export (AiProfile > Interact):
##  Cover: when a back-line player steps out (the closest man, or anyone that gets `step_gap` metres ahead of the line) or a holding midfielder presses, the nearest team mate
##   falls in behind him on the vacated side, and the rest of the back line slides across towards that side.
##  Outlet: when one of our midfielders presses the carrier, our striker sees it and goes looking for free space ahead (the counter outlet) instead of holding his line.
##  Traits: personal habits (AiTrait, players.csv `traits`), e.g. the roamer who walks in space ahead of the ball while the team defends.

@export_group("Cover")
@export var cover_enabled := true
## a back-line player this far ahead of the line's average counts as pushed out
@export var step_gap := 7.0
## the cover stands this far behind the player who stepped out
@export var cover_behind := 6.0
## and this much of the way across towards him (0 = in his own lane, 1 = right behind)
@export_range(0.0, 1.0) var cover_lateral := 0.55
## the rest of the back line slides this fraction of the way towards the side of the push
@export_range(0.0, 1.0) var compress := 0.25
## the cover runs at full speed when he is further than this from his cover spot
@export var cover_sprint_distance := 6.0
## roles that can cover and roles that count as the "back line"
@export var cover_roles := PackedStringArray(["CB", "LB", "RB", "CDM", "CM"])
@export var back_line_roles := PackedStringArray(["CB", "LB", "RB"])
## when one of these presses, a cover is assigned too (a holding midfielder stepping up leaves the centre open)
@export var midfield_pusher_roles := PackedStringArray(["CDM", "CM"])

@export_group("Outlet (counter)")
@export var outlet_enabled := true
## the striker(s) that start looking for space when one of ours presses
@export var outlet_roles := PackedStringArray(["ST"])
## presser roles that trigger it
@export var outlet_presser_roles := PackedStringArray(["CDM", "CM", "CAM", "LB", "RB", "CB"])
## the free space is searched around a point this far ahead of the ball, on the side away from the ball (0.5 = half way across)
@export var outlet_ahead := 12.0
@export_range(0.0, 1.0) var outlet_cross := 0.5
@export var outlet_radius := 12.0
## he looks again this often (seconds)
@export var outlet_retarget := 0.5
## stays level with or behind the last defender by this much (does not drift offside)
@export var onside_margin := 1.0
## free space = far from opponents (up to this many metres counts) + a little for going forward
@export var space_cap := 14.0
@export var space_forward_weight := 0.12

@export_group("Traits")
## trait definitions; a player has them through players.csv > traits
@export var traits: Array[AiTrait] = []

func fill() -> AiInteract:
	if traits.is_empty(): traits = AiTrait.defaults()
	return self

# ---------------------------------------------------------------- traits
func trait_of(f: Footballer) -> AiTrait:
	var raw := str(f.row.get("traits", ""))
	if raw == "": return null
	for id in raw.replace("|", " ").split(" ", false):
		for t in traits:
			if t != null and t.id == id: return t
	return null

## a roamer is never the one sent to close the ball down
func exempt_press(f: Footballer) -> bool:
	var t := trait_of(f)
	return t != null and t.exempt_press

# ---------------------------------------------------------------- once per team per frame
func compute(c: AiContext) -> void:
	c.cover.clear()
	c.pushers.clear()
	c.push_y = 0.0
	c.outlet = null
	if c.has_ball or c.carrier == null: return
	if cover_enabled: _compute_cover(c)
	if outlet_enabled and c.presser != null and c.presser.role in outlet_presser_roles: c.outlet = c.presser

func _compute_cover(c: AiContext) -> void:
	var back: Array = []
	var mean_t := 0.0
	for f in c.team.players:
		if f.role in back_line_roles:
			back.append(f)
			mean_t += f.pos.x * c.dir
	if back.is_empty(): return
	mean_t /= back.size()
	for f in c.team.players:
		if f.is_keeper() or not f.order.is_empty(): continue
		var pushed := false
		if f.role in back_line_roles: pushed = c.presser == f or f.pos.x * c.dir - mean_t > step_gap
		elif f.role in midfield_pusher_roles: pushed = c.presser == f
		if pushed: c.pushers.append(f)
	if c.pushers.is_empty(): return
	var sum_y := 0.0
	var taken := {}
	for p in c.pushers:
		sum_y += p.pos.y
		var v := Vector2(p.pos.x - c.dir * cover_behind, lerpf(p.slot.y, p.pos.y, 0.5))
		var best: Footballer = null
		var bs := 1e9
		for m in c.team.players:
			if m.is_keeper() or c.pushers.has(m) or taken.has(m) or not m.order.is_empty() or not (m.role in cover_roles): continue
			var sc := m.pos.distance_to(v) + (0.0 if m.pos.x * c.dir <= p.pos.x * c.dir else 6.0)
			if sc < bs:
				bs = sc
				best = m
		if best != null:
			taken[best] = true
			c.cover[best] = c.clamp_pitch(Vector2(v.x, lerpf(best.pos.y, v.y, cover_lateral)), 2.0)
	c.push_y = sum_y / c.pushers.size()

# ---------------------------------------------------------------- per player, after the role has decided
func post(f: Footballer, i: AiIntent, c: AiContext) -> void:
	if i == null or i.move_to == Vector2.INF or i.action != "": return
	if c.carrier == f or (c.game.pass_target == f and c.carrier == null): return
	var tr := trait_of(f)
	if not c.has_ball and c.carrier != null:
		if c.cover.has(f):
			i.move_to = c.cover[f]
			i.speed = c.s.sprint_factor if f.pos.distance_to(i.move_to) > cover_sprint_distance else c.s.jog_factor
			return
		if not c.pushers.is_empty() and f.role in back_line_roles and not c.pushers.has(f):
			i.move_to.y = lerpf(i.move_to.y, c.push_y, compress)
	if tr != null and _trait(f, i, c, tr): return
	if c.outlet != null and f.role in outlet_roles and c.presser != f:
		var ball_t := c.ball.x * c.dir
		var centre := Vector2((ball_t + outlet_ahead) * c.dir, lerpf(f.pos.y, -c.ball.y, outlet_cross))
		i.move_to = _space(f, c, c.clamp_pitch(centre, 2.0), outlet_radius, outlet_retarget)
		i.speed = c.s.jog_factor

## returns true when the trait decided the movement
func _trait(f: Footballer, i: AiIntent, c: AiContext, tr: AiTrait) -> bool:
	if not c.has_ball:
		if c.carrier == null: return false      # a loose ball: the role decides
		var t := maxf(c.ball.x * c.dir + tr.counter_ahead, tr.counter_min_x)
		var centre := Vector2(t * c.dir, lerpf(f.slot.y, c.ball.y, tr.lateral_pull))
		i.move_to = _space(f, c, c.clamp_pitch(centre, 2.0), tr.counter_radius, tr.roam_retarget)
		i.speed = tr.walk_factor
		return true
	if tr.roam_in_attack:
		i.move_to = _space(f, c, i.move_to, tr.roam_radius, tr.roam_retarget)
		i.speed = c.s.sprint_factor if c.poss_time < tr.sprint_after_win else c.s.jog_factor
		return true
	return false

## the freest spot within `radius` of `centre` (far from opponents, level with the last defender at most), kept for `retarget` seconds so the player does not jitter
func _space(f: Footballer, c: AiContext, centre: Vector2, radius: float, retarget: float) -> Vector2:
	var memo: Dictionary = f.ai.get("space", {})
	var now := Time.get_ticks_msec() / 1000.0
	if memo.has("t") and now - float(memo["t"]) < retarget and (memo["c"] as Vector2).distance_to(centre) < radius * 0.6:
		return memo["spot"]
	var last_t := -1e9
	for o in c.other.players:
		if not o.is_keeper(): last_t = maxf(last_t, o.pos.x * c.dir)
	var best := centre
	var bs := -1e9
	for ring in 2:
		for k in 8:
			var a := TAU * k / 8.0 + ring * 0.4
			var p := centre + Vector2(cos(a), sin(a)) * radius * (0.5 + 0.5 * ring)
			p = c.clamp_pitch(p, 2.0)
			if p.x * c.dir > last_t + onside_margin: p.x = (last_t + onside_margin) * c.dir
			var sc := minf(c.pressure(p), space_cap) + (p.x - f.pos.x) * c.dir * space_forward_weight - 0.02 * p.distance_to(centre)
			if sc > bs:
				bs = sc
				best = p
	f.ai["space"] = {"t": now, "c": centre, "spot": best}
	return best
