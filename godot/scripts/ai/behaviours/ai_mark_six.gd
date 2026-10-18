class_name AiMarkSix
extends AiBehaviour
## The 10 takes their 6 (catalogue section 8 "Mark their 6"): while they build up from the back, our attacking midfielder shadows their holding midfielder,
## goal side of him and on the line from the ball, so their centre backs cannot play into him and have to go wide or long.

@export_group("Mark the 6")
@export var goal_side := 2.0
## only while their carrier is in their own half
@export_range(0.0, 1.0) var max_depth := 0.5

func _init() -> void:
	priority = 3
	roles = PackedStringArray(["CAM"])
	when = DEFENDING

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	if c.carrier == null or f == c.presser or f.lock > 0.0: return false
	if c.depth(c.carrier.pos) < 1.0 - max_depth: return false                   # (depth is in our frame: their half is our far half)
	return _six(c) != null

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var s := _six(c)
	var i := AiIntent.new()
	var shadow := s.pos + (c.carrier.pos - s.pos).normalized() * goal_side * 0.6 + (c.own_goal() - s.pos).normalized() * goal_side * 0.4
	i.move_to = shadow
	i.speed = c.s.jog_factor if f.pos.distance_to(shadow) < 5.0 else c.s.sprint_factor
	i.note = "mark the 6"
	return i

func _six(c: AiContext) -> Footballer:
	var best: Footballer = null
	var bd := 1e9
	for o in c.other.players:
		if o.role != "CDM" or o == c.carrier: continue
		var d := o.pos.distance_to(c.carrier.pos)
		if d < bd:
			bd = d
			best = o
	return best
