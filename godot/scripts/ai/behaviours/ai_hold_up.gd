class_name AiHoldUp
extends AiBehaviour
## Hold-up play (catalogue section 10 "Hold up and shield"): a striker with his back to goal and a defender tight on him, and nobody yet to lay it off to,
## shields it: side-on, low, the ball on his far foot, the defender held off (harder to tackle: MatchPossession reads f.ai.shielding, stronger with PHY)
## for up to `max_hold` s while the midfield arrives; AiLayOff then plays the lay-off. A target man (PHY) holds it longer.

@export_group("Hold up")
@export var tight := 2.4
@export_range(-1.0, 1.0) var back_to_goal := 0.2
## seconds he holds it at PHY 50 and at PHY 90
@export var hold_low := 0.8
@export var hold_high := 2.2

static var stat_holds := 0

func _init() -> void:
	priority = 3
	roles = PackedStringArray(["ST"])
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.game.kicking.busy(f) or f.lock > 0.0: return false
	var o := c.nearest_opponent(f.pos)
	if o == null or o.pos.distance_to(f.pos) > tight or f.face.dot((c.goal() - f.pos).normalized()) > back_to_goal:
		f.ai.erase("shielding")
		return false
	var limit := lerpf(hold_low, hold_high, clampf((f.stat("PHY", 60) - 50.0) / 40.0, 0.0, 1.0))
	if f.hold > limit:
		f.ai.erase("shielding")
		return false
	return true

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var o := c.nearest_opponent(f.pos)
	var i := AiIntent.new()
	var away := (f.pos - o.pos).normalized()
	f.face = away                                                               # body between the man and the ball
	i.move_to = f.pos + away * 0.4
	i.speed = 0.3
	if not f.ai.get("shielding", false): stat_holds += 1
	f.ai["shielding"] = true
	i.note = "hold up"
	return i
