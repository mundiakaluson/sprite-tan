class_name Engagement
extends RefCounted
## One engagement in progress: the type, the two players, who started it and with what, each side's pick and the result.
## Made and run by EngagementDirector; resolved by the resolver for its type (DuelResolver for "duel").

enum Step { CHOOSE, REVEAL, ZAP, DONE }      ## ZAP: a card's effect plays out before the duel resolves (Double Team's helper on his way)

var type := "duel"
var ball: Footballer              ## the ball side's player (the carrier)
var challenger: Footballer        ## the challenge side's player
var helper: Footballer = null    ## a team mate brought in by a card (Double Team)
var initiator: Footballer         ## who started it in the sim (the carrier taking him on, or the defender going in)
var move := ""                    ## what the initiator was doing: "takeon", "tackle", "slide"
var step := Step.CHOOSE
var t := 0.0                      ## real seconds in this step
var picks := {}                   ## Team -> card row (empty Dictionary = the free default); a team is in here once it has chosen
var outcome := ""                 ## after resolve: "ball", "challenge", "loose", "foul", "cancelled"
var note := ""                    ## a line for the HUD / tests (what happened)
var start_clock := 0.0

func ball_team() -> Team:
	return ball.team

func challenge_team() -> Team:
	return challenger.team

func side_of(team: Team) -> String:
	return "ball" if team == ball.team else "challenge"

func player_of(team: Team) -> Footballer:
	return ball if team == ball.team else challenger

func involves(f: Footballer) -> bool:
	return f == ball or f == challenger or (helper != null and f == helper)

func involves_team(team: Team) -> bool:
	return team == ball.team or team == challenger.team

func picked(team: Team) -> bool:
	return picks.has(team)

func card_of(team: Team) -> Dictionary:
	return picks.get(team, {})
