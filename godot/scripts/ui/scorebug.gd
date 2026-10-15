@tool
class_name Scorebug
extends Control
## The score bug at the top left of the pitch view (design A): home box, away box, clock box, a RANKED / UNRANKED tag on top and, when ranked, the stakes line.
## Drawn in the card pixel language (ui/panel.png tinted). Ranked = gold frames with corner studs, unranked = steel. The HUD feeds it through the setters / `ranked`.
## Reds are shown as small red cards under the team name; `added` shows the orange +N next to the clock.

const GOLD := Color(1.0, 0.78, 0.27)
const DIM := Color(0.55, 0.57, 0.69)
const ORANGE := Color(1.0, 0.59, 0.24)
const RED := Color(0.93, 0.24, 0.2)
const WHITE := Color(1, 1, 1)
const STUD := Color(1.0, 0.98, 0.78)

@export var ranked := false: set = _set_ranked
@export var home_name := "HOME": set = _set_home_name
@export var away_name := "AWAY": set = _set_away_name
@export var home_color := Color(0.84, 0.2, 0.25)
@export var away_color := Color(0.93, 0.93, 0.96)
@export var home_score := 0
@export var away_score := 0
@export var home_reds := 0
@export var away_reds := 0
@export var clock_text := "0:00"
@export var period := "1ST HALF"
## added time in minutes, shown as +N next to the clock (0 = hidden)
@export var added := 0
@export var division := "DIV 3"
@export var win_points := 24
@export var loss_points := 18
## colour of the frames when unranked
@export var steel := PixelUi.STEEL

const TEAM_W := 92
const CLOCK_W := 74
const BOX_H := 24
const BOX_Y := 13

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	custom_minimum_size = Vector2(TEAM_W * 2 + CLOCK_W - 2, 52)

func _set_ranked(v: bool) -> void:
	ranked = v
	queue_redraw()
func _set_home_name(v: String) -> void:
	home_name = v
	queue_redraw()
func _set_away_name(v: String) -> void:
	away_name = v
	queue_redraw()

## one call for everything that changes during play
func update_state(h: int, a: int, h_reds: int, a_reds: int, clock: String, per: String, add_min: int) -> void:
	if h == home_score and a == away_score and h_reds == home_reds and a_reds == away_reds and clock == clock_text and per == period and add_min == added: return
	home_score = h
	away_score = a
	home_reds = h_reds
	away_reds = a_reds
	clock_text = clock
	period = per
	added = add_min
	queue_redraw()

func _acc() -> Color:
	return GOLD if ranked else steel

func _box(x: int, w: int) -> void:
	PixelUi.nine(self, Rect2(x, BOX_Y, w, BOX_H), PixelUi.tex("panel"), _acc())
	if ranked:
		for cx in [x + 2, x + w - 3]:
			draw_rect(Rect2(cx - 1, BOX_Y - 1, 3, 3), GOLD)
			draw_rect(Rect2(cx, BOX_Y, 1, 1), STUD)

func _text(x: float, y: float, s: String, col: Color, k := 1) -> void:
	PixelText.draw(self, Vector2(x + k, y + k), s, Color(0, 0, 0, 0.8), k)
	PixelText.draw(self, Vector2(x, y), s, col, k)

func _reds(x: int, y: int, n: int) -> void:
	for i in n:
		draw_rect(Rect2(x + i * 5, y, 4, 6), RED)
		draw_rect(Rect2(x + i * 5, y, 1, 6), Color(0.47, 0.08, 0.08))
		draw_rect(Rect2(x + i * 5 + 1, y + 1, 1, 1), Color(1, 0.67, 0.63))

func _chip(x: int, col: Color) -> void:
	draw_rect(Rect2(x, BOX_Y + 6, 4, 12), col)
	draw_rect(Rect2(x, BOX_Y + 6, 1, 12), col.lightened(0.2))

func _draw() -> void:
	# tag
	var tag := "RANKED" if ranked else "UNRANKED"
	var tw := PixelText.width(tag, 1) + 10
	PixelUi.nine(self, Rect2(0, 0, tw, 11), PixelUi.tex("panel"), GOLD if ranked else DIM)
	_text(5, 3, tag, GOLD if ranked else DIM)
	if ranked: _text(tw + 4, 3, division, GOLD)
	# home box: chip, name, reds ... score
	_box(0, TEAM_W)
	_chip(5, home_color)
	_text(13, BOX_Y + 5, home_name, WHITE)
	_reds(13, BOX_Y + 14, home_reds)
	var hs := str(home_score)
	_text(TEAM_W - 7 - PixelText.width(hs, 2), BOX_Y + 6, hs, WHITE, 2)
	# away box: score ... name, reds, chip
	var ax := TEAM_W - 1
	_box(ax, TEAM_W)
	_chip(ax + TEAM_W - 9, away_color)
	_text(ax + 7, BOX_Y + 6, str(away_score), WHITE, 2)
	var nx := ax + TEAM_W - 13 - PixelText.width(away_name, 1)
	_text(nx, BOX_Y + 5, away_name, WHITE)
	_reds(nx, BOX_Y + 14, away_reds)
	# clock
	var cx := ax + TEAM_W - 1
	_box(cx, CLOCK_W)
	var add_s := "+%d" % added if added > 0 else ""
	var cw := PixelText.width(clock_text, 2)
	var total := cw + (PixelText.width(add_s, 1) + 3 if added > 0 else 0)
	var x0 := cx + (CLOCK_W - total) / 2
	_text(x0, BOX_Y + 4, clock_text, WHITE, 2)
	if added > 0: _text(x0 + cw + 3, BOX_Y + 7, add_s, ORANGE)
	_text(cx + (CLOCK_W - PixelText.width(period, 1)) / 2, BOX_Y + 17, period, DIM)
	if ranked:
		_text(2, BOX_Y + BOX_H + 4, "WIN +%d   LOSS -%d" % [win_points, loss_points], Color(1, 0.86, 0.51))
