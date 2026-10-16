class_name AiRunInBehind
extends AiBehaviour
## Off the ball: a forward times a run IN BEHIND the defence when a team mate has the ball and time to play it. He picks the gap in their back line
## nearest to him (between two defenders, or outside the last one), starts level with the line and sprints through it to a spot `run_depth` m beyond.
## While he runs, f.ai["run_behind"] = {until, spot} tells the ball carrier (AiThroughBall) to slide it into his path. One runner per team at a time.

@export_group("Run in behind")
## runs per second for a forward who could make one (scaled by PAC)
@export var rate := 0.9
## the team mate on the ball: at least this far up the pitch (depth 0..1) and with no opponent closer than carrier_space (m)
@export var min_depth := 0.35
@export var carrier_space := 3.0
## the runner: within this far (m) of the carrier, and not already more than `ahead_max` m beyond their last line
@export var max_from_carrier := 32.0
@export var ahead_max := 2.0
## the run: this far (m) beyond their line, through a gap at least gap_min (m) wide; it lasts run_time s; cooldown s before he goes again
@export var run_depth := 11.0
@export var gap_min := 4.0
@export var run_time := 2.6
@export var cooldown := 3.5
## never closer to their goal line than this (m): he runs at the ball's landing, not into the keeper
@export var goal_line_gap := 6.0
## he only goes when he is sure: the carrier faces forward (dot over carrier_facing), the lane from the carrier to the spot is open (lane m), and it has
## stayed like that while he checked over his shoulder for scan_time s (shorter with good PAS + DRI: game sense)
@export_range(-1.0, 1.0) var carrier_facing := 0.3
@export var lane := 1.6
@export var scan_time := 0.55

static var stat_runs := 0

func _init() -> void:
	priority = -3
	roles = PackedStringArray(["ST", "LW", "RW", "CAM"])
	when = SUPPORT

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var run = f.ai.get("run_behind", null)
	if run != null:
		if _now() < float(run["until"]) and c.carrier != null and c.carrier.team == f.team: return true
		f.ai.erase("run_behind")
		c.team.ai.erase("runner")
		return false
	if f.lock > 0.0 or float(f.ai.get("run_cd", 0.0)) > _now(): return false
	var holder = c.team.ai.get("runner", null)
	if holder != null and holder != f and is_instance_valid(holder) and (holder as Footballer).ai.has("run_behind"): return false
	var k := c.carrier
	if k == null or k.is_keeper() or c.depth(k.pos) < min_depth: return false
	if c.pressure(k.pos) < carrier_space: return false
	if f.pos.distance_to(k.pos) > max_from_carrier: return false
	if (f.pos.x - line_x(c)) * c.dir > ahead_max: return false
	# scan: is it really on?
	var spot := gap_spot(f, c, run_depth, gap_min, goal_line_gap)
	var on := k.face.dot((c.goal() - k.pos).normalized()) > carrier_facing and not c.lane_blocked(k.pos, spot, lane)
	if not on:
		f.ai.erase("scan_since")
		return false
	var since := float(f.ai.get("scan_since", -1.0))
	if since < 0.0:
		f.ai["scan_since"] = _now()
		return false
	var sense := (f.stat("PAS", 60) + f.stat("DRI", 60)) * 0.5
	if _now() - since < scan_time * clampf(1.6 - sense / 100.0, 0.5, 1.2): return false
	return c.game.rng.randf() < rate * (0.5 + f.stat("PAC", 60) / 100.0) * c.game.get_physics_process_delta_time()

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var run = f.ai.get("run_behind", null)
	if run == null:
		f.ai.erase("scan_since")
		run = {"until": _now() + run_time, "spot": gap_spot(f, c, run_depth, gap_min, goal_line_gap)}
		f.ai["run_behind"] = run
		f.ai["run_cd"] = _now() + run_time + cooldown
		c.team.ai["runner"] = f
		stat_runs += 1
	var i := AiIntent.new()
	i.move_to = run["spot"]
	i.speed = c.s.sprint_factor
	i.note = "run in behind"
	return i

## their last line (pitch x of the deepest outfield opponent)
static func line_x(c: AiContext) -> float:
	var best := -1e9
	for o in c.other.players:
		if not o.is_keeper(): best = maxf(best, o.pos.x * c.dir)
	return best * c.dir

## a spot `depth` m behind their last line, through the gap in it nearest to f (gaps between the defenders near the line, and outside the end ones)
static func gap_spot(f: Footballer, c: AiContext, depth: float, gap_min: float, goal_gap: float) -> Vector2:
	var lx := line_x(c)
	var ys: Array = [-MatchGame.HALF_W + 3.0]
	for o in c.other.players:
		if not o.is_keeper() and absf(o.pos.x - lx) < 9.0: ys.append(o.pos.y)
	ys.append(MatchGame.HALF_W - 3.0)
	ys.sort()
	var best_y := f.pos.y
	var bd := 1e9
	for n in ys.size() - 1:
		var a: float = ys[n]
		var b: float = ys[n + 1]
		if b - a < gap_min: continue
		var mid := (a + b) * 0.5
		var d := absf(mid - f.pos.y) + absf(mid) * 0.15                    # nearest gap, a touch towards the middle
		if d < bd:
			bd = d
			best_y = mid
	var x := lx + c.dir * depth
	var limit := c.goal().x - c.dir * goal_gap
	if (x - limit) * c.dir > 0.0: x = limit
	return Vector2(x, clampf(best_y, -MatchGame.HALF_W + 3.0, MatchGame.HALF_W - 3.0))

func _now() -> float:
	return Engine.get_physics_frames() / float(Engine.physics_ticks_per_second)
