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
## how fast he turns to face where he runs (degrees per second; 400 = a leisurely turn, 900 = snappy)
@export var turn_deg_per_s := 650.0
## positioning jog as a fraction of top speed
@export_range(0.3, 1.0) var jog_factor := 0.7
@export_range(0.5, 1.5) var sprint_factor := 1.06
## the ball carrier runs at this fraction of top speed
@export_range(0.4, 1.0) var carry_factor := 0.8
## below this speed (m/s) a player can face somewhere other than where he runs (a scan glance, an open body while a pass comes; AiScan sets f.ai.look)
@export var look_max_speed := 3.0
## players push each other apart inside this distance
@export var separation := 0.9

@export_group("Ball and first touch")
## how big the ball is drawn (1 = the old size)
@export_range(0.3, 1.5) var ball_scale := 0.85
## when a player gets the ball it eases to his feet over this long instead of snapping (seconds), at this speed (higher = quicker)
@export var settle_time := 0.4
## the ball reaches his foot as a critically damped spring (omega, higher = quicker; ~16 settles in 0.25 s); the incoming ball speed is kept up to settle_max_speed m/s
@export var settle_omega := 12.0
@export var settle_max_speed := 12.0
## a ball further than this (m) from the new carrier is placed at his feet instead of rolling there (restarts)
@export var settle_snap := 2.5
## the first touch kills this fraction of his speed (a trap), and he is slowed for a moment
@export_range(0.0, 1.0) var control_cushion := 0.35

@export_group("Stamina and sprint")
## a clip is a sprint (base_sprint) from this fraction of his own top speed, otherwise a jog; running that fast drains stamina (per second, less with PHY), jogging gives a little back, standing a lot
@export_range(0.5, 1.0) var sprint_clip_frac := 0.9
@export var sprint_drain := 0.16
@export var jog_regen := 0.008
@export var rest_regen := 0.04
## PHY 100 drains this much less (drain x (1.3 - PHY / 100 x phy_k)); below `tired_below` stamina his top speed falls to `tired_speed` of normal and he runs the tired run clip (under `tired_clip_below`)
@export var phy_k := 1.0
@export_range(0.05, 1.0) var tired_below := 0.3
@export_range(0.3, 1.0) var tired_speed := 0.75
@export var tired_clip_below := 0.25

@export_group("Kick turn and stumble")
## he turns to face the target first when it is more than this many degrees away from where he faces, at this speed (degrees per second); the kick starts when he is within `pivot_done_deg`, or after `pivot_max` s
@export var pivot_min_deg := 65.0
@export var pivot_deg_per_s := 600.0
@export var pivot_done_deg := 14.0
@export var pivot_max := 0.9
## the turn is heavy at speed: the rate is divided by (1 + speed x this), scaled by agility (DRI 40 -> x agility_min, DRI 90 -> x agility_max); he also slows at pivot_brake (m/s2) down to pivot_min_speed while turning, and his run bends round with him
@export var pivot_speed_drag := 0.1
@export var agility_min := 0.6
@export var agility_max := 1.3
@export var pivot_brake := 6.0
@export var pivot_min_speed := 1.5
## turn clips played during the pivot: sharp (DRI >= skilled_dri), normal, heavy (DRI < heavy_dri)
@export var clips_turn_skilled := PackedStringArray(["tn04_spin_turn", "tn03_sharp_turn"])
@export var clips_turn_normal := PackedStringArray(["tn02_plant_turn", "tn03_sharp_turn"])
@export var clips_turn_heavy := PackedStringArray(["tn01_heavy_turn", "tn02_plant_turn"])
@export var skilled_dri := 75
@export var heavy_dri := 55
## an opponent closer than this (m) is pressing him (full pressure at his shoulder)
@export var kick_pressure_radius := 3.0
## chance a pass is scuffed = base + (60 - PAS) * per_pas + pressure * pressure_k + (kicked before turning) * misaligned_k; a scuffed pass gets this much aim error (metres)
@export var scuff_base := 0.04
@export var scuff_per_pas := 0.002
@export var scuff_pressure := 0.15
@export var scuff_misaligned := 0.12
@export var scuff_noise := 4.5
## after a scuffed pass he falls (when pressed) with this chance, else stumbles; a clean pass under pressure still makes him stumble a bit with this chance
@export_range(0.0, 1.0) var fall_chance := 0.4
@export_range(0.0, 1.0) var stumble_pressed := 0.25
## he staggers on at this speed (m/s) in the way he faces
@export var stumble_drift := 1.5
@export var clips_stumble_light := PackedStringArray(["base_stumble_fwd_s", "base_stumble_side_s", "base_stumble_back_s"])
@export var clips_stumble_medium := PackedStringArray(["base_stumble_fwd_m", "base_stumble_side_m", "base_stumble_back_m"])
@export var clips_fall := PackedStringArray(["base_fall", "base_fall_trip", "base_fall_back"])
## the keeper stands in this clip when he is not moving (a ready stance instead of the outfield idle)
@export var clip_keeper_idle := "gk_ready_idle"
## a keeper picking a loose ball off the grass (lower than scoop_max_height m) plays this (run in, bend, scoop it into his hands; the clip's ball track holds it) over scoop_time s
@export var clip_keeper_scoop := "gk35_scoop_collect"
@export var scoop_max_height := 0.45
## how close (m) a keeper has to be to pick a ball up off the grass (balls in the air use keeper_reach + REF)
@export var keeper_ground_reach := 1.0
@export var scoop_time := 1.3
@export var clip_keeper_set := "gk_set_low"
@export var clip_keeper_shuffle := "gk_shuffle"
## the keeper reads the game: relaxed (outfield idle) when the ball is far or his team has it, alert (ready stance) when the opponents have it within keeper_alert_dist m of his goal line,
## set (low, wide) when an opponent has it within keeper_set_dist. Below keeper_watch_speed he keeps his chest to the ball (turning at keeper_turn_deg_per_s) and sidesteps when the move is mostly sideways (share > keeper_shuffle_lateral)
@export var keeper_alert_dist := 50.0
@export var keeper_set_dist := 26.0
@export var keeper_watch_speed := 4.2
@export var keeper_turn_deg_per_s := 360.0
@export_range(0.0, 1.0) var keeper_shuffle_lateral := 0.6

