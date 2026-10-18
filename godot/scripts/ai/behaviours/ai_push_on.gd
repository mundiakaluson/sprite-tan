class_name AiPushOn
extends AiBehaviour
## "Pushing on" (FIFA football language; catalogue full back "Push on", winger "Press their full back"): a pass is travelling to an opponent near him on his side;
## he reads it and gets to the receiver as the ball arrives (touch-tight, goal side), or steps in front and intercepts when he gets there first.

@export_group("Push on")
## the receiver within this far of him, and the ball still at least this long (s) from the receiver
@export var reach := 12.0
@export var min_eta := 0.5
## he goes when he can be there by the time the ball is (his run time <= ball time x this)
@export_range(0.5, 2.0) var arrive_k := 0.95
@export var goal_side := 1.0
## only for a pass out to the flank (receiver this far from the middle)
@export var flank_z := 13.0

static var stat_push := 0

func _init() -> void:
	priority = -7
	roles = PackedStringArray(["LB", "RB", "LW", "RW"])
	when = LOOSE

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var r := c.game.pass_target
	if r == null or r.team == c.team or f.lock > 0.0: return false
	if r.pos.distance_to(f.pos) > reach or absf(r.pos.y) < flank_z: return false
	var v := c.ball_vel.length()
	if v < 2.0: return false
	var eta := c.ball.distance_to(r.pos) / v
	if eta < min_eta: return false
	var mine := f.pos.distance_to(r.pos) / maxf(f.top_speed() * c.s.sprint_factor, 0.1)
	if mine > eta * arrive_k: return false
	for m in c.team.players:                                                     # only the nearest of us goes
		if m != f and not m.is_keeper() and m.pos.distance_to(r.pos) < f.pos.distance_to(r.pos) - 0.5: return false
	return true

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var r := c.game.pass_target
	var i := AiIntent.new()
	var on_line := Geometry2D.get_closest_point_to_segment(f.pos, c.ball, r.pos)
	var tight := r.pos + (c.own_goal() - r.pos).normalized() * goal_side
	i.move_to = on_line if f.pos.distance_to(on_line) < 1.5 else tight             # in front of him if he can, else on his back
	i.speed = c.s.sprint_factor
	i.note = "push on"
	stat_push += 1
	return i
