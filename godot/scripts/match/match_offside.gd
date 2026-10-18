class_name MatchOffside
extends RefCounted
## The offside law (law 11), judged the real way: the moment a player plays the ball, every team mate who is in the opponents' half, nearer their goal line than the
## ball AND than the second-last opponent (the keeper usually being the last) is marked. If a marked player is the next to touch the ball he is offside: indirect
## free kick to the defenders where he touched it. Any other touch (an opponent, an onside team mate, the passer again) clears the marks. No offside from a throw-in,
## goal kick or corner (MatchSettings > Offside > offside_free_restarts).
## A marked player who KNOWS he is offside (by game sense) leaves the ball alone; the AI reads aware(f). Numbers: MatchSettings > Offside.

var g: MatchGame
var marked := {}            ## Footballer -> true if he knows he is offside (and leaves it), false if he does not
var passer: Footballer
var stat_calls := 0         ## offside given
var stat_marked := 0        ## kicks that left at least one team mate offside
var stat_by_role := {}
var log: Array[String] = []

func _init(game: MatchGame) -> void:
	g = game

func clear() -> void:
	marked.clear()
	passer = null

## is f standing offside right now if `kicker` played the ball (used by the AI too: c.game.offside.would_be(f))
func would_be(f: Footballer, ball_x: float) -> bool:
	var dir := f.team.dir
	var t := f.pos.x * dir
	if t <= 0.0: return false                                         # own half
	var tol := g.settings.offside_tolerance
	return t > ball_x * dir + tol and t > second_last(f.team) + tol

## team frame x (x * dir of `attacking`) of the opponents' second-last player: the offside line
func second_last(attacking: Team) -> float:
	var other := g.away if attacking == g.home else g.home
	var a := -1e9
	var b := -1e9
	for o in other.players:
		var t := o.pos.x * attacking.dir
		if t > a:
			b = a
			a = t
		elif t > b: b = t
	return b

## the ball was just played by f (kick released). `restart` = the restart this kick took ("" in open play)
func played(f: Footballer, restart: String) -> void:
	marked.clear()
	passer = f
	if not g.settings.offside_on or restart in g.settings.offside_free_restarts: return
	var bx := g.ball.phys.pos.x
	for m in f.team.players:
		if m == f or not would_be(m, bx): continue
		marked[m] = g.rng.randf() < _aware_chance(m)
	if not marked.is_empty(): stat_marked += 1

func is_marked(f: Footballer) -> bool:
	return marked.has(f)

## marked and knows it: the AI keeps him off the ball
func aware(f: Footballer) -> bool:
	return bool(marked.get(f, false))

func _aware_chance(f: Footballer) -> float:
	var s := g.settings
	var sense := (f.stat("PAS", 60) + f.stat("DRI", 60)) * 0.5
	return clampf((sense - s.offside_aware_min) / maxf(s.offside_aware_span, 1.0), s.offside_aware_floor, s.offside_aware_cap)

## f touches the ball. Returns true when that is an offside offence (the free kick is given; the caller must not go on with the touch)
func touched(f: Footballer) -> bool:
	if marked.is_empty(): return false
	if marked.has(f) and g.phase == MatchGame.Phase.PLAY:
		_whistle(f)
		return true
	clear()
	return false

func _whistle(f: Footballer) -> void:
	stat_calls += 1
	stat_by_role[f.role] = int(stat_by_role.get(f.role, 0)) + 1
	log.append("%5.0f  %s (%s) offside, pass by %s" % [g.clock, f.display_name(), f.role, passer.display_name() if passer != null else "?"])
	var spot := f.pos
	var defending := g.away if f.team == g.home else g.home
	clear()
	g.rules.free_kick(defending, spot, "OFFSIDE  %s" % f.display_name(), true)
	g.rules.appeal(defending, spot)

func stats() -> Dictionary:
	return {"calls": stat_calls, "kicks_with_offside_players": stat_marked, "by_role": stat_by_role}
