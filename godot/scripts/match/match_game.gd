class_name MatchGame
extends Node
## The match, kept thin: it owns the teams, the ball and the clock and calls the modules each physics frame. The work is in
##   MatchSettings (every number, edit in the inspector)       MatchPossession (ball carrying, pick-up, tackles, kicks)
##   AiBrain + scripts/ai/roles (what every player does)       MatchMotion (running, animation)       MatchRules (kick-off, goals, throw-ins, corners)
##   MatchOrders (the human's orders)  MatchCards (the hand)   MatchControls (mouse / pad input)    MatchHud (the strip under the pitch)
## Players are plain 2D sprites projected by the Stadium; all the playing is in metres (x along the pitch, z across; home attacks towards +x, the right of the screen).

signal goal_scored(team: Team, scorer: Footballer)
signal full_time(home_score: int, away_score: int)

const HALF_L := 52.5
const HALF_W := 34.0
const GOAL_HALF := 3.66
const BAR := 2.44
const GAME_SECONDS := 5400.0
enum Phase { KICKOFF, PLAY, GOAL, FULLTIME }

## every tweakable number; edit it here in the inspector (scenes/match/match_settings.tres)
@export var settings: MatchSettings

@onready var stadium: Stadium = $View/Viewport/Stadium
@onready var hud: MatchHud = $Hud
@onready var controls: MatchControls = $Controls

var rng := RandomNumberGenerator.new()
var home: Team
var away: Team
var teams: Array[Team] = []
var all: Array[Footballer] = []
var ball: Ball
var carrier: Footballer             ## who has the ball (null = loose or in the air)
var last_touch: Footballer
var pass_target: Footballer         ## who the last pass was meant for
var selected: Footballer            ## the player the human is giving orders to (set by MatchControls)
var phase := Phase.KICKOFF
var phase_t := 0.0
var clock := 0.0                    ## game seconds, 0 to 5400

var poss: MatchPossession
var motion: MatchMotion
var rules: MatchRules
var orders: MatchOrders
var cards: MatchCards
var brain: AiBrain
var _next_kick: Team
var _slow := false

func _ready() -> void:
	rng.randomize()
	if settings == null: settings = MatchSettings.new()
	MatchSettings.current = settings
	if not Data.ok:
		hud.message("No exported data. Open the manager tool and press Export to game.", 999.0)
		return
	stadium.stadium_id = settings.stadium_id
	var used := {}
	home = Team.new(); home.label = "HOME"; home.dir = 1.0; home.human = true; home.kit = settings.home_kit; home.color = MatchSettings.kit_color(settings.home_kit)
	away = Team.new(); away.label = "AWAY"; away.dir = -1.0; away.kit = settings.away_kit; away.color = MatchSettings.kit_color(settings.away_kit)
	home.build(MatchSettings.formation_id(settings.home_formation), used, rng)
	away.build(MatchSettings.formation_id(settings.away_formation), used, rng)
	teams = [home, away]
	for t in teams:
		for f in t.players:
			f.node = Player.create()
			stadium.add_actor(f.node, Vector2(50, 50))
			f.node.setup(f.row, settings.keeper_kit if f.is_keeper() else t.kit)
			all.append(f)
	ball = Ball.create(settings.ball_id)
	stadium.add_ball(ball)
	ball.preview_speed = 1.0
	poss = MatchPossession.new(self)
	motion = MatchMotion.new(self)
	rules = MatchRules.new(self)
	orders = MatchOrders.new(self)
	cards = MatchCards.new(self)
	brain = AiBrain.new(self)
	cards.deal()
	controls.setup(self, hud)
	hud.card_pressed.connect(cards.play)
	hud.set_hand(cards.hand)
	_start(home)

func _start(kicking: Team) -> void:
	_slow = false
	rules.kickoff(kicking)
	phase = Phase.KICKOFF
	phase_t = 1.8
	hud.message("KICK OFF", 1.6)

func goal(scorer: Team) -> void:
	scorer.score += 1
	phase = Phase.GOAL
	phase_t = 3.6
	_slow = false
	_next_kick = away if scorer == home else home
	hud.message("GOAL!  %s" % (last_touch.display_name() if last_touch != null else ""), 3.4)
	goal_scored.emit(scorer, last_touch)

## slow motion while the human lines up a shot (eased in and out in _process)
func set_slowmo(on: bool) -> void:
	_slow = on

func _process(dt: float) -> void:
	var real_dt := dt / maxf(Engine.time_scale, 0.05)
	var target := settings.aim_slowmo if _slow and phase == Phase.PLAY else 1.0
	Engine.time_scale = move_toward(Engine.time_scale, target, 5.0 * real_dt)

func _exit_tree() -> void:
	Engine.time_scale = 1.0

func _physics_process(dt: float) -> void:
	if not Data.ok or ball == null: return
	if phase == Phase.PLAY:
		clock += dt * GAME_SECONDS / (settings.match_minutes * 60.0)
		if clock >= GAME_SECONDS:
			phase = Phase.FULLTIME
			hud.message("FULL TIME  %d - %d     R = play again" % [home.score, away.score], 999.0)
			full_time.emit(home.score, away.score)
		else:
			brain.update(dt)
	elif phase == Phase.KICKOFF or phase == Phase.GOAL:
		phase_t -= dt
		if phase_t <= 0.0:
			if phase == Phase.KICKOFF: phase = Phase.PLAY
			else: _start(_next_kick)
	elif Input.is_action_just_pressed("m_restart"):
		get_tree().reload_current_scene()
	motion.update(dt)
	poss.update(dt)
	if phase == Phase.PLAY: rules.check()
	cards.tick(dt)
	var bp := ball.phys.pos
	stadium.focus = stadium.pitch_pos(Vector3(bp.x, 0.0, bp.z))
	hud.set_score(home.score, away.score, int(clock / 60.0))
	hud.set_controlled(selected.display_name() if selected != null else "")
	hud.set_cooldowns(cards.cooldown)
