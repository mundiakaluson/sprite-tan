class_name AiFinish
extends AiBehaviour
## The man with the ball in a shooting position: inside the box he takes the shot (no more waiting for a perfect lane), and chooses HOW:
##  - the keeper has come out (a one on one): too far to run round him -> chip; close -> a placed side-foot finish into the corner he is not covering
##  - wide of the goal (a wing / angle): a curler to the far post, with the inside of the boot (finesse) or the outside (trivela)
##  - central and close: a placed or snapped finish, into the corner away from the keeper
##  - outside the box: a drive (the role's normal shot logic still decides when)
## Kick styles are data/kick_styles.csv ids, clips are sh*.json (see MatchSettings > Kick animations).

@export_group("Finish")
## inside this zone he shoots (data/pitch_zones.csv id)
@export var box_zone := "opp_box"
## shots per second in the box at SHO 60 for a role with shoot_bias 1 (a shot is taken within about a third of a second on average at 3)
@export var rate := 3.0
## the chance a shot is taken from just outside the box, up to `edge_range` metres from goal (pressed carriers shoot more)
@export var edge_range := 24.0
@export var edge_rate := 0.8
## a defender (not the keeper) standing right in the line: no shot (lane width m). The keeper is dealt with by choosing the corner.
@export var lane_width := 1.1
## seconds before he can decide to shoot again
@export var cooldown := 0.6

@export_group("One on one")
## the keeper this far (m) off his line counts as coming out
@export var keeper_out := 3.5
## shooter further than this from the keeper: chip him; closer: place it past him
@export var chip_gap := 9.0
## chip: ball speed = sqrt(distance x this), so it drops under the bar after clearing him
@export var chip_k := 10.5
## chips are aimed this far (m) short of the goal line, to land and run on in
@export var chip_short := 1.0
## the corner for a placed finish is this far (m) inside the post
@export var post_margin := 1.2

@export_group("Wide shots")
## shooter further than this (m) off the middle: a curler to the far post
@export var side_y := 9.0
## how far (m) outside the far post the curler is aimed, and its ball speed (m/s; faster ones balloon over and bend less)
@export var curl_out := 2.0
@export var curl_speed := 23.0
## from this far (m) the curler is LIFTED (K12 lofted finesse / K13 lofted trivela): slower, rising, bending and dropping in at about lofted_height m;
## its speed is solved between lofted_speed_min and _max (start lofted_speed)
@export var lofted_min_dist := 13.0
@export var lofted_height := 1.5
@export var lofted_speed := 19.0
@export var lofted_speed_min := 15.0
@export var lofted_speed_max := 24.0
## which curl it is follows the geometry: the finesse (inside of the boot, K02) bends clockwise, the trivela (outside, K03) the other way, so one wing gets each

@export_group("Shot quality")
## good shooters strike it flat with a little bend away from the keeper (K10 / K11): SHO at least this, chance per central shot, aimed this far (m) inside the corner so the bend takes it into it
@export var flat_sho_min := 74
@export_range(0.0, 1.0) var flat_share := 0.75
@export var flat_aim_in := 1.6
## a low drive (K09) that skips in front of the keeper: from at least this far (m), chance per shot
@export var low_drive_min := 11.0
@export_range(0.0, 1.0) var low_drive_share := 0.3
## keeper off his line: a striker with SHO and "game sense" (average of PAS and DRI) at least these bends it round him into the far post instead of chipping / placing,
## when he is at least curl_min_gap (m) from the keeper
@export var curl_sho_min := 72
@export var curl_sense_min := 66
@export var curl_min_gap := 5.0
## corrections when aiming a bending shot by simulating its flight
@export var solve_steps := 4
@export var clips_flat := PackedStringArray(["sh02_instep_drive", "sh18_near_post_lash", "sh23_snap_shot"])
@export var clip_low_drive := "sh16_low_skimmer"

@export_group("Clips")
@export var clips_one_on_one := PackedStringArray(["sh01_side_foot_place", "sh28_composure_finish", "sh24_one_touch_finish"])
@export var clip_chip := "sh05_chip_lob"
@export var clip_finesse := "sh03_finesse_curler"
@export var clip_trivela := "sh04_trivela_bender"
@export var clips_central := PackedStringArray(["sh01_side_foot_place", "sh23_snap_shot", "sh14_toe_poke", "sh24_one_touch_finish"])

