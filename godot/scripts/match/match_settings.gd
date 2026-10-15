class_name MatchSettings
extends Resource
## (MatchSettings.current is the set the running match uses, so footballers can read it.)
## Every tweakable number of the match in one place. Select `scenes/match/match_settings.tres` (assigned to the Match node's Settings) and edit it in the inspector;
## save it as another .tres to keep presets (arcade, simulation, ...). Distances are metres, speeds metres per second, times seconds.

static var current: MatchSettings

@export_group("Match")
@export var stadium_id := "ST01"
@export var ball_id := "B01"
@export var home_formation := "F01"
@export var away_formation := "F02"
## real minutes the 90 game minutes take
@export_range(1.0, 20.0) var match_minutes := 4.0

@export_group("Players")
## top speed = speed_base + PAC x speed_per_pac
@export var speed_base := 4.4
@export var speed_per_pac := 0.036
@export var keeper_speed := 5.0
## how fast a player gets up to speed / slows down (m/s squared): low = heavy, realistic running, high = arcade
@export var accel := 7.0
@export var brake := 12.0
## how fast he turns to face where he runs (higher = snappier)
@export var turn_rate := 9.0
## positioning jog as a fraction of top speed
@export_range(0.3, 1.0) var jog_factor := 0.7
@export_range(0.5, 1.5) var sprint_factor := 1.1
## the ball carrier runs at this fraction of top speed
@export_range(0.4, 1.0) var carry_factor := 0.8
## players push each other apart inside this distance
@export var separation := 0.9

@export_group("Possession")
## how close the ball must be to a player's feet to be picked up
@export var pickup_reach := 0.9
@export var keeper_reach := 1.6
## a loose ball faster than control_speed_base + DRI x control_per_dri (x the ball's touch) is not controlled but bounces off
@export var control_speed_base := 9.0
@export var control_per_dri := 0.09
## the carried ball sits this far ahead of the feet (more when running)
@export var touch_ahead := 0.5
@export var no_touch_after_kick := 0.35
@export var tackle_reach := 1.3
## tackle attempts per second when a defender is on the carrier (x DEF / DRI)
@export var tackle_rate := 0.7
## the carrier cannot win the ball back for this long after losing it
@export var lose_ball_pause := 0.9

@export_group("Build-up")
## the pitch is split into thirds this far either side of the halfway line
@export var third_line := 17.5
## the carrier holds the ball at least this long before an unforced pass (seconds)
@export var hold_min := 0.8
## ... and must release by this time
@export var hold_max := 2.4
## 1 = recycle short, safe passes in build-up; 0 = go forward at once
@export_range(0.0, 1.0) var patience := 0.7
## an opponent this close counts as pressure: pass now
@export var pressure_radius := 3.5
## carry the ball at most this far before passing
@export var max_carry := 14.0
@export var shoot_range := 23.0
@export_range(0.0, 1.0) var shoot_chance := 0.5
@export var pass_min := 5.0
@export var pass_max := 38.0
## the pass length the AI likes
@export var ideal_pass := 14.0

@export_group("Team shape")
## how far the lines move up the pitch in each phase of play (scaled by the formation's line height)
@export var push_build_up := 6.0
@export var push_progress := 14.0
@export var push_final := 24.0
@export var push_defend := -6.0
## how far the team slides sideways towards the ball (x the formation's compactness)
@export_range(0.0, 1.0) var shift_to_ball := 0.4
## defenders pick up an attacker within this distance
@export var marking_distance := 9.0
## the player closing the ball down does so from this distance (press = formation press value)
@export var press_distance := 20.0

@export_group("AI")
@export_range(0.0, 1.0) var ai_level := 0.6
## seconds between the carrier's decisions
@export var think_interval := 0.3

@export_group("Orders")
## how slow time runs while you line up a shot (1 = no slow motion)
@export_range(0.05, 1.0) var aim_slowmo := 0.3
## seconds of cooldown per cooldown number in cards.csv
@export var cooldown_scale := 1.5
