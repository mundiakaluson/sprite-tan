class_name AiTrait
extends Resource
## A personal habit of a player, on top of his role (players.csv column `traits`, ids separated by space or |). The AI interaction layer (ai_interact.gd) applies it after the role has decided.
## One trait now: "roamer" (the Messi type): does not track back, walks slowly in space ahead of the ball while the team defends, ready for the quick counter,
## and drifts into free space instead of standing in his slot when the team attacks. Add more by adding exports here and a branch in AiInteract.post().

@export var id := "roamer"
@export var label := "ROAMER"
@export_group("Defending (the opponent has the ball)")
## he moves at this fraction of full speed (walks, saving himself)
@export_range(0.1, 1.0) var walk_factor := 0.35
## stands this far ahead of the ball (metres, towards the opponent goal) ...
@export var counter_ahead := 14.0
## ... but never deeper than this (team frame x, 0 = halfway line)
@export var counter_min_x := -6.0
## looks for the freest spot within this radius of that point
@export var counter_radius := 6.0
## pulled this much towards the ball's side of the pitch (0 = stays on his own side)
@export_range(0.0, 1.0) var lateral_pull := 0.25
## the nearest-player-presses rule skips him (he never closes down)
@export var exempt_press := true
@export_group("Attacking")
## drifts into the freest spot near where his role would stand, instead of the slot
@export var roam_in_attack := true
@export var roam_radius := 10.0
## looks for a new spot this often (seconds)
@export var roam_retarget := 0.7
## sprints for this long after his team wins the ball
@export var sprint_after_win := 3.0

static func defaults() -> Array[AiTrait]:
	var out: Array[AiTrait] = []
	out.append(AiTrait.new())
	return out