@export_group("Kick animations")
## the whole kick clip is played in this many seconds (the authored clips take ~1.5 s, far too slow for a pass); the ball goes at the clip's strike frame
@export var kick_clip_time := 0.7
@export var shot_clip_time := 0.75
## curled shots play slower so the wind-up and the bend of the body can be seen (whole clip, seconds)
@export var curl_clip_time := 0.95
## shot clips are scaled by the shooter's SHO: x shot_time_slow at SHO 40 or less, x shot_time_fast at SHO 90 or more (lower = quicker strike)
@export var shot_time_slow := 1.2
@export var shot_time_fast := 0.78
@export var clips_slow_kick := PackedStringArray(["sh03_finesse_curler", "sh04_trivela_bender", "sh17_far_post_bender", "sh21_lofted_finesse"])
## a player who kicks while running keeps moving: he slows at this rate (m/s2) during the clip instead of stopping dead
@export var glide_brake := 4.0
## shots on the run brake only this share of glide_brake: he strikes it in his stride and carries on running
@export_range(0.0, 1.0) var shot_glide_k := 0.3
## pass clips by situation (right-footed clips; one is picked at random from the list)
@export var clips_pass_short := PackedStringArray(["ps16_square_ball", "ps12_outside_foot_pass", "ps23_lay_off"])
@export var clips_pass_medium := PackedStringArray(["ps03_driven_pass", "ps12_outside_foot_pass", "ps16_square_ball"])
@export var clips_pass_long := PackedStringArray(["ps18_long_ball_forward", "air_pass_low", "ps10_switch_play"])
@export var clips_pass_back := PackedStringArray(["ps17_return_pass", "ps25_reverse_pass"])
@export var clips_pass_through := PackedStringArray(["ps01_through_ball", "ps15_killer_ball"])
@export_group("Pressured clearance")
## a lob/clearance with an opponent this close (0..1, see kick_pressure_radius) is a panicked hack
@export_range(0.0, 1.0) var panic_pressure := 0.55
## chance the clearance is the hack-and-fall version; otherwise he staggers on
@export_range(0.0, 1.0) var panic_fall_chance := 0.55
@export var clips_panic_clear := PackedStringArray(["cl01_panic_clear"])
@export var clip_panic_fall := "cl02_panic_clear_fall"
@export_group("Kick animations")
@export var clips_pass_lob := PackedStringArray(["ps13_chipped_pass", "ps02_lofted_through"])
@export var clips_shot_close := PackedStringArray(["sh01_side_foot_place", "sh14_toe_poke", "sh23_snap_shot", "sh24_one_touch_finish"])
@export var clips_shot_far := PackedStringArray(["sh02_instep_drive", "sh07_power_blast", "sh22_rocket_long_shot", "sh19_dipping_drive"])
## distances (m) between short / medium / long passes and close / far shots; a target more than back_deg behind him is a back pass
@export var pass_short_m := 11.0
@export var pass_long_m := 26.0
@export var shot_far_m := 22.0
@export var pass_back_deg := 110.0

