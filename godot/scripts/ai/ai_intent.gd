class_name AiIntent
extends RefCounted
## What a role's AI wants one player to do this frame. The AiBrain turns it into movement and kicks.

## where to go (Vector2.INF = stay put)
var move_to := Vector2.INF
## fraction of his top speed (the settings' jog_factor / sprint_factor / carry_factor are the usual values)
var speed := 0.7
## "" (just move), "pass", "through", "lob", "shoot", "takeon" (target = the defender he beats), "tackle" / "slide" (target = the carrier)
var action := ""
## team mate for a pass / through / lob
var target: Footballer
## spot for a shot, or for a pass with no team mate
var aim := Vector2.INF
## a shot's kick style (data/kick_styles.csv id, "" = the shot's default) and animation clip ("" = picked by distance); set by AiFinish
var style := ""
var clip := ""
## ball speed for a shot (m/s), 0 = the shot's own
var speed_override := 0.0
## shown nowhere yet: handy to print while tuning a role
var note := ""
