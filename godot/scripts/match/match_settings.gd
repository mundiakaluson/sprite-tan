@tool
class_name MatchSettings
extends Resource
## (MatchSettings.current is the set the running match uses, so footballers can read it.)
## Every tweakable number of the match in one place. Select `scenes/match/match_settings.tres` (assigned to the Match node's Settings) and edit it in the inspector;
## save it as another .tres to keep presets (arcade, simulation, ...). Distances are metres, speeds metres per second, times seconds.

static var current: MatchSettings
## the built-in formation names, used for the drop-down before the first export (data/formations.csv has the real list)
const FALLBACK_FORMATIONS := ["4-4-2", "4-3-3", "4-2-3-1", "4-1-4-1", "4-3-2-1", "4-1-2-1-2", "3-5-2", "3-4-3", "5-3-2", "5-4-1"]

@export_group("Match")
@export var stadium_id := "ST01"
@export var ball_id := "B01"
## formation by name (pick from the list; names come from data/formations.csv)
@export var home_formation := "4-4-2"
@export var away_formation := "4-3-3"
## formations you make here (add an element, New FormationLayout: name, family, ten slots). They appear in the two lists above
@export var custom_formations: Array[FormationLayout] = []:
	set(v):
		custom_formations = v
		notify_property_list_changed()
## the colours each team plays in (KitColors: open it, change the colours or use Load Preset to copy a kit from data/kits.csv)
@export var home_kit: KitColors
@export var away_kit: KitColors
## the goalkeepers' colours
@export var keeper_kit: KitColors
## real minutes the 90 game minutes take
@export_range(1.0, 20.0) var match_minutes := 4.0

@export_group("Scoreboard")
## ranked matches get the gold score bug with the stakes line, unranked the steel one
@export var ranked := false
@export var home_name := "HOME"
@export var away_name := "AWAY"
@export var division := "DIV 3"
@export var win_points := 24
@export var loss_points := 18

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

@export_group("Ball and first touch")
## how big the ball is drawn (1 = the old size)
@export_range(0.3, 1.5) var ball_scale := 0.7
## when a player gets the ball it eases to his feet over this long instead of snapping (seconds), at this speed (higher = quicker)
@export var settle_time := 0.3
@export var settle_rate := 9.0
## the first touch kills this fraction of his speed (a trap), and he is slowed for a moment
@export_range(0.0, 1.0) var control_cushion := 0.35

@export_group("Kick turn and stumble")
## he turns to face the target first when it is more than this many degrees away from where he faces, at this speed (degrees per second); the kick starts when he is within `pivot_done_deg`, or after `pivot_max` s
@export var pivot_min_deg := 30.0
@export var pivot_deg_per_s := 520.0
@export var pivot_done_deg := 14.0
@export var pivot_max := 0.6
## an opponent closer than this (m) is pressing him (full pressure at his shoulder)
@export var pressure_radius := 3.0
## chance a pass is scuffed = base + (60 - PAS) * per_pas + pressure * pressure_k + (kicked before turning) * misaligned_k; a scuffed pass gets this much aim error (metres)
@export var scuff_base := 0.05
@export var scuff_per_pas := 0.004
@export var scuff_pressure := 0.3
@export var scuff_misaligned := 0.25
@export var scuff_noise := 8.0
## after a scuffed pass he falls (when pressed) with this chance, else stumbles; a clean pass under pressure still makes him stumble a bit with this chance
@export_range(0.0, 1.0) var fall_chance := 0.4
@export_range(0.0, 1.0) var stumble_pressed := 0.25
## he staggers on at this speed (m/s) in the way he faces
@export var stumble_drift := 1.5
@export var clips_stumble_light := PackedStringArray(["base_stumble_fwd_s", "base_stumble_side_s", "base_stumble_back_s"])
@export var clips_stumble_medium := PackedStringArray(["base_stumble_fwd_m", "base_stumble_side_m", "base_stumble_back_m"])
@export var clips_fall := PackedStringArray(["base_fall"])

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
## per-role tuning for each side (scenes/ai/profile_default.tres); empty = role defaults. Give the two teams different profiles to try styles against each other
@export var home_ai: AiProfile
@export var away_ai: AiProfile
## a team defending in the opponent half presses (phase PRESS) when the formation's press number is above this
@export_range(0.0, 1.0) var press_line := 0.5
@export_range(0.0, 1.0) var ai_level := 0.6
## seconds between the carrier's decisions
@export var think_interval := 0.3

@export_group("Orders")
## how slow time runs while you line up a shot (1 = no slow motion)
@export_range(0.05, 1.0) var aim_slowmo := 0.3
## seconds of cooldown per cooldown number in cards.csv
@export var cooldown_scale := 1.5
## seconds the current-command box keeps showing an order after it is given
@export var command_hold := 2.0

@export_group("Order timing")
## seconds a Run / Press / Tackle order lasts before the player goes back to his own play
@export var run_order_time := 9.0
@export var press_order_time := 5.0
@export var tackle_order_time := 3.0
## a runner this close to his target has arrived (metres)
@export var arrive_distance := 1.2
## through ball: chance it curls (K02), and the runner is sent to where he will be this many seconds ahead at this speed
@export_range(0.0, 1.0) var through_curve_chance := 0.12
@export var through_lead := 1.5
@export var through_run_speed := 7.0