@export_group("Engagements")
## engagements on (design doc 9a / 9b): some duels freeze for card picks; off = the sim plays every duel by itself as before
@export var engage_on := true
## the home side: off = Manual (you pick a card in every engagement your team is in, attacking and defending), on = Auto (the AI manager picks for you). The away side is always Auto.
@export var home_auto_engage := false
## the hands at kick-off: card ids from cards.csv (e.g. DF08 = Double Team), up to 8. Empty slots are filled at random
## (2 shot, 2 pass, 2 dribble, 2 defend, skipping categories already covered). Deck building replaces this later.
@export var home_hand := PackedStringArray(["DF08"])
@export var away_hand := PackedStringArray()
## real seconds to pick; no pick in time = the free default (nothing spent)
@export var engage_choose_time := 2.5
## real seconds an Auto side takes to pick, and the reveal before the outcome plays out
@export var engage_ai_think := 0.5
@export var engage_reveal_time := 0.8
## time scale while choosing (slow motion; the match clock is stopped)
@export_range(0.01, 1.0) var engage_slowmo := 0.08
## play seconds between two engagements at least; engagements per side (as the ball side) aimed at over the match, and how far ahead of that pace it may run
@export var engage_min_gap := 4.0
@export var engage_target := 20
@export var engage_pace_slack := 3.0
## the press trigger: the presser within this many metres of the carrier starts a duel (checked every engage_press_every s; the same presser tries again after engage_press_retry game seconds)
@export var engage_press_zone := 2.6
@export var engage_press_every := 0.2
@export var engage_press_retry := 90.0
## chance a duel becomes an engagement: carrier in his own end (depth 0) .. in their box (depth 1)
@export_range(0.0, 1.0) var engage_chance_deep := 0.35
@export_range(0.0, 1.0) var engage_chance_high := 1.0
## resolution: P = clamp(succ + engage_k x (A - D), engage_p_min, engage_p_max) in %, A / D the two players' stats weighted by each card's stats
@export var engage_k := 0.6
@export var engage_p_min := 5.0
@export var engage_p_max := 95.0
## the free default's success %
@export var engage_default_succ := 60.0
## a won defending card turns into a foul with risk % x this
@export_range(0.0, 1.0) var engage_risk_win_share := 0.15
## a defender whose card failed and whose risk fired is out this much longer
@export var engage_down_strand := 1.6
## a shield card that wins: seconds nobody can tackle him
@export var engage_shield_time := 1.2
## a defender this close (m) tackles standing when he wins; further away he slides
@export var engage_stand_reach := 2.2
## ball speed (m/s) when it is poked away / squirts loose between them
@export var engage_poke_speed := 5.0
@export var engage_loose_speed := 3.5
## a foul: seconds the carrier cannot be tackled while he gets up, seconds the defender is out
@export var engage_foul_shield := 2.0
@export var engage_foul_out := 1.2
## AI manager: chance it plays a card when it has one (else the free default), and how greedy it is (low = nearly always its best card, high = random)
@export_range(0.0, 1.0) var engage_ai_play := 0.75
@export var engage_ai_temp := 0.12
## a foul card is worth this much to the AI unless the carrier is past engage_ai_foul_depth (0..1 up the pitch): it fouls to stop a chance, not everywhere
@export var engage_ai_foul_k := 0.3
@export var engage_ai_foul_depth := 0.75

@export_group("Double team")
## Double Team (effect move=double): the nearest team mate of the defender within this many metres of the carrier (and further than double_min_range) zaps in
@export var double_range := 30.0
@export var double_min_range := 2.5
## the carrier nearer than this to our goal = deep: the helper lands goal side (cover); further = upfield: he lands right behind the carrier
@export var double_deep_dist := 32.0
## upfield: metres behind the carrier; deep: metres goal side of the carrier and to the side away from the first defender
@export var double_behind := 1.2
@export var double_cover_dist := 3.0
@export var double_cover_side := 1.2
## the path: kinks and their sideways jitter (m); the zap itself runs on scenes/engagement/zap_trail.tscn's "zap" animation, this is only for aiming the carrier's spot
@export var double_kinks := 5
@export var double_jitter := 1.0
@export var double_zap_time := 0.35
## afterimages left along the path
@export var double_ghosts := 4
## time scale while he zaps in (lighter than the pick freeze)
@export_range(0.05, 1.0) var double_slowmo := 0.5
## added to the challenge side's stat in the duel roll (two on one)
@export var double_stat_bonus := 10.0
## his speed when he lands, x his top speed
@export var double_arrive_speed := 0.4

