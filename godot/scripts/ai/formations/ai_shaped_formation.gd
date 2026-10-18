class_name AiShapedFormation
extends AiFormation
## Shared team play of the formations after tactico.pro/formations/<name> (4-3-3, 4-2-3-1, 4-1-4-1, 4-3-2-1, diamond, 3-5-2, 3-4-3, 5-3-2, 5-4-1). One small file per formation
## extends this and has no numbers of its own: each formation's numbers are set on its resource in scenes/ai/profile_default.tres (AiProfile > Formations), every one an export with a tooltip.
## The rules (all from the tactico pages):
##  Defending: the team stands in lines (back line, midfield line, front line) that trail the ball by fixed gaps and slide with it. Nobody presses without a trigger
##   (back pass to a CB / GK, ball to a full back on the touchline, receiver facing his own goal); on a trigger the presser closes down and the striker takes the passing lane back.
##  Attacking: build-up splits the centre backs and a holding midfielder drops between them; full backs / wing-backs push up (one goes, one stays); of the central midfielders one goes forward
##   and one holds behind the ball; wide players hold the width (inside forwards cut in); the striker pins the last defender; a 10 works between the lines.
## Everything reads the stance (block_shift, press_always, press_never) and returns null for what it does not cover, so the role AI plays.

@export_group("Block (defending)")
## back line stands this far behind the ball, never deeper than back_min / higher than back_max (metres from the centre, team frame)
@export var back_trail := 28.0
@export var back_min := -34.0
@export var back_max := 6.0
## back line to midfield line, and midfield line to the front line
@export var gap_back_mid := 12.0
@export var gap_mid_st := 14.0
## midfield and front line never stand further up than the ball plus this
@export var ahead_of_ball := 6.0
## the holding midfielder sits this much deeper than the midfield line
@export var holder_drop := 5.0
## 0 = a 10 stands on the midfield line, 1 = on the front line
@export_range(0.0, 1.0) var between_lines := 0.5
## midfielders stand this fraction of their slot width when defending (narrow block)
@export_range(0.4, 1.2) var mid_narrow := 1.0
## winger / inside forward: which line he defends on (1 = drops into the midfield four, 2 = stays high with the striker)
@export_range(1, 2) var wide_forward_line := 2

@export_group("Press triggers")
@export var trigger_fullback := true
@export var trigger_back_pass := true
@export var trigger_facing_own_goal := true
## when the carrier is closer to our goal than this (0..1 of the pitch) we close down anyway
@export_range(0.0, 1.0) var block_depth := 0.45
@export var trigger_window := 2.0
## without a trigger the closest man stands this far goal-side of the carrier
@export var contain_distance := 6.0
## on a trigger the striker stands this far from the carrier towards the nearest centre back / pivot (the cover shadow)
@export var cover_shadow := 4.0
## the holding midfielder never presses: he delays and forces the ball wide
@export var holder_contains := false

@export_group("Centre backs")
## stoppers step out to an attacker who comes within this distance of them
@export var step_out_range := 10.0
@export var step_out_goal_side := 2.0
## a sweeper stays this much deeper than the back line
@export var sweeper_depth := 4.0
## attacking: the back line follows the ball with this trail
@export var attack_back_trail := 30.0
## build-up: centre backs spread to this multiple of their slot width
@export var build_split := 1.3
## build-up: the holding midfielder drops between the centre backs, this far in front of the line (negative = level)
@export var pivot_gap := 3.0

@export_group("Full backs and wing-backs")
## build-up: they push up this far
@export var build_push := 10.0
## one goes, one stays: the one on the far side from the ball stays as the spare defender
@export var one_goes_one_stays := true
## they overlap / underlap the winger in front of them
@export var overlap_ahead := 8.0
@export var overlap_z := 30.0
@export var underlap_ahead := 4.0
@export var underlap_z := 18.0
@export var wide_hold_z := 24.0
## a wing-back (no winger in front of him) goes this far beyond the ball line in attack, on the touchline
@export var wingback_ahead := 14.0

