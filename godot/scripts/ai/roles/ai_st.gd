class_name AiSt
extends AiRole
## Striker. Pins the centre backs, drops short to hold the ball up (`target` style), or runs in behind (`poacher` style); shoots whenever there is a chance.
## Formation switch: with two strikers (4-4-2, 3-5-2, 5-3-2) one drops and one stays; alone up front he stays high.

@export_group("Striker")
## the target style comes this much deeper in build-up and progression
@export var drop_depth := 8.0
## the poacher goes at least this far up the pitch (metres from the centre) in the final third
@export var poacher_x := 38.0

func _init() -> void:
	push_weight = 1.0
	shoot_bias = 1.0
	dribble_urge = 0.35
	range_bonus = 4.0
	lane_width = 1.4

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	match f.style:
		"target":
			if c.phase == AiBrain.Phase.BUILD_UP or c.phase == AiBrain.Phase.PROGRESS: spot.x -= c.dir * drop_depth
		"poacher":
			if c.phase == AiBrain.Phase.FINAL_THIRD: spot.x = c.dir * minf(52.0, maxf(spot.x * c.dir, poacher_x))
		_: pass
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)
