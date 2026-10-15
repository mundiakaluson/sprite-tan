@tool
class_name CameraRig
extends Camera3D
## The match camera. It orbits a target point on the pitch: the target follows the ball (along the pitch, and panning across it), and the camera sits at `distance` from the target
## at the given yaw / pitch, so rotating around the players is just changing yaw_deg (inspector, or `orbit_to()` from code for cinematics).
## yaw 0 = the usual TV view from the near touchline; 90 = from the left end; 180 = from behind the far touchline.

@export_group("Orbit")
## degrees around the target: 0 = TV view from the near touchline
@export_range(-360.0, 360.0) var yaw_deg := 0.0
## degrees above the grass
@export_range(5.0, 89.0) var pitch_deg := 36.5
## metres from the target
@export var distance := 50.4
@export_range(10.0, 90.0) var fov_deg := 36.0
## where the camera aims, relative to the followed point (x along the pitch, y up, z across; z = 15.5 puts the ball towards the top of the screen)
@export var aim_offset := Vector3(0.0, 0.0, 15.5)

@export_group("Follow")
## how fast the camera follows the ball along the pitch
@export var follow_speed := 4.0
## the camera never goes further than this along the pitch
@export var limit_x := 38.0
## as the ball goes towards the far touchline the camera slides this many metres that way (the near line may drop out of view); 0 = no pan
@export var pan_far := 6.0
@export var pan_speed := 3.0

@export_group("Stadium")
## take height / back / aim / fov from the stadium (data/stadiums.csv, a TV view that cuts off the near touchline) instead of the numbers above
@export var use_stadium_layout := false

var _x := 0.0
var _pan := 0.0
var _tween: Tween

func follow(target: Vector3, half_width: float, dt: float) -> void:
	_x = lerpf(_x, clampf(target.x, -limit_x, limit_x), clampf(follow_speed * dt, 0.0, 1.0))
	_pan = lerpf(_pan, _pan_for(target, half_width), clampf(pan_speed * dt, 0.0, 1.0))
	_apply()

func snap(target: Vector3, half_width: float) -> void:
	_x = clampf(target.x, -limit_x, limit_x)
	_pan = _pan_for(target, half_width)
	_apply()

## ball on the near touchline -> 0 (bottom line in view), on the far touchline -> -pan_far
func _pan_for(target: Vector3, half_width: float) -> float:
	return -pan_far * clampf((half_width - target.z) / (2.0 * half_width), 0.0, 1.0)

func _apply() -> void:
	fov = fov_deg
	var aim := Vector3(_x, 0.0, _pan) + aim_offset
	var p := deg_to_rad(pitch_deg)
	var y := deg_to_rad(yaw_deg)
	var off := Vector3(sin(y) * cos(p), sin(p), cos(y) * cos(p)) * distance
	look_at_from_position(aim + off, aim, Vector3.UP)

## glide to a new angle / distance (a replay, a goal celebration ...). Leave a value at INF to keep it.
func orbit_to(yaw := INF, pitch := INF, dist := INF, seconds := 1.0) -> void:
	if _tween != null: _tween.kill()
	_tween = create_tween().set_parallel(true).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	if yaw != INF: _tween.tween_property(self, "yaw_deg", yaw, seconds)
	if pitch != INF: _tween.tween_property(self, "pitch_deg", pitch, seconds)
	if dist != INF: _tween.tween_property(self, "distance", dist, seconds)

## stadium layout camera (height above the grass, metres behind the near touchline, aim z, fov) -> orbit numbers
func apply_layout(cm: Dictionary, half_width: float) -> void:
	var dz: float = half_width + float(cm["back"]) - float(cm["look_z"])
	distance = Vector2(float(cm["height"]), dz).length()
	pitch_deg = rad_to_deg(atan2(float(cm["height"]), dz))
	fov_deg = float(cm["fov"])
	aim_offset = Vector3(0.0, 0.0, float(cm["look_z"]))
	yaw_deg = 0.0
