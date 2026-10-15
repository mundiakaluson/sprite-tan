class_name AiClearBall
extends AiBehaviour
## Defenders get the ball away when there is danger in our own box: with the ball and an opponent on him (or inside the six-yard box), he lumps it up the wing (a lob to a spot, no team mate);
## when the ball is loose in the box with an opponent about to reach it, the nearest defender goes and clears it.

@export_group("Clear ball")
## the zone that counts as our box (data/pitch_zones.csv ids: own_box, own_third ...)
@export var danger_zone := "own_box"
## clear when an opponent is closer than this (metres) to the carrier
@export var pressure_distance := 4.5
## always clear inside this zone, pressure or not
@export var panic_zone := "own_six"
## a loose ball: go for it when an opponent is within this many metres of it
@export var loose_danger := 9.0
## how far up the pitch the clearance is aimed, and how far from the touchline it lands (metres)
@export var clear_length := 38.0
@export var touchline_margin := 7.0
## aim further up the wing from the side with fewer opponents (higher = cares more about them)
@export var opponent_weight := 1.0

func _init() -> void:
	roles = PackedStringArray(["CB", "LB", "RB"])
	when = WITH_BALL | LOOSE

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.carrier == f:
		if c.in_zone(f.pos, panic_zone): return true
		return c.in_zone(f.pos, danger_zone) and c.pressure(f.pos) < pressure_distance
	# loose ball in our box: the nearest of us, with an opponent close to it
	if not c.in_zone(c.ball, danger_zone): return false
	if c.pressure(c.ball) > loose_danger: return false
	for m in c.team.players:
		if m != f and not m.is_keeper() and m.pos.distance_to(c.ball) < f.pos.distance_to(c.ball): return false
	return true

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	if c.carrier == f:
		i.action = "lob"
		i.aim = _clear_spot(f, c)
		i.note = "clear"
	else:
		i.move_to = c.ball + c.ball_vel * 0.25
		i.speed = c.s.sprint_factor
		i.note = "go and clear"
	return i

## up the pitch, to the wing with fewer opponents (and an open line from him to it)
func _clear_spot(f: Footballer, c: AiContext) -> Vector2:
	var x := clampf(f.pos.x + c.dir * clear_length, -MatchGame.HALF_L + 6.0, MatchGame.HALF_L - 6.0)
	var best := Vector2(x, 0.0)
	var best_score := -1e9
	for side in [-1.0, 1.0]:
		var spot := Vector2(x, side * (MatchGame.HALF_W - touchline_margin))
		var score := c.pressure(spot) * opponent_weight - (20.0 if c.lane_blocked(f.pos, spot, 1.5) else 0.0) - absf(f.pos.y - spot.y) * 0.1
		if score > best_score:
			best_score = score
			best = spot
	return best
