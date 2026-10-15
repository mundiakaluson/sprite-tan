class_name BallKick
extends BallState
## A kick state (Pass, Through, Lob, Shot). `action_id` picks the row in data/ball_actions.csv: which kick style, how fast, how far ahead of a moving
## receiver to aim (lead), which stat sets accuracy. plan() turns "kick it to there" into numbers; Ball.play_action() then kicks and enters this state.

@export var action_id := "pass"

func _row() -> Dictionary:
	return Data.row("ball_actions", action_id)

## from = where the ball is, target = where to (metres, x along / z across), stats = the kicker's player row, target_vel = how the receiver is moving (m/s)
func plan(from: Vector3, target: Vector2, stats: Dictionary, target_vel := Vector2.ZERO) -> Dictionary:
	var r := _row()
	if r.is_empty():
		push_warning("BallKick: no row '%s' in ball_actions.csv (run Export to game)" % action_id)
		return {"style": "K07", "speed": 15.0, "target": target, "noise": 0.0, "action": action_id}
	var aim_pt := target + target_vel * Data.num(r.get("lead"), 0.0)
	var dist := Vector2(from.x, from.z).distance_to(aim_pt)
	var stat := Data.inum(stats.get(str(r.get("stat", "PAS"))), 60)
	var speed := Data.num(r.get("base_speed"), 15.0) + Data.num(r.get("per_metre"), 0.0) * dist + Data.num(r.get("per_stat"), 0.0) * stat
	var k := Data.num(r.get("lob_range_k"), 0.0)
	if k > 0.0: speed = sqrt(dist * k)
	speed = clampf(speed, Data.num(r.get("min_speed"), 5.0), Data.num(r.get("max_speed"), 35.0))
	return {"style": str(r.get("style", "K07")), "speed": speed, "target": aim_pt,
		"noise": (100.0 - stat) * Data.num(r.get("noise_per_point"), 0.05), "action": action_id}
