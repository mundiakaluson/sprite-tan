class_name AiJockey
extends AiBehaviour
## Example behaviour: the defender nearest to the ball carrier does not dive in, he backs off goal-side and keeps a gap (jockeying) until help arrives.
## Copy this file to make your own: change `wants()` (when) and `act()` (what), keep the exports for the numbers.

@export_group("Jockey")
## only when the carrier is closer than this (metres)
@export var max_range := 12.0
## only when the carrier is further than this: closer than that and the normal press takes over
@export var min_range := 2.5
## he keeps this far from the carrier, on the goal side
@export var gap := 3.0
## only while the carrier is in his own half of the pitch (false = anywhere)
@export var own_half_only := true

func _init() -> void:
	roles = PackedStringArray(["CB", "LB", "RB"])
	when = DEFENDING

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var carrier := c.carrier
	if carrier == null: return false
	var d := f.pos.distance_to(carrier.pos)
	if d > max_range or d < min_range: return false
	if own_half_only and (carrier.pos.x - c.own_goal().x) * c.dir > 52.0: return false     # carrier past the halfway line
	for m in c.team.players:                                                                   # he must be the nearest of us
		if m != f and not m.is_keeper() and m.pos.distance_to(carrier.pos) < d: return false
	return true

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var carrier := c.carrier
	var i := AiIntent.new()
	i.move_to = c.clamp_pitch(carrier.pos + (c.own_goal() - carrier.pos).normalized() * gap, 1.0)
	i.speed = clampf(carrier.vel.length() / maxf(f.top_speed(), 0.1) + 0.15, c.s.jog_factor, c.s.sprint_factor)     # keeps pace, never faster than he needs
	i.note = "jockey"
	return i