func _init() -> void:
	priority = -5
	roles = PackedStringArray(["ST", "LW", "RW", "CAM", "CM"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, role: AiRole) -> bool:
	if c.game.kicking.busy(f) or c.game.dribble.busy(f) or f.lock > 0.0 or f.hold < 0.25: return false
	if f.ai.get("finish_cd", 0.0) > _now(): return false
	var d := f.pos.distance_to(c.goal())
	var in_box := c.in_zone(f.pos, box_zone)
	if not in_box and d > edge_range: return false
	if _blocked(f, c): return false
	var skill := 0.5 + f.stat("SHO", 60) / 100.0
	var p := (rate if in_box else edge_rate) * skill * role.shoot_bias * c.game.get_physics_process_delta_time()
	if c.pressure(f.pos) < c.s.pressure_radius: p *= 2.0                # pressed: get it off
	return c.game.rng.randf() < p

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos + (f.vel if f.vel.length() > 0.5 else f.face) .normalized() * 4.0     # keep running through the shot, no stopping to set himself
	i.speed = c.s.carry_factor
	i.action = "shoot"
	f.ai["finish_cd"] = _now() + cooldown
	var rng := c.game.rng
	var goal := c.goal()
	var gk := _keeper(c)
	var kx := gk.pos.x if gk != null else goal.x
	var off_line := absf(goal.x - kx) if gk != null else 0.0
	var gap := f.pos.distance_to(gk.pos) if gk != null else 99.0
	var half_goal := MatchGame.GOAL_HALF
	var far := _corner(f, c, gk, half_goal)                              # the corner away from the keeper
	i.aim = Vector2(goal.x + c.dir * 1.5, far)
	i.speed_override = 0.0
	var sho := f.stat("SHO", 60)
	var sense := (f.stat("PAS", 60) + f.stat("DRI", 60)) * 0.5
	if gk != null and off_line > keeper_out:                              # one on one
		if sho >= curl_sho_min and sense >= curl_sense_min and gap >= curl_min_gap:
			var side := -signf(gk.pos.y - f.pos.y) if absf(gk.pos.y - f.pos.y) > 0.4 else -signf(f.pos.y + 0.01)     # the far post: away from where the keeper is
			_curl(i, f, c, side, half_goal)
			i.note = "keeper off his line: curled round him"
			return i
		if gap > chip_gap:
			i.style = "K05"
			i.clip = clip_chip
			i.aim = Vector2(goal.x - c.dir * chip_short, clampf(f.pos.y * 0.3, -2.0, 2.0))
			i.speed_override = sqrt(f.pos.distance_to(i.aim) * chip_k)
			i.note = "chip"
		else:
			i.style = "K01"
			i.clip = _pick(clips_one_on_one, f, rng)
			i.note = "place past keeper"
		return i
	if absf(f.pos.y) > side_y:                                          # wide: bend it round the keeper to the far post
		_curl(i, f, c, -signf(f.pos.y), half_goal)
		i.note = "curler"
		return i
	var d := f.pos.distance_to(goal)
	if sho >= flat_sho_min and rng.randf() < flat_share:                 # struck flat, bending late away from the keeper into the corner
		var corner := Vector2(goal.x + c.dir * 1.5, far)
		var start := Vector2(corner.x, far - signf(far) * flat_aim_in)
		var cw := _cross(start - f.pos, corner - start) < 0.0              # starts inside, bends out into the corner (away from the keeper)
		i.style = "K10" if cw else "K11"
		i.clip = _pick(clips_flat, f, rng)
		i.speed_override = _shot_speed(f)
		i.aim = _solve(c, i.style, i.speed_override, Vector2(goal.x, far), start)
		i.note = "flat bender"
		return i
	if d >= low_drive_min and rng.randf() < low_drive_share:              # low and hard, skipping up off the grass in front of him
		i.style = "K09"
		i.clip = clip_low_drive if f.node.has_clip(clip_low_drive) else _pick(clips_flat, f, rng)
		i.note = "low drive"
		return i
	i.style = "K01"
	i.clip = _pick(clips_central, f, rng)
	i.note = "finish"
	return i

# ---------------------------------------------------------------- helpers
## a curler into the post on `side` (+1 / -1 across): aimed curl_out m outside it, bending back in; the spin direction follows the geometry
## (K02 finesse = inside of the boot bends clockwise, K03 trivela = outside of the boot the other way)
func _curl(i: AiIntent, f: Footballer, c: AiContext, side: float, half_goal: float) -> void:
	var goal := c.goal()
	var out := Vector2(goal.x + c.dir * 1.5, side * (half_goal + curl_out))
	var post := Vector2(goal.x, side * (half_goal - post_margin))
	var cw := _cross(out - f.pos, post - out) < 0.0
	i.clip = clip_finesse if cw else clip_trivela
	if f.pos.distance_to(goal) >= lofted_min_dist:                        # from range: lifted, slower, dropping under the bar (K12 / K13)
		i.style = "K12" if cw else "K13"
		var sol := _solve_lofted(c, i.style, Vector2(goal.x, post.y), out)
		i.aim = sol[0]
		i.speed_override = sol[1]
		return
	i.style = "K02" if cw else "K03"
	i.speed_override = curl_speed                                          # close in: low and quicker
	i.aim = _solve(c, i.style, curl_speed, Vector2(goal.x, post.y), out)    # aim so the bend brings it into the post

## a lifted curler: aim AND speed so it crosses the line at the post at `lofted_height` (simulated flight, Ball.predict_cross). Returns [aim, speed].
func _solve_lofted(c: AiContext, style_id: String, target: Vector2, guess: Vector2) -> Array:
	var b := c.game.ball
	var from := b.phys.pos
	var aim := guess
	var speed := lofted_speed
	for n in solve_steps + 3:
		var hit := b.predict_cross(from, aim, style_id, speed, target.x)
		var miss := target.y - hit.z
		var high := lofted_height - hit.y
		if absf(miss) < 0.2 and absf(high) < 0.25: break
		aim.y += miss * 0.9
		speed = clampf(speed + high * 0.9, lofted_speed_min, lofted_speed_max)
	return [aim, speed]

## the aim that makes a kick with this style and speed cross the goal line at `target` (a few corrections of a simulated flight, Ball.predict_cross); starts from `guess`
func _solve(c: AiContext, style_id: String, speed: float, target: Vector2, guess: Vector2) -> Vector2:
	var b := c.game.ball
	var from := b.phys.pos
	var aim := guess
	for n in solve_steps:
		var hit := b.predict_cross(from, aim, style_id, speed, target.x)
		var miss := target.y - hit.z
		if absf(miss) < 0.15: break
		aim.y += miss * 0.9
	return aim

## the shot's own speed for this shooter (data/ball_actions.csv row "shot")
func _shot_speed(f: Footballer) -> float:
	var r := Data.row("ball_actions", "shot")
	return clampf(Data.num(r.get("base_speed"), 24.0) + Data.num(r.get("per_stat"), 0.11) * f.stat("SHO", 60), Data.num(r.get("min_speed"), 18.0), Data.num(r.get("max_speed"), 36.0))

func _cross(a: Vector2, b: Vector2) -> float:
	return a.x * b.y - a.y * b.x

## which corner (y) to put it in: the one the keeper is not at; with no keeper, the far one from the shooter
func _corner(f: Footballer, c: AiContext, gk: Footballer, half_goal: float) -> float:
	var side := signf(f.pos.y) if absf(f.pos.y) > 0.5 else (1.0 if c.game.rng.randf() < 0.5 else -1.0)
	var target_side := -side                                              # far post by default
	if gk != null and absf(gk.pos.y) > 0.8: target_side = -signf(gk.pos.y)
	return target_side * (half_goal - post_margin)

func _keeper(c: AiContext) -> Footballer:
	for o in c.other.players:
		if o.is_keeper(): return o
	return null

## a defender (not the keeper) in the line to goal
func _blocked(f: Footballer, c: AiContext) -> bool:
	for o in c.other.players:
		if o.is_keeper(): continue
		var p := Geometry2D.get_closest_point_to_segment(o.pos, f.pos, c.goal())
		if p.distance_to(o.pos) < lane_width and p.distance_to(f.pos) > 1.5: return true
	return false

func _pick(list: PackedStringArray, f: Footballer, rng: RandomNumberGenerator) -> String:
	var ok := PackedStringArray()
	for n in list:
		if f.node.has_clip(n): ok.append(n)
	return ok[rng.randi() % ok.size()] if not ok.is_empty() else ""

func _now() -> float:
	return Engine.get_physics_frames() / float(Engine.physics_ticks_per_second)
