class_name AiCb
extends AiRole
## Centre back. Holds the line, splits wide in build-up so the keeper has a pass, plays safe (never shoots, rarely dribbles) and lets the ball playing styles step forward.
## Formation switch: in a back three the middle one (style sweeper) covers behind; in a back five all three stay compact.

@export_group("Centre back")
## in build-up he spreads this much wider than his slot (a back four / a back three or five)
@export var split_four := 1.5
@export var split_three := 1.25
## the sweeper style stays this much deeper
@export var sweeper_drop := 3.0
## pass taste: bonus for a pass to a midfielder, penalty for one longer than long_pass
@export var midfield_bonus := 4.0
@export var long_pass := 25.0
@export var long_penalty := 6.0

func _init() -> void:
	push_weight = 0.35
	shoot_bias = 0.0
	dribble_urge = 0.1

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	if c.phase == AiBrain.Phase.BUILD_UP:
		match c.family:
			"THREE_BACK", "FIVE_BACK": spot.y = spot.y * split_three
			_: spot.y = spot.y * split_four
	if f.style == "sweeper": spot.x -= c.dir * sweeper_drop
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _pass_bias(f: Footballer, m: Footballer, _c: AiContext) -> float:
	var b := 0.0
	if m.role == "CDM" or m.role == "CM": b += midfield_bonus
	if m.pos.distance_to(f.pos) > long_pass: b -= long_penalty
	return b