@export_group("Take-on and slide tackles")
## a defender within takeon_box_dist m of his own goal bites this much less often (he stays on his feet in the box)
@export var takeon_box_dist := 20.0
@export_range(0.0, 1.0) var takeon_box_read := 0.18
## a take-on: he shows the shoulder one way for fake_time s (at fake_speed x top speed), then bursts the other way for burst_time s (burst_speed x top speed, turning at turn_rate)
@export var clips_takeon := PackedStringArray(["dr01_step_over", "dr05_body_feint", "dr14_chop_cut", "dr02_drag_back", "dr28_pull_push", "dr27_outside_hook"])
## skill moves, used instead with chance (DRI - 60) / 40 (at most skill_max): elastico, croqueta, roulette, stepover chain, cruyff turn, spin
@export var clips_takeon_skill := PackedStringArray(["dr08_elastico", "dr07_la_croqueta", "dr03_roulette", "dr15_stepover_chain", "dr09_cruyff_turn", "dr21_spin_away"])
@export_range(0.0, 1.0) var skill_max := 0.7
@export var takeon_fake_time := 0.3
@export var takeon_burst_time := 0.5
@export var takeon_fake_speed := 0.8
@export var takeon_burst_speed := 1.1
@export var takeon_turn_rate := 14.0
## the defender buys the fake with chance base + (carrier DRI - his DEF) x per_stat; then he lunges / slides the faked way (share bite_slide) or is wrong-footed (stumble), and is out of play for `recover` s;
## the carrier cannot be tackled for `shield` s after a bitten fake. A defender who read it gets a tackle (reach, win chance)
@export var takeon_bite_base := 0.5
@export var takeon_bite_per_stat := 0.008
@export_range(0.0, 1.0) var takeon_bite_slide := 0.5
@export var takeon_recover := 0.9
@export var takeon_shield := 0.6
@export var takeon_read_reach := 2.4
@export_range(0.0, 1.0) var takeon_read_win := 0.6
## the slide tackle: clips, how long it takes (s), how fast he slides (m/s), where he aims (the carrier's position this many s ahead), how far the ball can be at the strike frame (m),
## win chance = base + (DEF - DRI) x per_stat; a missed slide leaves him on the floor (Tackle tumbles)
@export var clips_slide := PackedStringArray(["df02_slide_tackle"])
@export var slide_clip_time := 0.75
@export var slide_speed := 8.0
@export var slide_lead := 0.3
@export var slide_reach := 1.9
@export var slide_win_base := 0.55
@export var slide_per_stat := 0.008

@export_group("Keeper one on one")
## the keeper rushing a breakaway: smother clip, how long it takes, how far the carrier can be at the strike frame, win chance = base + (keeper (REF + HAN) / 2 - carrier DRI) x per_stat
@export var clip_smother := "gk03_smother"
@export var smother_clip_time := 0.8
@export var smother_reach := 2.2
@export var smother_base := 0.5
@export var smother_per_stat := 0.008
## the Rush order (click the keeper): how long it lasts (s)
@export var keeper_rush_order_time := 4.0

@export_group("Tackle tumbles")
## a won tackle: the tackler slides in (clip below, played in tackle_clip_time s) and the ball changes hands at its strike frame; the victim then falls with this chance, else stumbles
@export var clips_tackle := PackedStringArray(["df01_stand_tackle", "df03_poke_tackle"])
@export var tackle_clip_time := 0.5
@export_range(0.0, 1.0) var tackle_victim_fall := 0.4
## a failed challenge (attempts per second while a defender is on the carrier): the tackler over-commits and stumbles / falls, the carrier is knocked a bit
@export var tackle_miss_rate := 0.8
@export_range(0.0, 1.0) var tackle_miss_fall := 0.3
@export_range(0.0, 1.0) var tackle_miss_carrier_stumble := 0.3

@export_group("Possession")
## how close the ball must be to a player's feet to be picked up
@export var pickup_reach := 0.9
@export var keeper_reach := 1.6
## a loose ball faster than control_speed_base + DRI x control_per_dri (x the ball's touch) is not controlled but bounces off
@export var control_speed_base := 9.0
@export var control_per_dri := 0.09
## the carried ball sits this far ahead of the feet (more when running)
@export var touch_ahead := 0.3
## the ball runs this much further ahead for each m/s he runs
@export var touch_speed := 0.035
## dribbling: the ball runs this much further ahead (m) once per `touch_stride` metres, then he catches up (scaled by speed, full at 6 m/s)
@export var touch_pulse := 0.4
@export var touch_stride := 2.3
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
## seconds after the ball is struck before the runner reacts and sets off
@export var through_react := 0.25

