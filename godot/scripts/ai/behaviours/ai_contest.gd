class_name AiContest
extends AiBehaviour
## A ball in the air (a lob, a clearance): the nearest player of each team who can get there goes to where it will come down to head height and WAITS for it, facing the ball, instead of
## drifting back to his slot. With a rival there too, MatchAerial plays the duel (header, shove and chest, shoulder leap) when the ball arrives. The yellow ring is MatchAerial's marker.

@export_group("Contest")
## he sprints to the spot while further than this (m), then jogs in
@export var sprint_beyond := 4.0

func _init() -> void:
	priority = -10
	when = RECEIVING | LOOSE

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	return c.game.aerial.spot_for(f) != Vector2.INF and f.lock <= 0.0

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	var spot := c.game.aerial.spot_for(f)
	var d := f.pos.distance_to(spot)
	if d <= c.s.aerial_wait_dist:
		i.move_to = f.pos                                                  # in place: he waits for it, looking up
		f.ai["air_wait"] = true
		var b := c.game.ball.phys.pos
		var to := Vector2(b.x, b.z) - f.pos
		if to.length() > 0.5: f.face = to.normalized()
	else:
		i.move_to = spot
		i.speed = c.s.sprint_factor if d > sprint_beyond else c.s.jog_factor
		f.ai.erase("air_wait")
	i.note = "contest"
	return i
