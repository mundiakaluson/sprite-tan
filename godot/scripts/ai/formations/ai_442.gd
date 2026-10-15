class_name Ai442
extends AiFormation
## 4-4-2 (F01), after tactico.pro/formations/4-4-2. Two banks of four and two strikers who work as a pair.
##  Defending: back four, midfield four and strikers keep set distances to each other and move with the ball (mid block). Nobody presses without a trigger.
##  Attacking: the back line follows the ball up; wide midfielders hold the width and the full back overlaps (or underlaps when the winger comes inside);
##   only one central midfielder goes forward, the other stays behind the ball; one striker drops into the pocket, the other stays on the last defender's shoulder.
## Roles: LB/RB = full backs, CB, LW/RW = wide midfielders, CM x2, ST x2. All numbers are exports (metres unless said).

@export_group("Block (defending)")
## the back line stands this far behind the ball (it never goes deeper than back_min or higher than back_max, metres from the centre in the team's frame)
@export var back_trail := 28.0
@export var back_min := -34.0
@export var back_max := 6.0
## distance back line to midfield line, and midfield line to the strikers
@export var gap_back_mid := 12.0
@export var gap_mid_st := 14.0
## midfield and strikers never stand further up than the ball plus this
@export var ahead_of_ball := 6.0
## the holding central midfielder sits this much deeper than the midfield line
@export var holder_drop := 3.0

@export_group("Press triggers")
## no press from the strikers' end of the pitch without one of these. When the carrier is closer to our goal than block_depth (0..1 of the pitch) we close down anyway.
@export var trigger_fullback := true
@export var trigger_back_pass := true
@export var trigger_facing_own_goal := true
@export_range(0.0, 1.0) var block_depth := 0.45
## a carrier who has held the ball longer than this is no longer a trigger (he has settled)
@export var trigger_window := 2.0
## without a trigger the closest man jogs and stands this far goal-side of the carrier
@export var contain_distance := 6.0
## on a trigger the other striker takes the passing lane back: he stands this far from the carrier towards the nearest centre back / pivot
@export var cover_shadow := 4.0

@export_group("Centre backs")
## the stopper steps out to a striker who comes within this distance of his spot, standing this far goal-side
@export var step_out_range := 10.0
@export var step_out_goal_side := 2.0
## attacking: the back line follows the ball with this trail (metres behind it)
@export var attack_back_trail := 30.0
## build-up: centre backs spread to this multiple of their slot width
@export var build_split := 1.35

@export_group("Full backs")
## build-up: they push up this far to give a pass
@export var build_push := 10.0
## the wide midfielder in front counts as holding the width when he is further out than this
@export var wide_hold_z := 24.0
## overlap: run to this far ahead of the winger, on the touchline line
@export var overlap_ahead := 8.0
@export var overlap_z := 30.0
## underlap (winger came inside): run inside him on this line, this far ahead
@export var underlap_ahead := 4.0
@export var underlap_z := 18.0

@export_group("Wide midfielders")
## attacking: hold the width at this distance from the centre line
@export var width_z := 28.0
## ball on the other flank in the final third: come to the far post
@export var far_post_when_far := true

@export_group("Central midfielders")
## the one who stays behind the ball stands this far behind it
@export var holder_behind := 8.0
## the one who goes forward arrives late at the edge of the box, this far across (cut-back)
@export var late_z := 8.0

@export_group("Strikers")
## pinning the back four: stand this far in front of the opponents' last defender (negative = level)
@export var shoulder_gap := 1.0
## the dropper stands this far in front of the last defender (the pocket)
@export var pocket_depth := 14.0
## the shoulder striker uses the channel between centre back and full back when the ball is wide: this far across
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

## x (in the team frame, times dir) of the opponents' last outfield defender
func _last_defender_t(c: AiContext) -> float:
	var best := -1e9
	for o in c.other.players:
		if not o.is_keeper(): best = maxf(best, o.pos.x * c.dir)
	return best

func _block_x(c: AiContext, line: int, trail: float) -> float:
	var back := clampf(_ball_t(c) - trail, back_min, back_max)
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
	if trigger_facing_own_goal and k.face.x * c.dir > 0.3 and c.depth(k.pos) > 0.5: return true   # his own goal is the way we attack
	return false

