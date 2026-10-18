class_name AiContext
extends RefCounted
## What one team sees this frame: the ball, who has it, what phase the team is in, the formation numbers and a few helpers. Roles read it, never change it.
## Pitch: x along (the team attacks towards x = 52.5 * dir), z across. depth() goes 0 (own goal line) to 1 (opponent goal line).

const HALF_L := 52.5
const HALF_W := 34.0

static var _styles := {}

var game: MatchGame
var s: MatchSettings
var team: Team
var profile: AiProfile          ## this team's role + formation tuning
var other: Team
var dir := 1.0
var phase := 0                  ## AiBrain.Phase
var has_ball := false           ## this team has the ball
var carrier: Footballer
var ball := Vector2.ZERO
var ball_vel := Vector2.ZERO
var presser: Footballer         ## the team mate closing the ball down when we do not have it
var formation_id := ""
var family := ""                ## FOUR_BACK / THREE_BACK / FIVE_BACK
var stance: TeamStance = TeamStance.new()
var cover := {}                 ## Footballer -> where he covers a team mate who stepped out (set by AiInteract.compute)
var pushers: Array = []         ## team mates who stepped out of the line / are pressing
var push_y := 0.0               ## average z of the pushers
var outlet: Footballer          ## our presser, when his press should send the striker looking for space
var poss_time := 0.0            ## seconds since this team won the ball (0 while it does not have it)
# ---- the line (AiLine.compute, once per frame)
var offside_t := 0.0            ## team-frame x (x * dir) of the offside line our forwards must stay behind (their second-last player or the ball)
var line_shift := 0.0           ## metres our back line (and the block with it) is moved up (+) or dropped (-) by reading the ball
var line_shift_base := 0.0      ## line_shift when an offside trap was sprung
var line_target := 0.0
var line_urgent := false        ## the line is stepping / dropping fast: defenders sprint to it
var line_mode := ""             ## hold / squeeze / drop / trap / attack (debug, tests)
var line_floor_t := -35.5       ## team-frame x the back line never drops below
var trap_until := -1.0          ## game clock until which the offside trap step is on
# ---- transitions (AiTransition.compute)
var lost_t := -1e9              ## game clock when we last lost the ball, and where
var lost_at := Vector2.ZERO
var won_t := -1e9               ## game clock when we last won it
var counter_press := false      ## we are counter-pressing right now
var countering := false         ## we are on a counter-attack right now
var cp_players := {}            ## Footballer -> where he goes in the counter-press (carrier or a lane)
var rest_marks := {}            ## rest defender -> their forward he watches
var rest_list: Array = []
var rest_frame := -1
var base_form := {}             ## the formation's own numbers, before the stance
var form := {}                  ## formations.csv numbers, family defaults filled in: line_height, width, compactness, press, overlap, directness, counter, risk

func setup(g: MatchGame, t: Team) -> void:
	game = g
	s = g.settings
	team = t
	other = g.away if t == g.home else g.home
	dir = t.dir
	formation_id = t.formation_id
	var lay := MatchSettings.layout(formation_id)
	var row: Dictionary = lay.row() if lay != null else Data.row("formations", formation_id)
	family = str(row.get("family", "FOUR_BACK"))
	var fam := {}
	for r in Data.table("formation_families"):
		if r["family"] == family: fam = r
	for k in ["line_height", "width", "compactness", "press", "overlap", "directness", "counter", "risk"]:
		var v := str(row.get(k, ""))
		if v == "": v = str(fam.get(k, "0.5"))
		base_form[k] = v.to_float()
		form[k] = base_form[k]

## lean the formation numbers by the team's stance (called every frame by the brain)
func set_stance(st: TeamStance) -> void:
	stance = st
	for k in base_form: form[k] = clampf(float(base_form[k]) + st.delta(k), 0.0, 1.0)

## game-clock seconds for `real` real seconds (the 90 minutes are played in MatchSettings.match_minutes)
func game_s(real: float) -> float:
	return real * MatchGame.GAME_SECONDS / (s.match_minutes * 60.0)

## once per frame: how long this team has had the ball
func tick(dt: float) -> void:
	poss_time = poss_time + dt if has_ball else 0.0

func refresh() -> void:
	carrier = game.carrier
	ball = Vector2(game.ball.phys.pos.x, game.ball.phys.pos.z)
	ball_vel = Vector2(game.ball.phys.vel.x, game.ball.phys.vel.z)
	has_ball = carrier != null and carrier.team == team

# ---- the pitch map (data/pitch_zones.csv, pitch_spots.csv), seen from this team's side
func spot(id: String) -> Vector2:
	return PitchMap.spot(id, dir)

func zone(id: String) -> Rect2:
	return PitchMap.rect(id, dir)

func zone_centre(id: String) -> Vector2:
	return PitchMap.centre(id, dir)

func in_zone(pos: Vector2, id: String) -> bool:
	return PitchMap.contains(id, pos, dir)

func zones_at(pos: Vector2) -> Array:
	return PitchMap.zones_at(pos, dir)

## formation number (0..1), e.g. f("press")
func f(key: String, d := 0.5) -> float:
	return float(form.get(key, d))

func depth(pos: Vector2) -> float:
	return clampf((pos.x * dir + HALF_L) / (2.0 * HALF_L), 0.0, 1.0)

func goal() -> Vector2:
	return Vector2(HALF_L * dir, 0.0)

func own_goal() -> Vector2:
	return Vector2(-HALF_L * dir, 0.0)

func clamp_pitch(p: Vector2, margin := 1.0) -> Vector2:
	return Vector2(clampf(p.x, -HALF_L + margin, HALF_L - margin), clampf(p.y, -HALF_W + margin, HALF_W - margin))

func nearest_opponent(pos: Vector2) -> Footballer:
	var best: Footballer = null
	var bd := 1e9
	for o in other.players:
		var d := o.pos.distance_to(pos)
		if d < bd:
			bd = d
			best = o
	return best

## distance to the closest opponent
func pressure(pos: Vector2) -> float:
	var o := nearest_opponent(pos)
	return o.pos.distance_to(pos) if o != null else 99.0

## an opponent in the way of the lane a -> b. One standing on the passer (closer than skip_start to a along the lane) is pressure, not a block, and one on the receiver
## (closer than skip_end to b) is the receiver's marker: both show in the "open" score instead. Without this every pass of a pressed carrier counted as blocked.
func lane_blocked(a: Vector2, b: Vector2, width := 2.2, skip_start := 2.5, skip_end := 1.5) -> bool:
	for o in other.players:
		var p := Geometry2D.get_closest_point_to_segment(o.pos, a, b)
		if p.distance_to(o.pos) >= width: continue
		if p.distance_to(a) < skip_start or p.distance_to(b) < skip_end: continue
		return true
	return false

## every team mate as a pass option: {mate, dist, forward (metres gained towards goal), open (distance to his nearest opponent), blocked}
func pass_options(from_f: Footballer) -> Array:
	var out: Array = []
	for m in team.players:
		if m == from_f: continue
		var d := m.pos.distance_to(from_f.pos)
		if d < s.pass_min or d > s.pass_max: continue
		out.append({"mate": m, "dist": d, "forward": (m.pos.x - from_f.pos.x) * dir, "open": pressure(m.pos), "blocked": lane_blocked(from_f.pos, m.pos),
			"offside": game.offside.would_be(m, from_f.pos.x)})
	return out

## styles.csv row of a formation style ("fullback", "anchor", ...)
static func style_row(style: String) -> Dictionary:
	if _styles.is_empty():
		for r in Data.table("styles"): _styles[r["style"]] = r
	return _styles.get(style, {})
