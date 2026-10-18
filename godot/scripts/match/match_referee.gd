class_name MatchReferee
extends RefCounted
## Fouls, advantage and cards (behaviour catalogue section 12 "Referee and fouls", batch 5). A failed tackle, a missed slide, an engagement foul or a deliberate
## pull-back may be a foul. The referee plays advantage when the fouled side still has the ball going forward; otherwise a free kick where it happened, or a
## penalty when it was inside the offender's own box. Cards by how bad it was (a tactical foul is a yellow); a second yellow sends him off (he leaves the pitch).
## Numbers: MatchSettings > Referee.

var g: MatchGame
var stat := {}                      ## "fouls", "advantage", "free_kicks", "penalties", "yellows", "reds", "tactical"
var log: Array[String] = []

func _init(game: MatchGame) -> void:
	g = game

func _count(k: String) -> void:
	stat[k] = int(stat.get(k, 0)) + 1

## chance that this challenge was a foul: kind "tackle" (standing, missed), "slide" (missed), "behind" is worked out from the angle
func foul_chance(tackler: Footballer, victim: Footballer, kind: String) -> float:
	var s := g.settings
	var base := s.foul_tackle if kind == "tackle" else s.foul_slide
	if _in_own_box(tackler.team, victim.pos): base *= s.foul_box_care
	var from_behind := victim.face.dot((tackler.pos - victim.pos).normalized()) < -0.4
	if from_behind: base += s.foul_behind
	return clampf(base * (1.3 - tackler.stat("DEF", 60) / 100.0), 0.0, 0.95)

## a challenge went wrong: maybe a foul (rolled here)
func challenge(tackler: Footballer, victim: Footballer, kind: String) -> void:
	if g.phase != MatchGame.Phase.PLAY or tackler.team == victim.team: return
	if g.rng.randf() < foul_chance(tackler, victim, kind): foul(tackler, victim, kind)

## a foul by `by` on `on`
func foul(by: Footballer, on: Footballer, kind: String) -> void:
	if g.phase != MatchGame.Phase.PLAY: return
	var s := g.settings
	_count("fouls")
	if kind == "tactical": _count("tactical")
	var behind := on.face.dot((by.pos - on.pos).normalized()) < -0.4
	var card := s.card_tactical if kind == "tactical" else (s.card_slide if kind == "slide" else s.card_tackle) + (s.card_behind if behind else 0.0)
	var yellow := g.rng.randf() < card
	var in_box := _in_own_box(by.team, on.pos)
	log.append("%5.0f  %s (%s) on %s: %s%s%s" % [g.clock, by.display_name(), kind, on.display_name(), "penalty" if in_box else "foul", "  yellow" if yellow else "", ""])
	# advantage: the fouled side still has it, in the opponents' half, and nobody is on him
	var keeps := g.carrier != null and g.carrier.team == on.team
	if keeps and not in_box and not yellow and (g.carrier.pos.x * on.team.dir) > s.advantage_from and _space(g.carrier) > s.advantage_space:
		_count("advantage")
		g.hud.toast("ADVANTAGE")
		return
	if yellow: _book(by)
	if in_box:
		_count("penalties")
		var spot := Vector2(-by.team.dir * (MatchGame.HALF_L - 11.0), 0.0)
		g.rules.restart("penalty", on.team, spot, "PENALTY", _best_taker(on.team))
	else:
		_count("free_kicks")
		g.rules.free_kick(on.team, on.pos, "FOUL  %s" % by.display_name())

func _in_own_box(t: Team, p: Vector2) -> bool:
	return p.x * t.dir < -MatchGame.HALF_L + 16.5 and absf(p.y) < 20.16

func _space(f: Footballer) -> float:
	var best := 99.0
	for o in g.all:
		if o.team != f.team: best = minf(best, o.pos.distance_to(f.pos))
	return best

func _best_taker(t: Team) -> Footballer:
	var best: Footballer = null
	for f in t.players:
		if f.is_keeper(): continue
		if best == null or f.stat("SHO", 60) > best.stat("SHO", 60): best = f
	return best

func yellows(f: Footballer) -> int:
	return int(f.ai.get("yellow", 0))

func _book(f: Footballer) -> void:
	f.ai["yellow"] = yellows(f) + 1
	_count("yellows")
	if yellows(f) >= 2:
		_count("reds")
		g.hud.message("RED CARD  %s" % f.display_name(), 1.6)
		send_off(f)
	else:
		g.hud.toast("YELLOW  %s" % f.display_name())

## off the pitch: out of his team and the match lists, picture hidden
func send_off(f: Footballer) -> void:
	if g.carrier == f: g.carrier = null
	if g.pass_target == f: g.pass_target = null
	f.team.players.erase(f)
	g.all.erase(f)
	f.order = {}
	if f.node != null: f.node.visible = false
	if g.selected == f: g.selected = null

func stats() -> Dictionary:
	return stat