# ---------------------------------------------------------------- we have the ball
func _attack(f: Footballer, c: AiContext, role: AiRole) -> AiIntent:
	var spot := role.home_spot(f, c)
	var side := signf(f.slot.y)
	if side == 0.0: side = 1.0
	var building := c.phase == AiBrain.Phase.BUILD_UP
	match f.role:
		"CB":
			if building: spot.y *= build_split
			else: spot.x = _block_x(c, 0, attack_back_trail) * c.dir
		"LB", "RB":
			if building:
				spot.x += c.dir * build_push
			else:
				var wm := _wide_mate(f, c)
				if wm != null:
					var holds := absf(wm.pos.y) > wide_hold_z
					var ahead := wm.pos.x * c.dir + (overlap_ahead if holds else underlap_ahead)
					spot = Vector2(maxf(spot.x * c.dir, ahead) * c.dir, side * (overlap_z if holds else underlap_z))
		"LW", "RW":
			spot.y = side * width_z
			if far_post_when_far and c.phase == AiBrain.Phase.FINAL_THIRD and signf(c.ball.y) == -side and absf(c.ball.y) > 12.0:
				spot = c.spot("far_post_left" if side < 0.0 else "far_post_right")
		"CM":
			spot = _attack_cm(f, c, spot)
		"ST":
			spot = _attack_st(f, c, spot)
		_:
			return null
	return _go(c, spot, c.s.jog_factor)

func _wide_mate(f: Footballer, c: AiContext) -> Footballer:
	for m in c.team.players:
		if (m.role == "LW" or m.role == "RW") and signf(m.slot.y) == signf(f.slot.y): return m
	return null

## the two central midfielders: the one nearer the ball goes forward, the other holds behind the ball
func _attack_cm(f: Footballer, c: AiContext, spot: Vector2) -> Vector2:
	var pair := _mates(c, "CM")
	var goer := _nearest_to_ball(pair, c)
	if pair.size() < 2 or goer == f:
		if c.phase == AiBrain.Phase.FINAL_THIRD and c.carrier != null:
			var edge := c.spot("opp_box_edge")
			return Vector2(edge.x, -signf(c.carrier.pos.y if c.carrier.pos.y != 0.0 else 1.0) * late_z)   # the cut-back / back post
		return spot
	return Vector2(minf(spot.x * c.dir, _ball_t(c) - holder_behind) * c.dir, spot.y * 0.6)

## the two strikers: building up both pin the back four; after that the one nearer the ball drops into the pocket, the other stays on the shoulder
func _attack_st(f: Footballer, c: AiContext, spot: Vector2) -> Vector2:
	var last_t := _last_defender_t(c)
	var shoulder := Vector2(minf(last_t - shoulder_gap, 51.0) * c.dir, spot.y)
	if c.phase == AiBrain.Phase.BUILD_UP: return shoulder
	var pair := _mates(c, "ST")
	var dropper := _nearest_to_ball(pair, c)
	if pair.size() >= 2 and dropper == f:
		return Vector2((last_t - pocket_depth) * c.dir, spot.y * 0.5)
	if absf(c.ball.y) > 14.0: shoulder.y = signf(c.ball.y) * channel_z
	return shoulder

# ---------------------------------------------------------------- they have the ball
func _defend(f: Footballer, c: AiContext, role: AiRole) -> AiIntent:
	var carrier := c.carrier
	var triggered := _pressing_trigger(c)
	if c.presser == f:
		if triggered or c.depth(carrier.pos) <= block_depth: return null          # normal close-down by the role
		var spot := carrier.pos + (c.own_goal() - carrier.pos).normalized() * contain_distance
		return _go(c, spot, c.s.jog_factor)
	if triggered and f.role == "ST":
		var cover := _cover_target(c)
		if cover != null:
			return _go(c, carrier.pos + (cover.pos - carrier.pos).normalized() * cover_shadow, c.s.sprint_factor)
	var home := role.home_spot(f, c)
	var x := home.x
	match f.role:
		"CB", "LB", "RB":
			x = _block_x(c, 0, back_trail) * c.dir
			if f.role == "CB" and f.style == "stopper":
				var st := _striker_near(f, c)
				if st != null:
					return _go(c, st.pos + (c.own_goal() - st.pos).normalized() * step_out_goal_side, c.s.sprint_factor)
		"LW", "RW":
			x = _block_x(c, 1, back_trail) * c.dir
		"CM":
			var pair := _mates(c, "CM")
			var holder := pair.size() >= 2 and _nearest_to_ball(pair, c) != f
			x = (_block_x(c, 1, back_trail) - (holder_drop if holder else 0.0)) * c.dir
		"ST":
			x = _block_x(c, 2, back_trail) * c.dir
		_:
			return null
	return _go(c, Vector2(x, home.y), c.s.jog_factor)

## the opposing centre back / pivot nearest the ball (not the carrier): the lane the second striker shadows
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
