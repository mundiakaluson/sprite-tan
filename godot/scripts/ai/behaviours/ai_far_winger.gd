class_name AiFarWinger
extends AiBehaviour
## The far-side winger (catalogue section 9 "Far-side job", "Overload then switch"): with the ball on the other flank he does not drift in to watch.
## He holds the width on the highest line he can (AiLine keeps him onside), so the switch is on, and he stays patient until it comes.

@export_group("Far side")
## the ball this far over on the other side
@export var ball_z := 9.0
@export var width := 28.0
## how far ahead of the ball he waits (m), at most
@export var ahead := 14.0

func _init() -> void:
	priority = 4
	roles = PackedStringArray(["LW", "RW"])
	when = SUPPORT

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if f.lock > 0.0 or c.box_jobs.has(f) or c.countering: return false
	return absf(c.ball.y) > ball_z and signf(c.ball.y) != signf(f.slot.y) and c.depth(c.ball) > 0.35

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var i := AiIntent.new()
	i.move_to = Vector2(minf(c.ball.x * c.dir + ahead, MatchGame.HALF_L - 8.0) * c.dir, signf(f.slot.y) * width)
	i.speed = c.s.jog_factor
	i.note = "far side, wide"
	return i
