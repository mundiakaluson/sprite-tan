class_name AiIntent
extends RefCounted
## What a role's AI wants one player to do this frame. The AiBrain turns it into movement and kicks.

## where to go (Vector2.INF = stay put)
var move_to := Vector2.INF
## fraction of his top speed (the settings' jog_factor / sprint_factor / carry_factor are the usual values)
var speed := 0.7
## "" (just move), "pass", "through", "lob", "shoot"
var action := ""
## team mate for a pass / through / lob
var target: Footballer
## spot for a shot, or for a pass with no team mate
var aim := Vector2.INF
## shown nowhere yet: handy to print while tuning a role
var note := ""
