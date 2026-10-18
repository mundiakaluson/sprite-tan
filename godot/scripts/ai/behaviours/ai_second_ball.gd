class_name AiSecondBall
extends AiBehaviour
## Second balls (catalogue section 6 "Second balls", Spielverlagerung "the art of the long ball"): a high ball is coming down and two others contest it
## (MatchAerial). Midfielders not in the duel stand staggered around where the header will drop: one a few metres short of it, one beside it, so whichever
## way it is flicked, one of ours is first to the bounce.

@export_group("Second ball")
@export var within := 26.0
## spots around the contest: short of it (towards our goal), and to the side
@export var short := 6.0
@export var side := 7.0

static var stat_frames := 0

func _init() -> void:
	priority = -8
	roles = PackedStringArray(["CDM", "CM", "CAM"])
	when = LOOSE

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var a := c.game.aerial
	if not a.active() or a.spot_for(f) != Vector2.INF or f.lock > 0.0: return false
	var spot: Vector2 = a.ev.get("contest", Vector2.INF)
	if spot == Vector2.INF or f.pos.distance_to(spot) > within: return false
	return _slot(f, c) >= 0

func act(f: Footballer, c: AiContext, _role: AiRole, _dt: float) -> AiIntent:
	var spot: Vector2 = c.game.aerial.ev["contest"]
	var k := _slot(f, c)
	var back := (c.own_goal() - spot).normalized()
	var p := spot + back * short if k == 0 else spot + back * 2.0 + Vector2(0.0, side * (1.0 if spot.y < 0.0 else -1.0))
	var i := AiIntent.new()
	i.move_to = c.clamp_pitch(p, 1.0)
	i.speed = c.s.sprint_factor
	i.note = "second ball"
	stat_frames += 1
	return i

## 0 = short of it, 1 = beside it, -1 = not one of the two nearest of our midfielders
func _slot(f: Footballer, c: AiContext) -> int:
	var spot: Vector2 = c.game.aerial.ev["contest"]
	var list: Array = []
	for m in c.team.players:
		if m.role in roles and c.game.aerial.spot_for(m) == Vector2.INF: list.append(m)
	list.sort_custom(func(a, b): return a.pos.distance_to(spot) < b.pos.distance_to(spot))
	return list.slice(0, 2).find(f)
