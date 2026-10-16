class_name BallPhysics
extends RefCounted
## Ball flight, bounce and roll (pure simulation). Mirror of balls/balllib.py: keep the two in step; tune the numbers in the manager tool's Ball studio tab (data/balls.csv).
## World: x along the pitch, y up, z across. Metres and seconds. spin = angular velocity (rad/s): +z = backspin when moving along +x, +y = side spin.

const SPIN_LO := 15.0           # below this spin rate a fast ball can knuckle
const KNU_W2 := 48.0            # knuckle (metres of wobble) -> sideways acceleration: a = x * (2 pi f)^2 at about 1-2 Hz

var pos := Vector3.ZERO
var vel := Vector3.ZERO
var spin := Vector3.ZERO
var t := 0.0
var seed_value := 1.0           # a different seed = a different wobble
var g := 9.81
var rad := 0.17
var drag := 0.012
var mag := 0.0058
var knu := 0.0
var knu_v := 18.0
var crisis := 0.0
var crisis_v := 14.0
var e := 0.75
var mu := 0.6
var roll := 0.25
var sdec := 0.15
var spin_drag := 0.0           # side spin costs speed (a curler slows as it bends); data/balls.csv spin_drag
var power := 1.0
var touch := 1.0
var mass := 0.43

static func _f(row: Dictionary, key: String, d: float) -> float:
	var v = row.get(key, "")
	return float(v) if str(v) != "" else d

func setup(row: Dictionary) -> void:
	g = _f(row, "gravity", 9.81); rad = _f(row, "radius", 0.17); drag = _f(row, "air_drag", 0.012); mag = _f(row, "magnus", 0.0058); knu = _f(row, "knuckle", 0.0)
	knu_v = _f(row, "knuckle_speed", 18.0); crisis = _f(row, "crisis", 0.0); crisis_v = _f(row, "crisis_speed", 14.0); e = _f(row, "restitution", 0.75)
	mu = _f(row, "friction", 0.6); roll = _f(row, "roll_drag", 0.25); sdec = _f(row, "spin_decay", 0.15); spin_drag = _f(row, "spin_drag", 0.0); power = _f(row, "power", 1.0); touch = _f(row, "touch", 1.0); mass = _f(row, "mass", 0.43)
	pos = Vector3(0, rad, 0)

static func _phase(sd: float, k: float) -> float:
	return fposmod(sin(sd * 12.9898 + k * 78.233) * 43758.5453, 1.0) * TAU

func accel() -> Vector3:
	var sp := vel.length()
	var a := Vector3(0, -g, 0)
	var k := drag
	if crisis > 0.0: k = drag * (1.0 + crisis * smoothstep(crisis_v + 2.5, crisis_v - 2.5, sp))    # drag jumps up below the critical speed
	k *= 1.0 + spin_drag * minf(1.0, absf(spin.y) / 40.0)                                             # side spin costs speed: a curler slows as it bends
	a -= vel * (k * sp)
	a += spin.cross(vel) * mag                                                                          # Magnus: spin curves the ball
	if knu > 0.0 and sp > 1.0:                                                                          # knuckle: a fast, nearly spin-free ball wobbles sideways
		var amp := knu * smoothstep(knu_v * 0.6, knu_v, sp) * (1.0 - smoothstep(SPIN_LO * 0.5, SPIN_LO, spin.length()))
		if amp > 0.0:
			var u := vel.cross(Vector3.UP)
			if u.length() > 0.000001:
				u = u.normalized()
				var w := u.cross(vel).normalized()
				var n1 := (sin(TAU * 1.1 * t + _phase(seed_value, 1.0)) + 0.6 * sin(TAU * 2.3 * t + _phase(seed_value, 2.0))) / 1.6
				var n2 := (sin(TAU * 0.9 * t + _phase(seed_value, 3.0)) + 0.6 * sin(TAU * 2.0 * t + _phase(seed_value, 4.0))) / 1.6
				a += (u * n1 + w * (0.6 * n2)) * (amp * KNU_W2)
	return a

func _contact(normal_impulse: float) -> void:
	var rv := Vector3(0, -rad, 0)
	var vc := vel + spin.cross(rv)
	vc.y = 0.0
	var m := vc.length()
	if m > 0.000001:
		var j := minf(mu * normal_impulse, m / 2.5)
		var dv := -vc / m * j                                    # hollow ball: tangential slip dies at 1/(1+1/1.5)
		vel += dv
		spin += rv.cross(dv) * 1.5 / (rad * rad)

## advance by dt (use <= 1/60). Returns the speed it hit the ground with (0 = no bounce this step).
func step(dt: float) -> float:
	vel += accel() * dt
	pos += vel * dt
	spin *= exp(-sdec * dt)
	t += dt
	var bounced := 0.0
	if pos.y <= rad:
		pos.y = rad
		if vel.y < -0.8:
			var vin := -vel.y
			vel.y = vin * e
			_contact(vin * (1.0 + e))
			bounced = vin
		else:
			vel.y = 0.0
			_contact(g * dt)
			var k := exp(-roll * dt)
			vel.x *= k; vel.z *= k
	return bounced

## start a shot: dir = direction (any length), speed in m/s before the ball's own power factor
func launch(from: Vector3, dir: Vector3, speed: float, new_spin := Vector3.ZERO, seed_v := 1.0) -> void:
	pos = from; vel = dir.normalized() * speed * power; spin = new_spin; seed_value = seed_v; t = 0.0
