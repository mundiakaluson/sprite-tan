class_name Footballer
extends RefCounted
## One player inside the match: his data row, the Player node (just the picture) and the match state.
## Positions are metres on the pitch: Vector2(x along the pitch, z across). Team.dir says which way his team attacks.

var row := {}
var node: Player
var team: Team
var role := "CM"
var style := ""                 ## formation style (data/styles.csv): fullback, wingback, anchor, poacher, ...
var slot := Vector2.ZERO        ## home position (metres), already turned for the team's side
var pos := Vector2.ZERO
var vel := Vector2.ZERO
var want := Vector2.ZERO        ## the velocity he is trying for this frame (AI or an order sets it)
var face := Vector2.RIGHT
var no_touch := 0.0             ## seconds he cannot win the ball (just kicked it, just lost it)
var lock := 0.0                 ## seconds committed to an animation (kick, skill, tackle)
var shield := 0.0               ## seconds nobody can tackle him (dribble cards)
var think := 0.0                ## AI decision timer
var hold := 0.0                 ## seconds he has held the ball
var carried := 0.0              ## metres he has carried the ball since he got it
var clip := ""
var pending := Callable()       ## runs when the animation reaches its strike point
var pending_t := 0.0
var aim := Vector2.ZERO          ## he is pivoting to face this way before a kick (MatchKicking)
var aim_done := Callable()      ## runs when the pivot is finished; empty = not pivoting
var aim_t := 0.0
var glide := false               ## kicking on the move: he keeps his speed through the clip (slows gently) instead of stopping
var mirror := false              ## play his clip mirrored (a left dive: the keeper clips are authored for the right)
var ball_rel := Vector3.ZERO     ## the ball's velocity relative to him while it settles (a damped spring, so a pass rolls to his foot instead of snapping)
var settle := 0.0               ## seconds left of the ball easing to his feet after he got it
var ai := {}                    ## memory of the AI interaction layer (space target, ...)
var order := {}                 ## an order from the human: {kind: "run" / "press", target, t}; empty = play by himself

func stat(key: String, d := 60) -> int:
	return Data.inum(row.get(key), d)

func is_keeper() -> bool:
	return role == "GK"

func top_speed() -> float:
	var s := MatchSettings.current if MatchSettings.current != null else MatchSettings.new()
	if is_keeper(): return s.keeper_speed
	return s.speed_base + stat("PAC", 60) * s.speed_per_pac

func display_name() -> String:
	return str(row.get("name", "?"))
