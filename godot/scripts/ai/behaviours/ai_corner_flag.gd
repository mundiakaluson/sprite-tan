class_name AiCornerFlag
extends AiBehaviour
## Game management (catalogue section 12 "Corner-flag shield"): protecting a lead late on, a forward with the ball near their corner does not cross or shoot.
## He takes it to the corner flag and shields it there (side-on, defender held off), running the clock down.

@export_group("Corner flag")
@export var after_minute := 80.0
## near their corner: within this far of the goal line and this far of the touchline
@export var near_line := 20.0
@export var near_touch := 16.0

static var stat_frames := 0

func _init() -> void:
	priority = -9
	roles = PackedStringArray(["ST", "LW", "RW", "CAM", "CM", "LB", "RB"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.game.clock / 60.0 < after_minute or c.team.score <= c.other.score: return false
	if c.game.kicking.busy(f) or f.lock > 0.0: return false
	return MatchGame.HALF_L - f.pos.x * c.dir < near_line and MatchGame.HALF_W - absf(f.pos.y) < near_touch

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var flag := Vector2((MatchGame.HALF_L - 1.5) * c.dir, signf(f.pos.y) * (MatchGame.HALF_W - 1.5))
	var i := AiIntent.new()
	i.move_to = flag
	i.speed = c.s.carry_factor * 0.6
	var o := c.nearest_opponent(f.pos)
	if f.pos.distance_to(flag) < 2.0 and o != null:
		f.face = (f.pos - o.pos).normalized()
		f.ai["shielding"] = true
		i.move_to = f.pos
	i.note = "corner flag"
	stat_frames += 1
	return i
