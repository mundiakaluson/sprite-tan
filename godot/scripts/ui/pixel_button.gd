@tool
class_name PixelButton
extends Control
## A button in the card language (frame art from assets/ui/button_*.png, text in the pixel font). Same API as Button where it matters:
## `text`, `disabled`, `toggle_mode`, `button_pressed`, signals `pressed` and `toggled(on)`, `set_pressed_no_signal()`. `accent` tints the frame
## (a toggled-on button lights up in it). The art needs Export to game > HUD art.

signal pressed
signal toggled(on: bool)

@export var text := "":
	set(v):
		text = v
		queue_redraw()
@export var accent := PixelUi.STEEL:
	set(v):
		accent = v
		queue_redraw()
@export_range(1, 3) var text_scale := 1:
	set(v):
		text_scale = v
		queue_redraw()
@export var disabled := false:
	set(v):
		disabled = v
		queue_redraw()
@export var toggle_mode := false
@export var button_pressed := false:
	set(v):
		button_pressed = v
		queue_redraw()

var _hover := false
var _down := false

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP
	focus_mode = Control.FOCUS_NONE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	custom_minimum_size = Vector2(64, 18)

func set_pressed_no_signal(v: bool) -> void:
	button_pressed = v

func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_ENTER:
		_hover = true
		queue_redraw()
	elif what == NOTIFICATION_MOUSE_EXIT:
		_hover = false
		_down = false
		queue_redraw()

func _gui_input(ev: InputEvent) -> void:
	var mb := ev as InputEventMouseButton
	if mb == null or mb.button_index != MOUSE_BUTTON_LEFT or disabled: return
	if mb.pressed:
		_down = true
		queue_redraw()
		accept_event()
	elif _down:
		_down = false
		queue_redraw()
		accept_event()
		if _hover:
			if toggle_mode:
				button_pressed = not button_pressed
				toggled.emit(button_pressed)
			pressed.emit()

func _draw() -> void:
	var state := "normal"
	if disabled: state = "disabled"
	elif _down: state = "pressed"
	elif button_pressed: state = "active"
	elif _hover: state = "hover"
	PixelUi.nine(self, Rect2(Vector2.ZERO, size), PixelUi.tex("button_" + state), accent)
	var col := Color.WHITE
	if disabled: col = Color(0.35, 0.37, 0.45)
	var w := PixelText.width(text, text_scale)
	var pos := Vector2(floorf((size.x - w) / 2.0), floorf((size.y - 6.0 * text_scale) / 2.0) + (1 if _down else 0))
	if not disabled: PixelText.draw(self, pos + Vector2(text_scale, text_scale), text, Color(0, 0, 0, 0.7), text_scale)
	PixelText.draw(self, pos, text, col, text_scale)