@export_group("Card effects")
## success roll: the card's stat difference to 60 counts this much per point (percent)
@export var stat_roll_k := 0.3
## shot cards: ball speed = base + card ball_speed x per_point (x miss_speed when the roll fails); aim noise in degrees-ish: good, bad base, + card risk x risk_k
@export var shot_base_speed := 14.0
@export var shot_speed_per_point := 2.6
@export_range(0.1, 1.0) var shot_miss_speed := 0.75
@export var shot_good_noise := 1.5
@export var shot_bad_noise := 8.0
@export var shot_risk_noise := 0.6
## pass cards: speed = distance x per_m + base, clamped (before the card's ball_speed bonus)
@export var pass_speed_base := 6.0
@export var pass_speed_per_m := 0.85
@export var pass_speed_min := 9.0
@export var pass_speed_max := 26.0
## dribble cards: seconds nobody can tackle him, and the burst speed
@export var dribble_shield := 1.3
@export var dribble_burst := 7.0
## tackle cards: dash speed, and reach = base + card reach x per_point
@export var tackle_dash := 6.5
@export var tackle_card_reach := 3.0
@export var tackle_reach_per_point := 0.25

@export_group("Goalkeeper saves")
## the keeper dives for a shot faster than this (m/s) that is heading for the goal and within his reach
@export var save_threat_speed := 9.0
## ... and that arrives within this many seconds
@export var save_max_time := 1.3
## he starts the dive when the ball is this many seconds later than the clip's strike frame
@export var save_reaction := 0.1
## how far sideways he can dive (metres), how high he can jump to add to his reach height, how far past his normal reach a dive stretches
@export var dive_range := 4.6
@export var jump_height := 0.8
@export var dive_extra := 0.9
## the dive also goes a bit forward (metres)
@export var dive_forward := 0.5
## how much of the sideways distance a stand-and-catch / claim / palm covers (0 = he stays put)
@export_range(0.0, 1.0) var stand_travel := 0.6
## ball height (m) above which it is a high ball (claimed if slow, palmed if fast) and below which it is low
@export var high_ball := 1.9
@export var low_ball := 0.6
@export var claim_speed := 13.0
@export var catch_speed := 14.0
## a central ball closer than this to him is caught standing
@export var stand_range := 1.2
## a ball further than this to the side is a far stretch (fingertips)
@export var far_range := 3.2
## clean catches (catch, claim) can hold a shot this much faster than a dive
@export var catch_bonus := 4.0
## deflections: sideways speed round the post, height of a palm over the bar, height of a fingertip save
@export var deflect_wide := 6.0
@export var palm_lift := 5.0
@export var deflect_lift := 2.5
@export_subgroup("Save clips (he picks one at random)")
@export var clips_catch := PackedStringArray(["gk08_big_hands", "gk03_smother"])
@export var clips_claim := PackedStringArray(["gk05_claim_cross"])
@export var clips_palm := PackedStringArray(["gk10_high_palm", "gk04_punch_clear"])
@export var clips_low := PackedStringArray(["gk09_low_dive", "gk20_cat_reflexes"])
@export var clips_mid := PackedStringArray(["gk02_reach_dive", "gk12_starfish"])
@export var clips_far := PackedStringArray(["gk24_fingertip_save", "gk23_far_post_reach"])

@export_group("Goalkeeper and control")
## a keeper catches a shot slower than base + HAN x per_han (m/s), otherwise he parries
@export var save_speed_base := 14.0
@export var save_speed_per_han := 0.25
## keeper reach grows by REF x this
@export var keeper_ref_reach := 0.012
## ball heights a player / keeper can reach (metres)
@export var reach_height := 1.3
@export var keeper_reach_height := 2.5
## the intended receiver of a pass gets this much more reach and control
@export var receiver_reach_k := 1.25
@export var receiver_control_k := 1.3
## a ball too fast to control keeps this much of its speed after bouncing off the player
@export_range(0.0, 1.0) var bounce_off := 0.45

## drop-down lists in the inspector, read from the exported tables
func _validate_property(property: Dictionary) -> void:
	var table := ""
	var col := "id"
	match property.name:
		"home_formation", "away_formation":
			table = "formations"
			col = "name"
		_: return
	var names: Array = []
	for r in Data.table(table): names.append(str(r.get(col, "")))
	if names.is_empty(): names = FALLBACK_FORMATIONS.duplicate()   # no export yet: the built-in names
	for l in custom_formations:
		if l != null: names.append(l.layout_name)
	property.hint = PROPERTY_HINT_ENUM
	property.hint_string = ",".join(names)

## formation id (F01) for a name ("4-4-2") or an id
static func formation_id(name_or_id: String) -> String:
	var l := layout(name_or_id)
	if l != null: return l.id
	for r in Data.table("formations"):
		if r["name"] == name_or_id or r["id"] == name_or_id: return r["id"]
	return "F01"


## a custom formation (made in Custom Formations) by name or id, or null
static func layout(name_or_id: String) -> FormationLayout:
	if current == null: return null
	for l in current.custom_formations:
		if l != null and (l.layout_name == name_or_id or l.id == name_or_id): return l
	return null
