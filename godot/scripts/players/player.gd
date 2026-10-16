@tool
class_name Player
extends Node2D
## One player on the pitch. Instance scenes/players/player.tscn (Player.create() does it), then setup(row).
## Scene: Sprite (the recoloured picture), AnimationPlayer (one Animation per sprite sheet), AnimationTree (the flow graph with arrows
## between clips), StateMachine (gameplay states as child nodes). States ask for a clip with play_clip(); the tree plays it and follows
## the arrows (data/animation_flow.csv) by itself.
##   var p := Player.create(); add_child(p); p.setup(Data.row("players", "PL242")); p.move_to(Vector2(300, 200)); p.play_action("kick")

signal state_changed(from_state: StringName, to_state: StringName)
signal clip_event(event_name: String)       # "strike", "land", ... from the animation

const SCENE := "res://scenes/players/player.tscn"
const BASE_SPEED := 30.0        # pixels per second at PAC 0 (placeholder numbers, tune with the match view)
const SPEED_PER_PAC := 0.6

@onready var sprite: PlayerSprite = $Sprite
@onready var anim_player: AnimationPlayer = $AnimationPlayer
@onready var anim_tree: AnimationTree = $AnimationTree
@onready var sm: PlayerStateMachine = $StateMachine

var row := {}
var velocity := Vector2.ZERO
var move_target := Vector2.ZERO
## 0..31, 8 = screen right, 16 = toward the camera. Drag it with the Player root selected to rotate the preview.
@export_range(0, 31) var facing := 16:
	set(v):
		facing = posmod(v, 32)
		if is_node_ready() and sprite != null: _apply_face()
## which player's look the preview shows (forwarded to the Sprite)
@export var preview_player := "PL242":
	set(v):
		preview_player = v
		if is_node_ready() and sprite != null and Engine.is_editor_hint(): sprite.player_id = v
## where the player stands when this scene is placed inside a Stadium's Actors node (pitch coords, x 0-100 across, y 0-100 own goal to opponent goal)
@export var pitch_position := Vector2(50, 50)
var _playback: AnimationNodeStateMachinePlayback
var _chain := {}                # clip -> next clip, for arrows marked auto in animation_flow.csv

static func create() -> Player:
	return (load(SCENE) as PackedScene).instantiate() as Player

func setup(r: Dictionary, kit: KitColors = null) -> void:
	row = r
	sprite.kit = kit
	sprite.setup(str(r.get("id", "")))
	if not sprite.clip_event.is_connected(_on_clip_event): sprite.clip_event.connect(_on_clip_event)
	_chain.clear()
	for f in Data.table("animation_flow"):
		if f.get("mode", "auto") == "auto": _chain[f["from"]] = f["to"]
	anim_tree.active = true
	_playback = anim_tree.get("parameters/playback")
	if not anim_tree.animation_finished.is_connected(_on_anim_finished): anim_tree.animation_finished.connect(_on_anim_finished)
	if not sm.transitioned.is_connected(_on_transitioned): sm.transitioned.connect(_on_transitioned)
	sm.start()

## the picture is mirrored (flipped, direction index 32 - d): a left dive made from the clip authored for the right (docs/DECISIONS.md, keeper clips)
var mirror := false

func set_mirror(m: bool) -> void:
	if m == mirror: return
	mirror = m
	if sprite != null:
		sprite.flip_h = m
		_apply_face()

func _apply_face() -> void:
	sprite.face(posmod(32 - facing, 32) if mirror else facing)

func _ready() -> void:
	if Engine.is_editor_hint(): sprite.face(facing)

# ---- orders (the AI and the player's cards call these)
func send_event(ev: StringName, data := {}) -> void:
	sm.send_event(ev, data)

func move_to(pos: Vector2) -> void:
	sm.send_event(&"move_to", {"target": pos})

func play_action(clip: String, face_toward := Vector2.ZERO, next := &"") -> void:
	var d := {"clip": clip}
	if next != &"": d["next"] = next
	if face_toward != Vector2.ZERO: d["face"] = face_toward
	sm.send_event(&"play_action", d)

# ---- helpers for states
func move_speed() -> float:
	var pac := Data.inum(row.get("PAC"), 50)
	return BASE_SPEED + pac * SPEED_PER_PAC

## the sprites were rendered by a camera looking down at ELEVATION degrees, which squashes the ground depth by sin(ELEVATION) (sprites/gen_player_v2.py ELEV = 30). A body turned to a world heading
## only LOOKS that way on screen when the heading is un-squashed again, so a screen direction is stretched vertically by 1 / sin(ELEVATION) before picking the sprite direction.
## Without this a runner going down-right on screen faced much more to the right than he moved.
## 0.5 is the exact geometry (sin 30) but made the body look too much toward the camera in play; 1.0 is the old behaviour (screen angle). Tweak between.
static var sprite_squash := 0.72

func face_vector(v: Vector2) -> void:
	if v.length() < 0.001: return
	v.y /= sprite_squash
	var deg := rad_to_deg(atan2(v.x, -v.y))          # up = 0, right = 90, down = 180, left = 270
	facing = posmod(int(round(deg / 11.25)), 32)
	_apply_face()

func has_clip(clip: String) -> bool:
	return anim_player.has_animation(clip)

## starts a clip from its first frame. Clips with arrows in the flow graph carry on by themselves. Unknown clips are skipped with a warning.
func play_clip(clip: String) -> void:
	if not has_clip(clip):
		push_warning("Player: no animation '%s' (export first, or check the name in the Animation panel)" % clip)
		return
	_apply_face()
	_playback.start(clip)

func current_clip() -> String:
	return String(_playback.get_current_node()) if _playback != null else ""

func _on_anim_finished(clip: StringName) -> void:
	var c := String(clip)
	# a clip that arrows into another non-looping clip is mid-chain: the tree carries on, the state hears about the END of the chain
	if _chain.has(c):
		var nxt: Dictionary = Data.anims.get("animations", {}).get(_chain[c], {})
		if not bool(nxt.get("loop", false)): return
	sm.clip_finished(c)

func _on_clip_event(event_name: String) -> void:
	clip_event.emit(event_name)

func _on_transitioned(a: StringName, b: StringName) -> void:
	state_changed.emit(a, b)