@export_group("Wide players")
## hold the width at this distance from the centre line
@export var width_z := 28.0
## inside forwards cut in to this line when the ball is on their side
@export var inside_z := 14.0
@export var far_post_when_far := true

@export_group("Midfield")
## the holder stands this far behind the ball while the other central midfielders go
@export var holder_behind := 8.0
## the runner arrives late at the edge of the box, this far across (cut-back)
@export var late_z := 8.0

@export_group("Front players")
## the striker pins the last defender: this far in front of him
@export var shoulder_gap := 1.0
## a second striker / the 10 drops into the pocket, this far in front of the last defender
@export var pocket_depth := 12.0
@export var channel_z := 11.0

func think(f: Footballer, c: AiContext, role: AiRole, _dt: float) -> AiIntent:
	if c.carrier == f: return null
	if c.game.pass_target == f and c.carrier == null: return null
	if c.has_ball: return _attack(f, c, role)
	if c.carrier != null: return _defend(f, c, role)
	return null

# ---------------------------------------------------------------- helpers
func _go(c: AiContext, spot: Vector2, speed: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = c.clamp_pitch(spot, 1.5)
	i.speed = speed
	return i

func _ball_t(c: AiContext) -> float:
	return c.ball.x * c.dir

func _last_defender_t(c: AiContext) -> float:
	var best := -1e9
	for o in c.other.players:
		if not o.is_keeper(): best = maxf(best, o.pos.x * c.dir)
	return best

## x (team frame) of a line: 0 back, 1 midfield, 2 front
func _block_x(c: AiContext, line: int, trail: float) -> float:
	var back := clampf(clampf(_ball_t(c) - trail, back_min, back_max) + c.stance.block_shift + (0.0 if c.has_ball else c.line_shift), -45.0, 40.0)
	if not c.has_ball: back = maxf(back, c.line_floor_t)                # AiLine: the line steps up / drops as one, never below its floor
	var x := back
	if line >= 1: x = minf(back + gap_back_mid, _ball_t(c) + ahead_of_ball)
	if line >= 2: x = minf(back + gap_back_mid + gap_mid_st, _ball_t(c) + ahead_of_ball)
	return minf(x, 50.0)

func _mates(c: AiContext, role_name: String) -> Array:
	var out: Array = []
	for m in c.team.players:
		if m.role == role_name: out.append(m)
	return out

func _nearest_to_ball(list: Array, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bd := 1e9
	for m in list:
		var d: float = m.pos.distance_to(c.ball)
		if d < bd:
			bd = d
			best = m
	return best

func _pressing_trigger(c: AiContext) -> bool:
	var k := c.carrier
	if k == null or k.hold > trigger_window: return false
	if trigger_fullback and (k.role == "LB" or k.role == "RB"): return true
	if trigger_back_pass and (k.role == "GK" or k.role == "CB") and c.depth(k.pos) > 0.5: return true
	if trigger_facing_own_goal and k.face.x * c.dir > 0.3 and c.depth(k.pos) > 0.5: return true
	return false

func _side(f: Footballer) -> float:
	var s := signf(f.slot.y)
	return s if s != 0.0 else 1.0

## the winger / wide midfielder on the same side, for the overlap decision
func _wide_mate(f: Footballer, c: AiContext) -> Footballer:
	for m in c.team.players:
		if (m.role == "LW" or m.role == "RW") and signf(m.slot.y) == signf(f.slot.y): return m
	return null

## the full back / wing-back who stays: the one further from the ball (only when both are on the pitch)
func _stays_home(f: Footballer, c: AiContext) -> bool:
	if not one_goes_one_stays: return false
	var backs := _mates(c, "LB") + _mates(c, "RB")
	if backs.size() < 2: return false
	var near := backs[0] as Footballer
	for b in backs:
		if absf(b.pos.y - c.ball.y) < absf(near.pos.y - c.ball.y): near = b
	return near != f

func _is_wide_forward(f: Footballer) -> bool:
	return f.role == "LW" or f.role == "RW"

# ---------------------------------------------------------------- we have the ball
func _attack(f: Footballer, c: AiContext, role: AiRole) -> AiIntent:
	var spot := role.home_spot(f, c)
	var side := _side(f)
	var building := c.phase == AiBrain.Phase.BUILD_UP
	match f.role:
		"CB":
			if f.style == "sweeper": spot.x = (_block_x(c, 0, attack_back_trail) - sweeper_depth) * c.dir
			elif building: spot.y *= build_split
			else: spot.x = _block_x(c, 0, attack_back_trail) * c.dir
		"CDM":
			spot = _attack_cdm(f, c, spot, building)
		"LB", "RB":
			if _stays_home(f, c):
				spot.x = _block_x(c, 0, attack_back_trail) * c.dir
			elif building:
				spot.x += c.dir * build_push
			else:
				var wm := _wide_mate(f, c)
				if wm != null:
					var holds := absf(wm.pos.y) > wide_hold_z
					var ahead := wm.pos.x * c.dir + (overlap_ahead if holds else underlap_ahead)
					spot = Vector2(maxf(spot.x * c.dir, ahead) * c.dir, side * (overlap_z if holds else underlap_z))
				elif f.style == "wingback":
					spot = Vector2(maxf(spot.x * c.dir, minf(_ball_t(c) + wingback_ahead, 48.0)) * c.dir, side * width_z)
		"LW", "RW":
			spot = _attack_wide(f, c, spot, side)
		"CM":
			spot = _attack_cm(f, c, spot)
		"CAM":
			spot = _attack_cam(f, c, spot)
		"ST":
			spot = _attack_st(f, c, spot)
		_:
			return null
	return _go(c, spot, c.s.jog_factor)

## one holding midfielder: drops between the centre backs in build-up, then stays behind the ball. A double pivot: the deeper one drops / holds, the other may step forward with the ball
func _attack_cdm(f: Footballer, c: AiContext, spot: Vector2, building: bool) -> Vector2:
	var pair := _mates(c, "CDM")
	var holder := true
	if pair.size() >= 2:
		var deeper := pair[0] as Footballer
		for m in pair:
			if m.pos.x * c.dir < deeper.pos.x * c.dir: deeper = m
		holder = deeper == f
	if holder:
		if building: return Vector2((_block_x(c, 0, attack_back_trail) + pivot_gap) * c.dir, spot.y * 0.35)
		return Vector2(minf(spot.x * c.dir, _ball_t(c) - holder_behind) * c.dir, spot.y * 0.6)
	if building: return spot
	return Vector2(minf(spot.x * c.dir + 6.0, _ball_t(c) - 2.0) * c.dir, spot.y)

func _attack_wide(f: Footballer, c: AiContext, spot: Vector2, side: float) -> Vector2:
	spot.y = side * width_z
	if f.style == "inside_forward" and signf(c.ball.y) == side and c.phase != AiBrain.Phase.BUILD_UP: spot.y = side * inside_z
	if far_post_when_far and c.phase == AiBrain.Phase.FINAL_THIRD and signf(c.ball.y) == -side and absf(c.ball.y) > 12.0:
		spot = c.spot("far_post_left" if side < 0.0 else "far_post_right")
	return spot

## the central midfielders (not the holder): the one nearer the ball goes forward, the rest hold behind the ball
func _attack_cm(f: Footballer, c: AiContext, spot: Vector2) -> Vector2:
	var pair := _mates(c, "CM")
	var goer := _nearest_to_ball(pair, c)
	if pair.size() < 2 or goer == f:
		if c.phase == AiBrain.Phase.FINAL_THIRD and c.carrier != null:
			var edge := c.spot("opp_box_edge")
			return Vector2(edge.x, -signf(c.carrier.pos.y if c.carrier.pos.y != 0.0 else 1.0) * late_z)
		return spot
	return Vector2(minf(spot.x * c.dir, _ball_t(c) - holder_behind) * c.dir, spot.y * 0.6)

## the 10 (or two 10s): between the lines; with two, the nearer one takes the pocket and the other runs beyond the striker
func _attack_cam(f: Footballer, c: AiContext, spot: Vector2) -> Vector2:
	var last_t := _last_defender_t(c)
	var pair := _mates(c, "CAM")
	var pocket := Vector2((last_t - pocket_depth) * c.dir, lerpf(spot.y, c.ball.y, 0.35))
	if pair.size() >= 2 and _nearest_to_ball(pair, c) != f:
		return Vector2(minf(last_t - shoulder_gap, 51.0) * c.dir, spot.y)
	if c.phase == AiBrain.Phase.BUILD_UP: return Vector2(minf(spot.x * c.dir, last_t - pocket_depth - 6.0) * c.dir, spot.y)
	return pocket

func _attack_st(f: Footballer, c: AiContext, spot: Vector2) -> Vector2:
	var last_t := _last_defender_t(c)
	var shoulder := Vector2(minf(last_t - shoulder_gap, 51.0) * c.dir, spot.y)
	if c.phase == AiBrain.Phase.BUILD_UP: return shoulder
	var pair := _mates(c, "ST")
	if pair.size() >= 2 and _nearest_to_ball(pair, c) == f:
		return Vector2((last_t - pocket_depth - 2.0) * c.dir, spot.y * 0.5)
	if absf(c.ball.y) > 14.0: shoulder.y = signf(c.ball.y) * channel_z
	return shoulder

# ---------------------------------------------------------------- they have the ball
func _defend(f: Footballer, c: AiContext, role: AiRole) -> AiIntent:
	var carrier := c.carrier
	var triggered := _pressing_trigger(c) or c.stance.press_always
	if c.presser == f:
		var may_press := not c.stance.press_never and (triggered or c.depth(carrier.pos) <= block_depth) and not (holder_contains and f.role == "CDM")
		if may_press: return null
		return _go(c, carrier.pos + (c.own_goal() - carrier.pos).normalized() * contain_distance, c.s.jog_factor)
	if triggered and f.role == "ST":
		var cover := _cover_target(c)
		if cover != null:
			return _go(c, carrier.pos + (cover.pos - carrier.pos).normalized() * cover_shadow, c.s.sprint_factor)
	var home := role.home_spot(f, c)
	var t := _defend_line_x(f, c)
	if t == INF: return null
	if f.role == "CB" and f.style == "stopper":
		var st := _striker_near(f, c)
		if st != null: return _go(c, st.pos + (c.own_goal() - st.pos).normalized() * step_out_goal_side, c.s.sprint_factor)
	var y := home.y
	if f.role in ["CM", "CDM", "CAM"]: y *= mid_narrow
	var urgent := c.line_urgent and f.role in ["CB", "LB", "RB"]                # the line steps / drops at a run, together
	return _go(c, Vector2(t * c.dir, y), c.s.sprint_factor if urgent else c.s.jog_factor)

## where (team frame x) the player stands when they have the ball; INF = not covered
func _defend_line_x(f: Footballer, c: AiContext) -> float:
	match f.role:
		"CB":
			var x := _block_x(c, 0, back_trail)
			return x - sweeper_depth if f.style == "sweeper" else x
		"LB", "RB": return _block_x(c, 0, back_trail)
		"CDM": return _block_x(c, 1, back_trail) - holder_drop
		"CM": return _block_x(c, 1, back_trail)
		"CAM": return lerpf(_block_x(c, 1, back_trail), _block_x(c, 2, back_trail), between_lines)
		"LW", "RW": return _block_x(c, wide_forward_line if f.style != "wide_mid" else 1, back_trail)
		"ST": return _block_x(c, 2, back_trail)
	return INF

func _cover_target(c: AiContext) -> Footballer:
	var best: Footballer = null
	var bd := 1e9
	for o in c.other.players:
		if o == c.carrier or not (o.role == "CB" or o.role == "CDM" or o.role == "GK"): continue
		var d := o.pos.distance_to(c.carrier.pos)
		if d < bd:
			bd = d
			best = o
	return best

func _striker_near(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bd := step_out_range
	for o in c.other.players:
		if o.role != "ST" and o.role != "CAM": continue
		var d := o.pos.distance_to(f.pos)
		if d < bd and o.pos.x * c.dir < f.pos.x * c.dir + 4.0 and signf(o.pos.y - f.pos.y) != 0.0:
			bd = d
			best = o
	return best