@export_group("Bent passes")
## a passer with game sense (PAS + DRI average >= pass_curl_sense_min) bends a pass / through ball of pass_curl_min_dist m or more round a defender who is
## within pass_curl_block m of the straight lane (opponents within pass_curl_skip m of the passer or the receiver do not count: pressure / a marker)
@export var pass_curl_on := true
@export var pass_curl_sense_min := 70.0
@export var pass_curl_min_dist := 12.0
@export var pass_curl_block := 1.8
@export var pass_curl_skip := 2.0
## the bent path must clear the defenders by this much more than the straight one; the kick styles for each way of bending (data/kick_styles.csv)
@export var pass_curl_gain := 0.8
@export var pass_curl_style_cw := "K14"
@export var pass_curl_style_ccw := "K15"
## aim search: up to this many degrees off the straight line, in steps; the bent flight must pass within pass_curl_miss m of the target; speed x pass_curl_speed_k
@export var pass_curl_max_deg := 35.0
@export var pass_curl_step_deg := 2.5
@export var pass_curl_miss := 1.2
@export var pass_curl_speed_k := 1.0
## the speeds tried (x the pass speed): a slower ball bends more
@export var pass_curl_speeds := PackedFloat32Array([0.55, 0.7, 0.85, 1.0])
## the bent path must keep at least this far (m) from every defender, or it is not played (they step across: a near miss is an interception)
@export var pass_curl_need := 1.8

@export_group("Through-ball runs")
## the human points the run: the pointer this many metres or more from the runner sets his direction (closer = straight up the pitch)
@export var through_point_min := 1.5
## once the drag is a through ball it stays on the runner while the pointer is within snap radius x this (room to point the run)
@export var through_point_reach := 4.0
## smart runs: game sense (PAS + DRI average) at least this curves the run round defenders on the straight line
@export var curve_sense_min := 68.0
## a defender within this many metres of the straight run blocks it; the bend (m) of the curve at its middle at curve_sense_min and at sense 99
@export var curve_block := 2.5
@export var curve_bend_min := 3.0
@export var curve_bend_max := 5.5
## the curve must clear defenders by this much more than the straight run to be worth it
@export var curve_gain := 0.8
## a curved run is this much faster (0.2 = +20%) and leaves faint afterimages every curve_ghost_every s (0 = none)
@export var curve_run_boost := 0.2
@export var curve_ghost_every := 0.14
## he leaves the curve and runs at the ball once he reaches the meeting point or the ball is this close (m); aims this many seconds ahead of the rolling ball
@export var curve_chase_dist := 5.0
@export var curve_chase_lead := 0.35

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
## the save happens the moment the ball is in his reach, from this many seconds before the clip's strike frame until this long after it (the ball is slower than his guess, so he waits for it)
@export var save_window_before := 0.15
@export var save_window_after := 0.6
## the ball counts as in reach when it is this close to him along the pitch (metres)
@export var save_depth := 1.8
## how far sideways he gets (m/s, plus per REF point) in the time his clip takes: a shot further from him than speed x time + save_reach beats him
@export var dive_speed := 2.0
@export var dive_speed_per_ref := 0.03
## how far from where he ends up the gloves reach (metres, plus keeper_ref_reach per REF point)
@export var save_reach := 0.75
## a ball in reach is still not always stopped: chance = (save_skill_base + average of his REF and HAN x save_skill_per_stat) x (1 - dive_difficulty x sideways distance / dive_range).
## On failure it is a parry back into play with chance save_parry, else it beats him.
@export_range(0.0, 1.0) var save_skill_base := 0.35
@export var save_skill_per_stat := 0.004
@export_range(0.0, 1.0) var dive_difficulty := 0.9
@export_range(0.0, 1.0) var save_parry := 0.5
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
## where a parry goes: an attacker within parry_danger m of the rebound spot (parry_spot m in front of him) = he pushes it wide round the post for a corner;
## nobody close = he steers it back out to the flank, away from the attackers (parry_out m/s out, parry_side m/s wide). Low HAN adds parry_scatter m/s of randomness.
@export var parry_danger := 8.0
@export var parry_spot := 5.0
@export var parry_out := 7.0
@export var parry_side := 5.0
@export var parry_scatter := 4.0
@export_subgroup("Save clips (he picks one at random)")
@export var clips_catch := PackedStringArray(["gk08_big_hands", "gk03_smother"])
## when the save is going to be a CATCH (decided as he commits) these play instead: diving catches for low / mid / far balls, body catches for shots at him
@export var clips_catch_dive := PackedStringArray(["gk29_diving_catch"])
@export var clips_catch_body := PackedStringArray(["gk30_chest_catch", "gk08_big_hands"])
## his body stops this far (m) short of the ball sideways so his hand meets it (a parry off the glove, not the chest); for a catch it is closer (the ball comes into both hands in front of him)
@export var hand_offset := 1.0
@export var catch_hand_offset := 0.4
## the glove: a save only happens with the ball within glove_reach (+ glove_reach_per_ref x REF) of his hand sideways and glove_depth along the pitch
@export var glove_reach := 0.35
@export var glove_reach_per_ref := 0.003
@export var glove_depth := 0.7
## standing saves (catch / claim / palm): how far the hands reach sideways from his body
@export var stand_arm := 0.55
## with the ball, the keeper carries it in his hands: this far in front of him (m) at this height (m)
@export var keeper_hold_ahead := 0.25
@export var keeper_hold_height := 1.0
## metres per sprite-rig unit (the clips' own ball track, root motion): a 1.8 m player is about 46 rig units
@export var rig_unit_m := 0.039
@export var clips_claim := PackedStringArray(["gk05_claim_cross"])
@export var clips_palm := PackedStringArray(["gk10_high_palm", "gk04_punch_clear"])
@export var clips_low := PackedStringArray(["gk09_low_dive", "gk27_bottom_hand_save", "gk20_cat_reflexes"])
@export var clips_mid := PackedStringArray(["gk02_reach_dive", "gk28_strong_wrist_parry", "gk12_starfish"])
@export var clips_far := PackedStringArray(["gk24_fingertip_save", "gk26_top_hand_stretch", "gk23_far_post_reach"])

