class_name AiKeeperGesture
extends AiBehaviour
## The keeper has just gathered the ball: before he distributes he says something with it, once per possession, depending on the game:
##  - winning late on              -> CALM IT DOWN (pats the air, takes his time)
##  - losing late on                -> WAVE THE TEAM UP (urgent, quick)
##  - a back five / parked bus / the opponent pressing high -> ORGANISE the back line (sweeping arm)
##  - otherwise                     -> POINTS at the team mate he is about to give it to (and then gives it to him: AiGk reads f.ai["gk_target"])
## Clips: gk31-gk34 (sprites/moves_keeper.py). Numbers below.

@export_group("Keeper gestures")
## chance he gestures at all after taking the ball (some keepers just get on with it)
@export_range(0.0, 1.0) var chance := 0.85
## "late on" = from this match minute
@export var late_minute := 70.0
## seconds the gesture takes (the clip is stretched to it)
@export var gesture_time := 1.1
@export var calm_time := 1.8
@export var clip_point := "gk31_point_to_team_mate"
@export var clip_wave_up := "gk32_wave_team_up"
@export var clip_calm := "gk33_calm_it_down"
@export var clip_organise := "gk34_organise_defence"
## stances / formation families that make him organise
@export var organise_stances := PackedStringArray(["park_bus", "mid_block"])
@export var organise_families := PackedStringArray(["FIVE_BACK"])
## the team mate he points at: within this distance (m), the freest one
@export var point_range := 45.0

static var stat := {}       ## headless: gesture -> count

func _init() -> void:
	priority = -20
	roles = PackedStringArray(["GK"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, role: AiRole) -> bool:
	if f.hold < 0.05: f.ai.erase("gestured")                              # a new possession
	if f.ai.get("gestured", false) or f.lock > 0.0 or f.hold < 0.25: return false
	if role is AiGk and (role as AiGk).calm_left(f, c) > 0.0: return false  # after he has walked back and looked round
	f.ai["gestured"] = true
	return c.game.rng.randf() < chance

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = f.pos
	i.action = "gesture"
	var minute := c.game.clock / 60.0
	var diff := c.team.score - c.other.score
	var pressing := 0
	for o in c.other.players:
		if not o.is_keeper() and c.depth(o.pos) < 0.33: pressing += 1        # opponents camped in our third
	if minute >= late_minute and diff > 0:
		i.clip = clip_calm
		i.speed_override = calm_time
		i.note = "calm it down"
	elif minute >= late_minute and diff < 0:
		i.clip = clip_wave_up
		i.speed_override = gesture_time
		i.note = "push up"
	elif c.team.stance_id in organise_stances or c.family in organise_families or pressing >= 3:
		i.clip = clip_organise
		i.speed_override = gesture_time * 1.3
		i.note = "organise"
	else:
		var mate := _free_mate(f, c)
		i.clip = clip_point
		i.speed_override = gesture_time
		i.target = mate
		if mate != null: f.ai["gk_target"] = mate
		i.note = "point"
	stat[i.note] = int(stat.get(i.note, 0)) + 1
	return i

func _free_mate(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f or m.pos.distance_to(f.pos) > point_range: continue
		var o := c.nearest_opponent(m.pos)
		var free := o.pos.distance_to(m.pos) if o != null else 20.0
		var score := free - m.pos.distance_to(f.pos) * 0.15
		if score > bs:
			bs = score
			best = m
	return best
