class_name AiWideDuel
extends AiBehaviour
## The full back against the winger (behaviour catalogue section 5: "1v1 approach", "2v1", "Stop the cross").
## Their carrier on his flank, coming at him: fast-slow-sideways-low. He closes quickly, then slows at about an arm's length, side-on, goal side and a little
## INSIDE him (the back foot in line with the ball) so the winger can only go down the line; near the byline he stands across the crossing lane.
## A second attacker overlapping (2v1): he drops off between the two and delays, showing the pass down the line, until help arrives. Tackling is left to AiTackle.

@export_group("Wide duel")
## the carrier is on his flank (this far from the middle) within this far of him
@export var flank_z := 12.0
@export var engage_dist := 14.0
## arm's length (m), and how far inside (towards the middle) he leans to show him down the line
@export var hold_dist := 1.6
@export var inside := 0.8
## close at a sprint until this far away, then he slows
@export var close_until := 4.0
## 2v1: a second attacker within this far of the carrier, further forward or level: he drops off this far and splits them
@export var overlap_dist := 12.0
@export var split_back := 3.5
## near the byline (this far from it) he stands across the crossing lane instead
@export var byline_x := 10.0

static var stat_duels := 0
static var stat_two_v_one := 0

func _init() -> void:
	priority = -6
	roles = PackedStringArray(["LB", "RB"])
	when = DEFENDING

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var k := c.carrier
	if k == null or f.lock > 0.0 or c.game.dribble.busy(f): return false
	if absf(k.pos.y) < flank_z or signf(k.pos.y) != signf(f.slot.y): return false
	if k.pos.distance_to(f.pos) > engage_dist: return false
	return (k.pos.x - f.pos.x) * c.dir > -3.0                                 # he is in front of me or level, not already gone

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var k := c.carrier
	var goal := c.own_goal()
	var i := AiIntent.new()
	var to_goal := (goal - k.pos).normalized()
	var inward := Vector2(0.0, -signf(k.pos.y))
	var spot := k.pos + (to_goal + inward * inside).normalized() * hold_dist
	var mate := _overlap(k, c)
	if mate != null:                                                           # 2v1: between them, a step deeper, delaying
		spot = k.pos.lerp(mate.pos, 0.35) + to_goal * split_back
		stat_two_v_one += 1
	elif MatchGame.HALF_L - absf(k.pos.x) < byline_x:                          # at the byline: across the crossing lane
		var mouth := Vector2(goal.x + c.dir * 6.0, 0.0)
		spot = k.pos + (mouth - k.pos).normalized() * hold_dist
	var d := f.pos.distance_to(spot)
	i.move_to = spot
	i.speed = c.s.sprint_factor if d > close_until else c.s.jog_factor * 0.6       # fast, then slow
	f.ai["look"] = (k.pos - f.pos).normalized()                                # side-on, eyes on the ball
	f.ai["look_until"] = c.game.clock + c.game_s(0.2)
	i.note = "wide duel"
	if d < 0.6: stat_duels += 1
	return i

func _overlap(k: Footballer, c: AiContext) -> Footballer:
	for o in c.other.players:
		if o == k or o.is_keeper(): continue
		if o.pos.distance_to(k.pos) < overlap_dist and (o.pos.x - k.pos.x) * -c.dir >= -1.0 and absf(o.pos.y) > 8.0: return o
	return null
