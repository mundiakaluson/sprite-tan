class_name EngagementView
extends RefCounted
## What an engagement shows in the HUD (stage 1, plain): the current-command box counts down the pick ("DUEL 1.8") and rings the
## opponent, the hand greys out the cards that do not fit, the reveal shows both picks in the message line ("ELASTICO  vs  STAND TACKLE").
## The proper engagement UI (scene, card reveal animation) is stage 2.

var g: MatchGame
var _mask_on := false

func _init(game: MatchGame) -> void:
	g = game
	g.engage.revealed.connect(_on_reveal)
	g.engage.finished.connect(_on_finish)

func update() -> void:
	var e := g.engage.current
	if e == null or e.step != Engagement.Step.CHOOSE or not e.involves_team(g.home): return
	var me := e.player_of(g.home)
	var them := e.challenger if me == e.ball else e.ball
	var what := "ATTACK" if me == e.ball else "DEFEND"
	if g.engage.waiting_for(g.home):
		g.command.show("card", "%s %s  %.1f" % [e.type.to_upper(), what, g.engage.time_left()], me, them, "pick a card, or wait for the free default", 0.0)
		if not _mask_on:
			var mask: Array = []
			for c in g.cards.hand_of(g.home): mask.append(g.cards.can_play(g.home, c, e))
			g.hud.set_playable(mask)
			_mask_on = true
	elif g.home.engage_auto:
		g.command.show("card", "%s %s  AUTO" % [e.type.to_upper(), what], me, them, "", 0.0)

func _on_reveal(e: Engagement) -> void:
	_clear_mask()
	if g.hud != null: g.hud.message("%s  vs  %s" % [EngageCard.label(e.card_of(e.ball.team), "KEEP IT"), EngageCard.label(e.card_of(e.challenger.team), "STAND")], g.settings.engage_reveal_time + 0.6)

func _on_finish(e: Engagement) -> void:
	_clear_mask()
	if e.involves_team(g.home):
		var won := (e.outcome == "ball") == (e.ball.team == g.home)
		var txt: String = {"ball": "BEAT HIM", "challenge": "WON IT", "loose": "LOOSE BALL", "foul": "FOUL", "cancelled": ""}.get(e.outcome, "")
		if txt != "": g.command.show("card", txt, e.player_of(g.home), null, ("won" if won else "lost") if e.outcome in ["ball", "challenge"] else "", g.settings.command_hold)

func _clear_mask() -> void:
	if _mask_on:
		g.hud.set_playable([])
		_mask_on = false
