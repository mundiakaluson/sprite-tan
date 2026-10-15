class_name Footballer
extends RefCounted
## One player inside the match: his data row, the Player node (just the picture) and the match state.
## Positions are metres on the pitch: Vector2(x along the pitch, z across). Team.dir says which way his team attacks.

var row := {}
var node: Player
var team: Team
var role := "CM"
var slot := Vector2.ZERO        ## home position (metres), already turned for the team's side
var pos := Vector2.ZERO
var vel := Vector2.ZERO
var want := Vector2.ZERO        ## the velocity he is trying for this frame (AI or keyboard sets it)
var face := Vector2.RIGHT
var no_touch := 0.0             ## seconds he cannot win the ball (just kicked it, just lost it)
var lock := 0.0                 ## seconds committed to an animation (kick, skill, tackle)
var shield := 0.0               ## seconds nobody can tackle him (dribble cards)
var think := 0.0                ## AI decision timer
var hold := 0.0                 ## seconds he has held the ball (the keeper)
var clip := ""
var pending := Callable()       ## runs when the animation reaches its strike point
var pending_t := 0.0
var order := {}                 ## an order from the human: {kind: "run" / "press", target, t}; empty = play by himself

func stat(key: String, d := 60) -> int:
	return Data.inum(row.get(key), d)

func is_keeper() -> bool:
	return role == "GK"

func top_speed() -> float:
	if is_keeper(): return 5.5
	return 5.2 + stat("PAC", 60) * 0.038

func display_name() -> String:
	return str(row.get("name", "?"))