@export_group("Goalkeeper and control")
## a keeper catches a shot slower than base + HAN x per_han (m/s), otherwise he parries
@export var save_speed_base := 8.0
@export var save_speed_per_han := 0.2
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

@export_group("Aerial duels")
## a ball in the air with this kick action (and an apex at least `aerial_min_apex` m) starts a contest: the nearest of each team goes to where it comes down to head height
@export var aerial_actions := PackedStringArray(["lob"])
@export var aerial_min_apex := 3.5
## the ball counts as met at this height (m); the landing marker shows where it first touches the grass
@export var head_height := 2.2
## only players who can get there within this many seconds more than the ball takes, and within this distance (m), go for it
@export var aerial_slack := 1.0
@export var aerial_range := 24.0
## standing next to the spot: closer than this he just waits (m)
@export var aerial_wait_dist := 0.6
## the contest is played when the ball is this many seconds from head height; the clip is stretched so its strike frame lands when the ball arrives
@export var aerial_trigger := 0.6
@export var aerial_clip_min := 0.5
@export var aerial_clip_max := 1.4
## a duel needs both within this distance (m) of the spot; otherwise the near one just waits and takes it
@export var duel_reach := 3.2
## the ball must be this close (m, along the ground) and between these heights at the strike frame, else he misses it
@export var header_reach := 2.4
@export var header_min_h := 0.5
@export var header_max_h := 3.6
## duel score = heading (PHY and DEF for defensive roles, SHO for the rest) + this share of PHY + noise (+/-) + bonus of the approach
@export_range(0.0, 1.0) var jump_share := 0.4
@export var duel_noise := 12.0
@export var receiver_bonus := 4.0
## push (shoulder shove, then chest it down): needs PHY at least this and this much more than the opponent; chance when allowed; bonus to his score; the opponent stumbles / falls
@export var push_phy := 74
@export var push_margin := 8
@export_range(0.0, 1.0) var push_chance := 0.6
@export var push_bonus := 18.0
@export_range(0.0, 1.0) var push_fall_chance := 0.35
## shoulder leap (hand on his shoulder, vault, header): "intelligence" = average of PAS and DRI, at least this; opponent this close (m); chance; bonus
@export var smart_min := 70
@export var leap_range := 2.4
@export_range(0.0, 1.0) var leap_chance := 0.7
@export var leap_bonus := 14.0
## what he does with a won header: defensive roles clear; others shoot inside this distance (m) from goal, else head it to the best team mate (ball speeds in m/s)
@export var defensive_roles := PackedStringArray(["CB", "LB", "RB", "CDM"])
@export var head_shoot_range := 19.0
@export var head_clear_speed := 17.0
@export var head_pass_speed := 12.0
@export var head_shot_speed := 21.0
@export var head_clear_length := 34.0
@export var head_noise := 6.0
## clips
@export var clip_wait_air := "ct01_wait_air"
@export var clip_push := "ct02_push_chest"
@export var clip_leap := "ct03_shoulder_leap"
@export var clip_header_clear := "df16_header_clear"
@export var clip_header_pass := "sh11_glancing_header"
@export var clip_header_shot := "sh12_power_header"
@export var clip_challenge := "base_jump"
## chest control: the ball keeps this share of its sideways speed, pops up this much (m/s) and drops this far ahead of him (m/s of push); the loser cannot touch it for chest_shield s
@export var chest_keep := 0.15
@export var chest_pop := 1.6
@export var chest_drop_ahead := 1.2
@export var chest_shield := 0.8
## while the duel clip plays both slide under the ball at up to this speed (m/s)
@export var aerial_steer_speed := 5.0

