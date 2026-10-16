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
## how far (m) outside the far post the curler is aimed
@export var curl_out := 3.0
## which curl it is follows the geometry: the finesse (inside of the boot, K02) bends clockwise, the trivela (outside, K03) the other way, so one wing gets each

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
	i.move_to = f.pos
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
	if gk != null and off_line > keeper_out:                              # one on one
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
		var out := Vector2(goal.x + c.dir * 1.5, -signf(f.pos.y) * (half_goal + curl_out))
		var v := out - f.pos
		var bend := Vector2(goal.x, -signf(f.pos.y) * (half_goal - post_margin)) - out      # the way it has to come back
		var cw := v.x * bend.y - v.y * bend.x < 0.0                       # K02 (finesse) bends clockwise (cross < 0), K03 (trivela) the other way
		i.style = "K02" if cw else "K03"
		i.clip = clip_finesse if cw else clip_trivela
		i.aim = out
		i.note = "curler"
		return i
	i.style = "K01"
	i.clip = _pick(clips_central, f, rng)
	i.note = "finish"
	return i

# ---------------------------------------------------------------- helpers
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
