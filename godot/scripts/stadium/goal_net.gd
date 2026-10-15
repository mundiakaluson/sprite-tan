class_name GoalNet
extends RefCounted
## Spring-mesh goal net (pure simulation, no nodes). Mirror of stadiums/goallib.py: keep the two in step; the Python Goal simulator tab is where the numbers are tuned.
## Local goal space (metres): origin = middle of the goal line on the ground, +x outward (behind the goal), y up, z across the mouth.
## Four panels (back, roof, two sides) of linked points. The front edge (on the posts and bar) and the ground edge are pinned; the rest swings.

const SUB := 3
const SWAY_SCALE := 0.02            # a post top moves this many metres per unit of wobble offset (the bar bounces half of that)

class Wobble:
	var k := 50.0
	var c := 3.5
	var x := 0.0
	var v := 0.0
	func step(dt: float) -> void:
		v += (-k * x - c * v) * dt
		x += v * dt
	func hit(impulse: float) -> void:
		v += impulse
	func energy() -> float:
		return absf(x) + absf(v) * 0.05

var hw := 3.66
var h := 2.44
var dep := 2.0
var dep_low := 2.0
var mesh := 0.35
var stiff := 0.5
var damp := 0.02
var grav := 6.0
var drag := 6.0
var pr := 0.06
var bounce := 0.55
const NET_A := 1100.0         # how hard the net wall pushes the ball back (m/s^2 per metre of penetration, times style stiffness; see apply())
const NET_C := 22.0           # the net soaks up the ball's speed while it is touching (1/s)
const BALL_R := 0.17          # game ball radius (a real ball is 0.11 m; a bit bigger reads better on screen)
var p := PackedVector3Array()
var prev := PackedVector3Array()
var home := PackedVector3Array()
var pinned := PackedByteArray()
var edges := PackedInt32Array()     # pairs of point indices
var rest := PackedFloat32Array()
var left := Wobble.new()
var right := Wobble.new()
var bar := Wobble.new()
var touching := false
var energy := 0.0

static func _f(g: Dictionary, key: String, d: float) -> float:
	var v = g.get(key, "")
	return float(v) if str(v) != "" else d

var wall_a := 600.0
var wall_c := 22.0
var alpha := 200.0
var droop := 0.0
var wear_override := -1.0

func setup(g: Dictionary, wear := -1.0) -> void:
	wear_override = wear
	hw = _f(g, "width", 7.32) / 2.0; h = _f(g, "height", 2.44); dep = _f(g, "depth", 2.0); dep_low = _f(g, "depth_low", dep); mesh = maxf(0.1, _f(g, "mesh", 0.35)); pr = _f(g, "post_radius", 0.06)
	apply(g)
	_build()

## new physics numbers without rebuilding the mesh
func apply(g: Dictionary) -> void:
	var w := (_f(g, "wear", 0.0) if wear_override < 0.0 else wear_override) / 100.0       # 0 new .. 1 worn out
	var st := _f(g, "stretch", 0.2)                                                       # 0 hard .. 1 soft
	stiff = _f(g, "stiffness", 0.5) * (1.0 - 0.45 * w) * (1.0 - 0.5 * st); grav = _f(g, "gravity", 6.0) * (1.0 + 1.5 * w); damp = _f(g, "damping", 0.02) * (1.0 - 0.4 * w)
	wall_a = NET_A * _f(g, "stiffness", 0.5) * (1.0 - 0.5 * w) / (1.0 + 10.0 * st); wall_c = NET_C * (1.0 - 0.6 * st); alpha = _f(g, "net_alpha", 200.0) * (1.0 - 0.35 * w); droop = 0.2 * w
	drag = _f(g, "drag", 6.0); bounce = _f(g, "bounce", 0.55)
	var k := _f(g, "post_sway", 50.0); var c := _f(g, "post_damp", 3.5)
	left.k = k; left.c = c; right.k = k; right.c = c; bar.k = k * 1.3; bar.c = c

func _build() -> void:
	var index := {}                   # Vector3i (millimetres) -> point number
	var pts: Array[Vector3] = []
	var edge_set := {}
	var panels := [
		[Vector3(dep, h, -hw), Vector3(dep, h, hw), Vector3(dep_low, 0, hw), Vector3(dep_low, 0, -hw)],      # back
		[Vector3(0, h, -hw), Vector3(0, h, hw), Vector3(dep, h, hw), Vector3(dep, h, -hw)],                  # roof
		[Vector3(0, 0, -hw), Vector3(0, h, -hw), Vector3(dep, h, -hw), Vector3(dep_low, 0, -hw)],            # side z = -hw
		[Vector3(0, 0, hw), Vector3(0, h, hw), Vector3(dep, h, hw), Vector3(dep_low, 0, hw)]]                # side z = +hw
	for pn in panels:
		var c00: Vector3 = pn[0]; var c10: Vector3 = pn[1]; var c11: Vector3 = pn[2]; var c01: Vector3 = pn[3]
		var nu := maxi(1, int(round((c10 - c00).length() / mesh))); var nv := maxi(1, int(round((c01 - c00).length() / mesh)))
		var idx := {}
		for i in range(nu + 1):
			for j in range(nv + 1):
				var u := float(i) / nu; var v := float(j) / nv
				var q := (c00 * (1 - u) + c10 * u) * (1 - v) + (c01 * (1 - u) + c11 * u) * v
				var key := Vector3i(roundi(q.x * 1000), roundi(q.y * 1000), roundi(q.z * 1000))
				if not index.has(key):
					index[key] = pts.size(); pts.append(q)
				idx[Vector2i(i, j)] = index[key]
		for i in range(nu + 1):
			for j in range(nv + 1):
				if i < nu: _edge(edge_set, idx[Vector2i(i, j)], idx[Vector2i(i + 1, j)])
				if j < nv: _edge(edge_set, idx[Vector2i(i, j)], idx[Vector2i(i, j + 1)])
	p = PackedVector3Array(pts)
	pinned.resize(p.size())
	for i in p.size(): pinned[i] = 1 if (p[i].x < 0.001 or p[i].y < 0.001 or (absf(p[i].y - h) < 0.001 and absf(p[i].x - dep) < 0.001)) else 0   # front frame, ground, rear top bar
	if droop > 0.0:                                                                         # a worn net hangs lower in the middle
		for i in p.size():
			if pinned[i] == 0:
				var q := p[i]; q.y -= droop * (1.0 - pow(q.z / hw, 2.0)) * clampf(q.y / h, 0.0, 1.0); p[i] = q
	prev = p.duplicate(); home = p.duplicate()
	edges.clear(); rest.clear()
	for k in edge_set.keys():
		var a: int = k >> 20; var b: int = k & 0xFFFFF
		edges.append(a); edges.append(b); rest.append(p[a].distance_to(p[b]))