@export_group("Ball trail")
## a fading line behind a fast ball so curl and skip can be seen; spin kicks (finesse, trivela, benders, low drive) show it from a lower speed
@export var trail_enabled := true
@export var trail_min_speed := 20.0
@export var trail_min_speed_spin := 12.0
@export var trail_seconds := 0.45
@export var trail_width := 2.0
@export var trail_color := Color(1.0, 1.0, 1.0, 0.55)

@export_group("Keeper reading shots")
## how much of the ball's real bend / dip the keeper reads when he commits (0 = he dives at the straight line, 1 = he reads it perfectly): read_base + (REF - 60) x read_per_ref, clamped
@export_range(0.0, 1.0) var read_base := 0.45
@export var read_per_ref := 0.015
## each kick style's save_difficulty (data/kick_styles.csv) cuts the stop chance; good keepers cancel part of it: counter = (average REF HAN - 60) / 40 x keeper_counter, clamped 0..1
@export_range(0.0, 1.0) var keeper_counter := 0.8

@export_group("Keeper scan")
## how often (s) each keeper re-reads the ball (KeeperScan)
@export var scan_every := 0.1
## the ball ray: only for balls faster than this (m/s) heading his way, traced this many seconds ahead; a crossing within the goal plus this margin (m) counts
@export var scan_min_speed := 6.0
@export var scan_horizon := 1.6
@export var scan_post_margin := 0.8
## when the ray says it is coming, he steps across this share of the way towards it before it arrives (only if it arrives within pre_step_time s)
@export_range(0.0, 1.0) var pre_step_k := 0.35
@export var pre_step_time := 1.0
## perimeter rays: with an opponent on the ball within set_range m of goal he stands on the bisector of the shooter's angle (bisect_weight of the way) and gets set
## when the carrier faces goal (dot of his facing and the way to goal over set_facing)
@export var set_range := 30.0
@export_range(0.0, 1.0) var bisect_weight := 0.8
@export_range(-1.0, 1.0) var set_facing := 0.3
## draw the rays (yellow: ball to the posts, cyan: where the bisector meets his line, red: the ball's traced flight and where it crosses him)
@export var scan_debug := false

@export_group("Offside")
## the offside law (MatchOffside): judged when a team mate plays the ball; a player in an offside position who then touches it gives an indirect free kick
@export var offside_on := true
## level counts as onside; a player has to be this much (m) beyond the second-last opponent and the ball to be offside
@export var offside_tolerance := 0.15
## restarts the law does not apply to (law 11: throw-in, goal kick, corner)
@export var offside_free_restarts := PackedStringArray(["throw_in", "goal_kick", "corner"])
## a player who knows he is offside leaves the ball: chance = (PAS+DRI average - aware_min) / aware_span, clamped to aware_floor..aware_cap
@export var offside_aware_min := 30.0
@export var offside_aware_span := 60.0
@export_range(0.0, 1.0) var offside_aware_floor := 0.2
@export_range(0.0, 1.0) var offside_aware_cap := 0.95

@export_group("Restarts")
## after the ball goes out (or a free kick is given) play stops for this long (real s) while everybody takes up position; the clock runs on
@export var restart_wait_throw_in := 1.4
@export var restart_wait_goal_kick := 2.2
@export var restart_wait_corner := 2.6
@export var restart_wait_free_kick := 2.4
## opponents keep this far (m) from the ball until it is played (9.15 m by law; 2 m at a throw-in)
@export var restart_distance := 9.15
@export var restart_distance_throw := 2.0
## the restart waits (on top of the times above) until everybody is within restart_ready_dist (m) of his set-piece spot, at most restart_max_wait real s in all
@export var restart_ready_dist := 2.5
@export var restart_max_wait := 6.0

