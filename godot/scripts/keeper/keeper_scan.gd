class_name KeeperScan
extends Node2D
## The keeper's eyes. Every `scan_every` s, for each keeper:
##  - BALL RAY: a ball moving towards his goal is traced forward (a copy of its physics, so bend and dip are included) to where it crosses his line;
##    how much of the real path he reads grows with REF (read_base / read_per_ref, MatchSettings > Keeper reading shots). Stored in k.ai["scan"]
##    = {z, h, t}: AiGk steps across towards it before the shot arrives, and his stance drops into the set position.
##  - PERIMETER RAYS: with an opponent on the ball in range, rays from the ball to both posts; the keeper stands on the bisector of that angle
##    (k.ai["bisect_z"]), which is where he covers the most goal.
##  - SET: k.ai["set"] = true when a shot is likely (an opponent with the ball within set_range facing goal, or the ball ray says it is coming): MatchMotion
##    plays the set / low stance, he stays on his toes and keeps his chest to the ball.
## Draws its rays when MatchSettings > Keeper scan > Debug Draw is on. Lives in the stadium's Actors layer (screen coordinates).

var g: MatchGame
var _t := 0.0

func setup(game: MatchGame) -> void:
	g = game
	z_index = 3995

func _physics_process(dt: float) -> void:
	if g == null or g.ball == null or g.phase != MatchGame.Phase.PLAY: return
	_t -= dt
	if _t > 0.0: return
	_t = g.settings.scan_every
	for k in g.all:
		if k.is_keeper(): _scan(k)
	if g.settings.scan_debug: queue_redraw()

func _scan(k: Footballer) -> void:
	var s := g.settings
	var goal := Vector2(-MatchGame.HALF_L * k.team.dir, 0.0)
	var b := g.ball
	var bp := Vector2(b.phys.pos.x, b.phys.pos.z)
	var carrier := g.carrier
	k.ai.erase("scan")
	# ball ray
	var v := b.phys.vel
	if carrier == null and v.length() > s.scan_min_speed and v.x * k.team.dir < 0.0:
		var p := b.copy_physics()
		var dt := 1.0 / 30.0
		var t := 0.0
		var line := k.pos.x
		while t < s.scan_horizon:
			var before := p.pos
			p.step(dt)
			t += dt
			if (p.pos.x - line) * k.team.dir <= 0.0:
				var straight_z := b.phys.pos.z + v.z * t
				var read := clampf(s.read_base + (k.stat("REF", 60) - 60) * s.read_per_ref, 0.0, 1.0)
				var z := lerpf(straight_z, p.pos.z, read)
				if absf(z) < MatchGame.GOAL_HALF + s.scan_post_margin:
					k.ai["scan"] = {"z": z, "h": p.pos.y, "t": t, "from": b.phys.pos, "hit": Vector3(line, p.pos.y, z)}
				break
	# perimeter rays: the angle the shooter sees, the keeper on its bisector
	k.ai.erase("bisect_z")
	k.ai["set"] = false
	var threat := carrier != null and carrier.team != k.team and carrier.pos.distance_to(goal) < s.set_range
	if threat:
		var near := Vector2(goal.x, -MatchGame.GOAL_HALF)
		var far := Vector2(goal.x, MatchGame.GOAL_HALF)
		var a := (near - bp).normalized()
		var c := (far - bp).normalized()
		var bis := (a + c).normalized()
		if absf(bis.x) > 0.01:
			var u := (k.pos.x - bp.x) / bis.x                                  # where the bisector meets his line
			k.ai["bisect_z"] = bp.y + bis.y * u
		var facing_goal := carrier.face.dot((goal - carrier.pos).normalized()) > s.set_facing
		k.ai["set"] = facing_goal
	if k.ai.has("scan"): k.ai["set"] = true

func _draw() -> void:
	if g == null or not g.settings.scan_debug: return
	var cam := g.stadium.camera
	for k in g.all:
		if not k.is_keeper(): continue
		var goal_x := -MatchGame.HALF_L * k.team.dir
		var bp := g.ball.phys.pos
		if k.ai.has("bisect_z") or k.ai.get("set", false):
			for pz in [-MatchGame.GOAL_HALF, MatchGame.GOAL_HALF]:
				draw_line(cam.unproject_position(Vector3(bp.x, 0.0, bp.z)), cam.unproject_position(Vector3(goal_x, 0.0, pz)), Color(1, 1, 0.3, 0.5), 1.0)
		if k.ai.has("bisect_z"):
			draw_circle(cam.unproject_position(Vector3(k.pos.x, 0.0, float(k.ai["bisect_z"]))), 3.0, Color(0.3, 1.0, 1.0, 0.9))
		if k.ai.has("scan"):
			var sc: Dictionary = k.ai["scan"]
			draw_line(cam.unproject_position(sc["from"]), cam.unproject_position(sc["hit"]), Color(1, 0.3, 0.3, 0.8), 1.5)
			draw_circle(cam.unproject_position(sc["hit"]), 3.0, Color(1, 0.2, 0.2, 1.0))
