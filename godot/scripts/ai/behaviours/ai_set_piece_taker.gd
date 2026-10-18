class_name AiSetPieceTaker
extends AiBehaviour
## The taker of a restart plays it as the set piece it is (behaviour catalogue section 11, batch 5):
##  corner: a lofted cross to the best header in the box who has the least company (now and then short to the man at the flag);
##  free kick: central and in range -> a direct shot (a curler over the wall, aimed at the far side of the goal); wide -> a cross into the line of runners;
##   further out -> a normal pass;
##  goal kick: short to a split centre back when nobody is on him, else long to the striker / a full back;
##  throw-in: to the freest of the short options (a long throw into the box from the last quarter with a strong thrower);
##  penalty: placed or powered by SHO, to a corner the keeper may not reach.
## The kick itself is the normal pass / lob / shot (throws are played as passes until there is a throw clip).

@export_group("Corners")
@export_range(0.0, 1.0) var short_corner := 0.13
@export var corner_crowd := 3.0
@export_group("Free kicks")
## shoot from within this (m) of goal when no more than shoot_z across
@export var shoot_range := 26.0
@export var shoot_z := 15.0
## a cross from wide within this of the goal line
@export var cross_range := 38.0
@export_group("Goal kicks")
## short when the centre back has nobody within this (m)
@export var short_free := 9.0
@export_group("Throw-ins")
## a long throw into the box from within this of the goal line by a thrower with PHY of at least long_phy
@export var long_throw_range := 26.0
@export var long_throw_phy := 76
@export_group("Penalties")
@export var pen_corner_z := 2.9
@export var pen_power_sho := 80

static var stat := {}

func _init() -> void:
	priority = -25
	when = WITH_BALL

func wants(f: Footballer, c: AiContext, _role: AiRole) -> bool:
	var r := c.game.rules
	return r.is_taker(f) and c.game.phase == MatchGame.Phase.PLAY and not c.game.kicking.busy(f) and f.lock <= 0.0 and r.kind != "kickoff"

func act(f: Footballer, c: AiContext, role: AiRole, _dt: float) -> AiIntent:
	var r := c.game.rules
	var i := AiIntent.new()
	i.move_to = f.pos
	var kind := r.kind
	match kind:
		"corner": _corner(f, c, i)
		"free_kick": _free_kick(f, c, i, role)
		"goal_kick": _goal_kick(f, c, i)
		"throw_in": _throw(f, c, i)
		"penalty": _penalty(f, c, i)
	if i.action == "": return null                                             # nothing special: the role plays it
	stat["%s %s" % [kind, i.note]] = int(stat.get("%s %s" % [kind, i.note], 0)) + 1
	return i

func _box_target(f: Footballer, c: AiContext) -> Footballer:
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f or m.is_keeper(): continue
		var mt := MatchGame.HALF_L - m.pos.x * c.dir
		if mt > 14.0 or absf(m.pos.y) > 11.0: continue
		var crowd := 0
		for o in c.other.players:
			if o.pos.distance_to(m.pos) < corner_crowd: crowd += 1
		var sc := m.stat("PHY", 60) * 0.05 - crowd * 1.5 + c.game.rng.randf_range(0.0, 1.5)
		if sc > bs:
			bs = sc
			best = m
	return best

func _corner(f: Footballer, c: AiContext, i: AiIntent) -> void:
	var g := c.game
	if g.rng.randf() < short_corner:
		for m in c.team.players:
			if m != f and m.pos.distance_to(f.pos) < 14.0 and c.pressure(m.pos) > 2.5:
				i.action = "pass"
				i.target = m
				i.note = "short"
				return
	var t := _box_target(f, c)
	if t != null:
		i.action = "lob"
		i.target = t
		i.note = "cross"
		AiBox.on_delivery(c, "corner")

func _free_kick(f: Footballer, c: AiContext, i: AiIntent, _role: AiRole) -> void:
	var goal := c.goal()
	var d: float = f.pos.distance_to(goal)
	if d < shoot_range and absf(f.pos.y) < shoot_z and not c.game.rules.indirect:
		var far := -signf(f.pos.y if absf(f.pos.y) > 0.5 else (1.0 if c.game.rng.randf() < 0.5 else -1.0))
		i.action = "shoot"
		i.aim = Vector2(goal.x, far * (MatchGame.GOAL_HALF - 0.7))
		i.style = "K02" if far * c.dir < 0.0 else "K03"
		i.note = "direct"
		return
	if d < cross_range and absf(f.pos.y) >= shoot_z * 0.6:
		var t := _box_target(f, c)
		if t != null:
			i.action = "lob"
			i.target = t
			i.note = "cross"
			AiBox.on_delivery(c, "free kick")

func _goal_kick(f: Footballer, c: AiContext, i: AiIntent) -> void:
	var best: Footballer = null
	var room := 0.0
	for m in c.team.players:
		if m.role != "CB": continue
		var p := c.pressure(m.pos)
		if p > room:
			room = p
			best = m
	if best != null and room > short_free:
		i.action = "pass"
		i.target = best
		i.note = "short"
		return
	var long_t: Footballer = null
	var ls := -1e9
	for m in c.team.players:
		if not (m.role in ["ST", "LB", "RB", "LW", "RW"]): continue
		var sc := c.pressure(m.pos) + m.stat("PHY", 60) * 0.05 + (m.pos.x - f.pos.x) * c.dir * 0.03
		if sc > ls:
			ls = sc
			long_t = m
	if long_t != null:
		i.action = "lob"
		i.target = long_t
		i.note = "long"

func _throw(f: Footballer, c: AiContext, i: AiIntent) -> void:
	var to_line := MatchGame.HALF_L - f.pos.x * c.dir
	if to_line < long_throw_range and f.stat("PHY", 60) >= long_throw_phy:
		var t := _box_target(f, c)
		if t != null:
			i.action = "lob"
			i.target = t
			i.note = "long throw"
			AiBox.on_delivery(c, "long throw")
			return
	var best: Footballer = null
	var bs := -1e9
	for m in c.team.players:
		if m == f or m.is_keeper(): continue
		var d: float = m.pos.distance_to(f.pos)
		if d > 22.0: continue
		var sc := c.pressure(m.pos) * 1.5 - d * 0.15 + (m.pos.x - f.pos.x) * c.dir * 0.1
		if c.lane_blocked(f.pos, m.pos, 1.2): sc -= 10.0
		if sc > bs:
			bs = sc
			best = m
	if best != null:
		i.action = "pass"
		i.target = best
		i.note = "short"

func _penalty(f: Footballer, c: AiContext, i: AiIntent) -> void:
	var goal := c.goal()
	var side := 1.0 if c.game.rng.randf() < 0.5 else -1.0
	var power := f.stat("SHO", 60) >= pen_power_sho and c.game.rng.randf() < 0.35
	i.action = "shoot"
	i.aim = Vector2(goal.x, side * (pen_corner_z if not power else 1.2))
	i.style = "K09" if power else ""
	i.note = "power" if power else "placed"