@export_group("Blocks and keeper claims")
## a ball faster than this (m/s) that hits a body (not the intended receiver) flies off it: up to deflect_deg off its line, keeping deflect_keep of its speed
@export var deflect_speed := 11.0
@export var deflect_deg := 55.0
@export_range(0.0, 1.0) var deflect_keep := 0.5
@export var deflect_up := 2.0
## the keeper comes for a high ball coming down within claim_depth (m) of his goal line and claim_width (m) of the middle, if he gets there in time
## (claim_slack s to spare) and his HAN + POS average is at least claim_min
@export var claim_depth := 11.0
@export var claim_width := 10.0
@export var claim_slack := 0.25
@export var claim_min := 50
## against an attacker under it: he claims it with chance claim_base + (his HAN/POS average - the attacker's heading) x claim_k / 100
@export var claim_base := 0.6
@export var claim_k := 1.2
## he catches it (or punches it when it is faster than he can hold: MatchPossession's keeper rule)
@export var claim_reach := 2.0

@export_group("Referee")
## a missed challenge is a foul with this chance (x 1.3 - DEF / 100): standing tackle, slide; one from behind adds foul_behind
@export_range(0.0, 1.0) var foul_tackle := 0.22
@export_range(0.0, 1.0) var foul_slide := 0.45
@export_range(0.0, 1.0) var foul_behind := 0.25
## yellow card chance by foul: standing, slide, from behind (added), tactical pull-back
@export_range(0.0, 1.0) var card_tackle := 0.08
@export_range(0.0, 1.0) var card_slide := 0.25
@export_range(0.0, 1.0) var card_behind := 0.2
@export_range(0.0, 1.0) var card_tactical := 0.9
## advantage: the fouled side keeps the ball beyond this team-frame x (m from the centre, + = their half) with nobody within advantage_space (m)
@export var advantage_from := 0.0
@export var advantage_space := 3.0
@export var restart_wait_penalty := 2.8
## in his own box a defender risks a foul this much less (a careless challenge there is a penalty)
@export_range(0.0, 1.0) var foul_box_care := 0.3

@export_group("Shielding and game management")
## a carrier shielding the ball (AiHoldUp, AiCornerFlag) is tackled this much less often: shield_k_weak at PHY 50, shield_k_strong at PHY 90
@export_range(0.0, 1.0) var shield_k_weak := 0.7
@export_range(0.0, 1.0) var shield_k_strong := 0.3
## from this minute a side that is ahead takes its restarts this much slower
@export var waste_after_minute := 75.0
@export var waste_restart_k := 1.8

@export_group("AI layer clips")
## clips of the real-football AI layer (sprites/moves_ai.py; bake them and Export to game). Until baked the moment just plays without its clip.
@export var clip_scan := "sc01_shoulder_check"
## a scan glance plays the clip only when he is this slow (m/s); the clip lasts scan_clip_time s
@export var scan_clip_speed := 1.5
@export var scan_clip_time := 0.45
@export var clip_throw_in := "ti01_throw_in"
@export var clip_long_throw := "ti02_long_throw"
## a throw longer than this (m) uses the long throw
@export var long_throw_from := 20.0
## clips whose own ball track holds the real ball (the ball stays in the thrower's hands)
@export var clips_ball_tracked := PackedStringArray(["ti01_throw_in", "ti02_long_throw"])
@export var clip_block := "bl01_block"
@export var block_clip_time := 0.8
@export var clip_punch := "gk36_punch"
@export var clip_wall := "wl01_wall_stand"
@export var clip_wall_jump := "wl02_wall_jump"
@export var wall_jump_time := 0.9
@export var clip_shield := "sh01_shield"
@export var clip_jockey := "jk01_jockey"
## the jockey / shield clips play while he moves slower than this (m/s)
@export var stance_clip_speed := 3.5
@export var clip_shirt_pull := "fl01_shirt_pull"
@export var shirt_pull_time := 0.9
@export var clip_penalty_runup := "pk01_penalty_runup"
@export var penalty_runup_time := 1.2
## the taker starts this far behind the ball and runs in at this speed (m/s)
@export var penalty_runup_dist := 2.6
@export var penalty_runup_speed := 2.4
@export var clip_keeper_penalty := "gk37_penalty_line"
@export var clip_offside_appeal := "ap01_offside_appeal"
## how many defenders appeal when offside is given
@export var appeal_count := 2
