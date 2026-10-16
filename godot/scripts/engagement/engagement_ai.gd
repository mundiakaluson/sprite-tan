class_name EngagementAi
extends RefCounted
## The AI manager's pick in an engagement (the away side, and the home side on Auto). It sees only what a human could:
## its own hand and cooldowns and the two players' stats, never the other side's pick. Mixed: it does not always play its best card,
## and sometimes keeps its cards (MatchSettings > Engagements: engage_ai_play, engage_ai_temp). Stage 1 version; the full opponent manager comes later.

var g: MatchGame

func _init(game: MatchGame) -> void:
	g = game

## the card row to play, or {} for the free default
func pick(e: Engagement, team: Team) -> Dictionary:
	var s := g.settings
	var opts := g.cards.playable(team, e)
	if opts.is_empty() or g.rng.randf() > s.engage_ai_play: return {}
	var me := e.player_of(team)
	var them := e.challenger if me == e.ball else e.ball
	var fallback_them := "DEF" if them == e.challenger else "DRI"
	var weights: Array[float] = []
	var total := 0.0
	for c in opts:
		var a := EngageCard.stat(me, c, "DRI")
		var d := EngageCard.stat(them, {}, fallback_them)
		var p := clampf(Data.num(c["succ"], 60.0) + s.engage_k * (a - d), s.engage_p_min, s.engage_p_max) / 100.0
		var value := p * (1.0 + 0.25 * (EngageCard.effect_num(c, "strand") - 1.0)) - Data.num(c["risk"], 10.0) / 100.0 * (1.0 - p) * 0.5
		if EngageCard.effect_str(c, "move") == "foul":
			var depth := clampf((e.ball.pos.x * e.ball.team.dir + MatchGame.HALF_L) / (2.0 * MatchGame.HALF_L), 0.0, 1.0)
			if depth < s.engage_ai_foul_depth: value *= s.engage_ai_foul_k
		var w := exp(value / maxf(s.engage_ai_temp, 0.01))
		weights.append(w)
		total += w
	var r := g.rng.randf() * total
	for i in opts.size():
		r -= weights[i]
		if r <= 0.0: return opts[i]
	return opts[opts.size() - 1]
