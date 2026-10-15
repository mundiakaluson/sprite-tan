class_name AiSt
extends AiRole
## Striker. Pins the centre backs, drops short to hold the ball up (`target` style), or runs in behind (`poacher` style); shoots whenever there is a chance.
## Formation switch: with two strikers (4-4-2, 3-5-2, 5-3-2) one drops and one stays; alone up front he stays high.

func _init() -> void:
	push_weight = 1.0
	shoot_bias = 1.0
	dribble_urge = 0.35

func _support(f: Footballer, c: AiContext) -> AiIntent:
	var spot := home_spot(f, c)
	match f.style:
		"target":
			# come short to receive in build-up and progression, hold it up
			if c.phase == AiBrain.Phase.BUILD_UP or c.phase == AiBrain.Phase.PROGRESS: spot.x -= c.dir * 8.0
		"poacher":
			# on the last defender's shoulder: up near the goal line in the final third
			if c.phase == AiBrain.Phase.FINAL_THIRD: spot.x = c.dir * minf(52.0, maxf(spot.x * c.dir, 38.0))
		_: pass
	return _go(c, c.clamp_pitch(spot, 2.0), c.s.jog_factor)

func _wants_shot(f: Footballer, c: AiContext) -> bool:
	# a striker shoots from a little further out than the others
	if f.pos.distance_to(c.goal()) > c.s.shoot_range + 4.0: return false
	if c.lane_blocked(f.pos, c.goal(), 1.4): return false
	return c.game.rng.randf() < minf(1.0, c.s.shoot_chance * (0.6 + shoot_bias)) 