func _edge(set: Dictionary, a: int, b: int) -> void:
	set[(mini(a, b) << 20) | maxi(a, b)] = true

func reset() -> void:
	p = home.duplicate(); prev = home.duplicate()
	left.x = 0; left.v = 0; right.x = 0; right.v = 0; bar.x = 0; bar.v = 0

## advance by dt. The ball (local position / velocity / radius) is optional. Returns {"vel": Vector3, "hits": [["net"|"left"|"right"|"bar", point], ...]}
func step(dt: float, has_ball := false, bp := Vector3.ZERO, bv := Vector3.ZERO, br := BALL_R) -> Dictionary:
	var hits := []
	var newv := bv
	var n := p.size()
	var reach := br + mesh * 0.4
	for i in n:
		if pinned[i] == 1: continue
		var q := p[i]
		var vel := (q - prev[i]) * (1.0 - damp)
		prev[i] = q
		q += vel
		q.y -= grav * dt * dt * 0.5
		p[i] = q
	touching = false
	if has_ball:
		var count := 0
		for i in n:
			if pinned[i] == 1: continue
			var d := p[i] - bp; var dist := d.length()
			if dist < reach:
				var nrm := d / maxf(dist, 0.000001)
				p[i] = bp + nrm * reach; prev[i] = p[i] - bv * dt * 0.6; count += 1
		if count > 0:
			touching = true
			newv = newv * exp(-drag * dt * minf(10.0, count) / 3.0)
			hits.append(["net", bp])
		# inside the goal the net is a soft wall (back, roof, sides): the ball cannot pass through it, the mesh bulges to show it
		if bp.x > 0.0 and absf(bp.z) < hw + br and bp.y < h:
			var aa := wall_a
			var damp_k := 1.0 - minf(0.9, wall_c * dt)
			var dd := bp.x + br - (dep_low + (dep - dep_low) * clampf(bp.y / h, 0.0, 1.0))
			if dd > 0.0:
				newv.x -= aa * dd * dt; newv *= damp_k; hits.append(["net", bp])
			dd = absf(bp.z) + br - hw
			var sg := 1.0 if bp.z > 0.0 else -1.0
			if dd > 0.0:
				newv.z -= sg * aa * dd * dt; newv *= damp_k; hits.append(["net", bp])
			dd = bp.y + br - h
			if dd > 0.0:
				newv.y -= aa * dd * dt; newv *= damp_k; hits.append(["net", bp])
		var parts := [["left", Vector3(0, 0, -hw), Vector3(0, h, -hw), left], ["right", Vector3(0, 0, hw), Vector3(0, h, hw), right], ["bar", Vector3(0, h, -hw), Vector3(0, h, hw), bar]]
		for part in parts:
			var a: Vector3 = part[1]; var b: Vector3 = part[2]; var ab := b - a
			var t := clampf((bp - a).dot(ab) / ab.dot(ab), 0.0, 1.0)
			var cp := a + ab * t; var dv := bp - cp; var dd := dv.length()
			if dd < br + pr and dd > 0.000001:
				var nn := dv / dd; var vn := newv.dot(nn)
				if vn < 0.0:
					newv = newv - (1.0 + bounce) * vn * nn
					(part[3] as Wobble).hit(-vn * 0.8)
					hits.append([part[0], bp])
	for _s in SUB:
		for e in rest.size():
			var a := edges[e * 2]; var b := edges[e * 2 + 1]
			var d := p[b] - p[a]
			var l := maxf(d.length(), 0.000000001)
			var corr := d * ((l - rest[e]) / l) * stiff
			var wa := 1.0 - pinned[a]; var wb := 1.0 - pinned[b]
			var tot := wa + wb
			if tot < 0.5: continue
			p[a] += corr * (wa / tot); p[b] -= corr * (wb / tot)
	left.step(dt); right.step(dt); bar.step(dt)
	var en := left.energy() + right.energy() + bar.energy()
	for i in n: en += (p[i] - prev[i]).length()
	energy = en
	return {"vel": newv, "hits": hits}
